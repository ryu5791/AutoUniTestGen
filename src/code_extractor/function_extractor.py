"""
FunctionExtractorモジュール

C言語ソースコードから関数本体を抽出する
"""

import re
from typing import Optional, List, Tuple
import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class FunctionExtractor:
    """関数本体抽出器"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def extract_function_body(self, source_code: str, function_name: str) -> Optional[str]:
        """
        関数本体を抽出
        
        Args:
            source_code: 元のソースコード
            function_name: 対象関数名
            
        Returns:
            関数の定義（static含む）全体、見つからない場合はNone
        """
        self.logger.info(f"関数 '{function_name}' の本体を抽出中...")
        
        # パターン1: static void function_name(...)
        # パターン2: void function_name(...)
        # パターン3: 戻り値型 function_name(...)
        # パターン4: static 戻り値型 function_name(...)
        
        # 関数定義のパターンを構築
        # 修飾子(static, inline等)、戻り値型、関数名、引数リスト
        pattern = rf'''
            ((?:static\s+)?                    # オプショナルなstatic
             (?:inline\s+)?                    # オプショナルなinline
             (?:extern\s+)?                    # オプショナルなextern
             [\w\s\*]+?)                       # 戻り値型（スペース、アスタリスク含む）
            \s+                                # スペース
            ({re.escape(function_name)})       # 関数名
            \s*                                # オプショナルなスペース
            \(                                 # 開き括弧
            [^)]*                              # 引数リスト
            \)                                 # 閉じ括弧
            \s*                                # オプショナルなスペース
            (?:__attribute__\s*\([^)]*\))?     # オプショナルな__attribute__
            \s*                                # オプショナルなスペース
            \{{                                # 関数本体の開始
        '''
        
        # VERBOSE, MULTILINE, DOTALLモードで検索
        matches = list(re.finditer(pattern, source_code, re.VERBOSE | re.MULTILINE))
        
        if not matches:
            self.logger.warning(f"関数 '{function_name}' が見つかりませんでした")
            return None
        
        if len(matches) > 1:
            self.logger.warning(f"関数 '{function_name}' が複数見つかりました（{len(matches)}個）。最初のものを使用します。")
        
        # 最初のマッチを使用
        match = matches[0]
        start_pos = match.start()
        
        # 関数本体の終わりを見つける（中括弧のバランスをチェック）
        end_pos = self._find_function_end(source_code, match.end())
        
        if end_pos is None:
            self.logger.error(f"関数 '{function_name}' の終了位置が見つかりませんでした")
            return None
        
        # 関数全体を抽出（閉じ括弧を含む）
        function_body = source_code[start_pos:end_pos]
        
        self.logger.info(f"関数 '{function_name}' を抽出しました（{len(function_body)}バイト）")
        return function_body
    
    def _find_function_end(self, source_code: str, start_pos: int) -> Optional[int]:
        """
        関数本体の終了位置を見つける
        
        中括弧のバランスをチェックして、対応する閉じ括弧の位置を返す
        
        Args:
            source_code: ソースコード
            start_pos: 検索開始位置（開き括弧の直後）
            
        Returns:
            閉じ括弧の直後の位置、見つからない場合はNone
        """
        brace_count = 1  # 既に1つ開き括弧を通過している
        pos = start_pos
        in_string = False
        in_char = False
        in_comment = False
        in_line_comment = False
        escape_next = False
        
        while pos < len(source_code):
            char = source_code[pos]
            
            # エスケープ文字の処理
            if escape_next:
                escape_next = False
                pos += 1
                continue
            
            if char == '\\':
                escape_next = True
                pos += 1
                continue
            
            # コメントの処理
            if not in_string and not in_char:
                # 行コメントの終了
                if in_line_comment:
                    if char == '\n':
                        in_line_comment = False
                    pos += 1
                    continue
                
                # ブロックコメントの終了
                if in_comment:
                    if char == '*' and pos + 1 < len(source_code) and source_code[pos + 1] == '/':
                        in_comment = False
                        pos += 2
                        continue
                    pos += 1
                    continue
                
                # コメントの開始
                if char == '/' and pos + 1 < len(source_code):
                    next_char = source_code[pos + 1]
                    if next_char == '/':
                        in_line_comment = True
                        pos += 2
                        continue
                    elif next_char == '*':
                        in_comment = True
                        pos += 2
                        continue
            
            # 文字列リテラルの処理
            if char == '"' and not in_char and not in_comment and not in_line_comment:
                in_string = not in_string
                pos += 1
                continue
            
            # 文字リテラルの処理
            if char == "'" and not in_string and not in_comment and not in_line_comment:
                in_char = not in_char
                pos += 1
                continue
            
            # 中括弧のカウント（文字列・コメント外のみ）
            if not in_string and not in_char and not in_comment and not in_line_comment:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # 対応する閉じ括弧を見つけた
                        return pos + 1
            
            pos += 1
        
        # 対応する閉じ括弧が見つからなかった
        return None
    
    def extract_function_signature(self, source_code: str, function_name: str) -> Optional[str]:
        """
        関数シグネチャ（プロトタイプ宣言）を抽出
        
        Args:
            source_code: 元のソースコード
            function_name: 対象関数名
            
        Returns:
            関数シグネチャ（例: "static void func(int a, int b)"）
        """
        # 関数本体を抽出
        function_body = self.extract_function_body(source_code, function_name)
        if not function_body:
            return None
        
        # 最初の開き中括弧までを抽出
        match = re.search(r'^(.*?)\s*\{', function_body, re.DOTALL)
        if match:
            signature = match.group(1).strip()
            return signature
        
        return None
    
    def list_all_functions(self, source_code: str) -> List[Tuple[str, str]]:
        """
        ソースコード内の全ての関数をリストアップ
        
        Args:
            source_code: 元のソースコード
            
        Returns:
            (関数名, シグネチャ) のリスト
        """
        # 関数定義パターン
        pattern = r'''
            ((?:static\s+)?                    # オプショナルなstatic
             (?:inline\s+)?                    # オプショナルなinline
             (?:extern\s+)?                    # オプショナルなextern
             [\w\s\*]+?)                       # 戻り値型
            \s+                                # スペース
            (\w+)                              # 関数名
            \s*                                # オプショナルなスペース
            \(                                 # 開き括弧
            [^)]*                              # 引数リスト
            \)                                 # 閉じ括弧
            \s*                                # オプショナルなスペース
            (?:__attribute__\s*\([^)]*\))?     # オプショナルな__attribute__
            \s*                                # オプショナルなスペース
            \{                                 # 関数本体の開始
        '''
        
        matches = re.finditer(pattern, source_code, re.VERBOSE | re.MULTILINE)
        
        functions = []
        for match in matches:
            full_sig = match.group(0)[:-1].strip()  # 最後の{を除く
            func_name = match.group(2).strip()
            functions.append((func_name, full_sig))
        
        self.logger.info(f"{len(functions)}個の関数が見つかりました")
        return functions
