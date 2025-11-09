"""
MacroExtractorモジュール

C言語ソースコードからマクロ定義を抽出する
"""

import re
from typing import List, Set
import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class MacroExtractor:
    """マクロ定義抽出器"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def extract_macros(self, source_code: str, target_macros: List[str] = None) -> List[str]:
        """
        マクロ定義を抽出
        
        Args:
            source_code: 元のソースコード
            target_macros: 抽出対象のマクロ名リスト（None=全て）
            
        Returns:
            マクロ定義のリスト
        """
        self.logger.info("マクロ定義を抽出中...")
        
        macros = []
        
        # #define パターン
        # 複数行マクロ（バックスラッシュ継続）にも対応
        pattern = r'#define\s+\w+(?:\([^)]*\))?\s+.*?(?:\\\n.*?)*'
        
        matches = re.finditer(pattern, source_code, re.MULTILINE)
        for match in matches:
            macro_str = match.group(0)
            
            if target_macros is None:
                macros.append(macro_str)
            else:
                # マクロ名を抽出してチェック
                macro_name = self._extract_macro_name(macro_str)
                if macro_name in target_macros:
                    macros.append(macro_str)
        
        self.logger.info(f"{len(macros)}個のマクロ定義を抽出しました")
        return macros
    
    def _extract_macro_name(self, macro_str: str) -> str:
        """
        マクロ定義からマクロ名を抽出
        
        Args:
            macro_str: マクロ定義文字列
            
        Returns:
            マクロ名
        """
        # #define マクロ名 ... から マクロ名 を抽出
        match = re.search(r'#define\s+(\w+)', macro_str)
        if match:
            return match.group(1)
        return ""
    
    def extract_macros_used_in_code(self, code: str) -> Set[str]:
        """
        コード内で使用されているマクロ名を抽出
        
        Args:
            code: コード（関数本体など）
            
        Returns:
            使用されているマクロ名のセット
        """
        self.logger.info("コード内で使用されているマクロ名を抽出中...")
        
        macros = set()
        
        # マクロ参照パターン
        # UtD1、UtD2 のような大文字で始まる識別子
        pattern = r'\b(UtD\w+|[A-Z][A-Z0-9_]+)\b'
        
        matches = re.finditer(pattern, code)
        for match in matches:
            macro_name = match.group(1)
            # 型名と区別するため、全て大文字または UtD で始まるものをマクロとみなす
            if macro_name.isupper() or macro_name.startswith('UtD'):
                macros.add(macro_name)
        
        self.logger.info(f"{len(macros)}個のマクロ参照が見つかりました")
        return macros
