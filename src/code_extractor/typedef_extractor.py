"""
TypedefExtractorモジュール

C言語ソースコードから型定義を抽出する
"""

import re
from typing import List, Optional, Set
import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class TypedefExtractor:
    """型定義抽出器"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def extract_typedefs(self, source_code: str, target_types: List[str] = None) -> List[str]:
        """
        型定義を抽出
        
        Args:
            source_code: 元のソースコード
            target_types: 抽出対象の型名リスト（None=全て）
            
        Returns:
            型定義のリスト
        """
        self.logger.info("型定義を抽出中...")
        
        typedefs = []
        
        # typedefパターンを検索
        # typedef ... } 型名; の形式
        pattern = r'typedef\s+(?:struct|union|enum)?\s*\{[^}]*\}\s*\w+\s*;'
        
        # より複雑なtypedef（ネストした構造体など）に対応
        # 中括弧のバランスを考慮した抽出が必要
        
        matches = re.finditer(r'typedef\s+', source_code)
        
        for match in matches:
            start_pos = match.start()
            typedef_str = self._extract_typedef_from_position(source_code, start_pos)
            
            if typedef_str:
                # target_typesが指定されている場合はフィルタリング
                if target_types is None:
                    typedefs.append(typedef_str)
                else:
                    # typedef名を抽出してチェック
                    typedef_name = self._extract_typedef_name(typedef_str)
                    if typedef_name in target_types:
                        typedefs.append(typedef_str)
        
        self.logger.info(f"{len(typedefs)}個の型定義を抽出しました")
        return typedefs
    
    def _extract_typedef_from_position(self, source_code: str, start_pos: int) -> Optional[str]:
        """
        指定位置から1つのtypedef定義を抽出
        
        Args:
            source_code: ソースコード
            start_pos: typedefキーワードの開始位置
            
        Returns:
            typedef定義全体
        """
        pos = start_pos
        brace_count = 0
        in_typedef = True
        
        while pos < len(source_code) and in_typedef:
            char = source_code[pos]
            
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == ';' and brace_count == 0:
                # typedef の終わり
                return source_code[start_pos:pos + 1]
            
            pos += 1
        
        return None
    
    def _extract_typedef_name(self, typedef_str: str) -> Optional[str]:
        """
        typedef定義から型名を抽出
        
        Args:
            typedef_str: typedef定義文字列
            
        Returns:
            型名
        """
        # typedef ... } 型名; から型名を抽出
        match = re.search(r'\}\s*(\w+)\s*;', typedef_str)
        if match:
            return match.group(1)
        
        # typedef 既存型 新型名; の形式
        match = re.search(r'typedef\s+[\w\s\*]+\s+(\w+)\s*;', typedef_str)
        if match:
            return match.group(1)
        
        return None
    
    def extract_types_used_in_code(self, code: str) -> Set[str]:
        """
        コード内で使用されている型名を抽出
        
        Args:
            code: コード（関数本体など）
            
        Returns:
            使用されている型名のセット
        """
        self.logger.info("コード内で使用されている型名を抽出中...")
        
        types = set()
        
        # 変数宣言から型名を抽出
        # 型名 変数名; または 型名 変数名 = 値;
        # Utx68、uint8_t などの型名パターン
        pattern = r'\b([A-Z]\w+|u?int\d+_t|size_t|bool|char|short|int|long|float|double)\b'
        
        matches = re.finditer(pattern, code)
        for match in matches:
            type_name = match.group(1)
            types.add(type_name)
        
        self.logger.info(f"{len(types)}個の型名が見つかりました")
        return types
    
    def extract_struct_definitions(self, source_code: str) -> List[str]:
        """
        struct定義を抽出（typedefでない独立したstruct）
        
        Args:
            source_code: 元のソースコード
            
        Returns:
            struct定義のリスト
        """
        structs = []
        
        # struct 構造体名 { ... }; のパターン
        pattern = r'struct\s+\w+\s*\{[^}]*\}\s*;'
        
        matches = re.finditer(pattern, source_code)
        for match in matches:
            structs.append(match.group(0))
        
        self.logger.info(f"{len(structs)}個のstruct定義を抽出しました")
        return structs
