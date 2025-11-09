"""
VariableExtractorモジュール

C言語ソースコードからグローバル変数宣言を抽出する
"""

import re
from typing import List, Set
import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class VariableExtractor:
    """変数宣言抽出器"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def extract_global_variables(self, source_code: str) -> List[str]:
        """
        グローバル変数宣言を抽出
        
        Args:
            source_code: 元のソースコード
            
        Returns:
            グローバル変数宣言のリスト
        """
        self.logger.info("グローバル変数を抽出中...")
        
        variables = []
        
        # 外部変数宣言パターン: extern 型 変数名;
        extern_pattern = r'extern\s+[\w\s\*]+\s+\w+\s*(?:\[[^\]]*\])?\s*;'
        
        matches = re.finditer(extern_pattern, source_code)
        for match in matches:
            variables.append(match.group(0))
        
        self.logger.info(f"{len(variables)}個のグローバル変数を抽出しました")
        return variables
    
    def extract_variables_used_in_code(self, code: str) -> Set[str]:
        """
        コード内で使用されている変数名を抽出
        
        Args:
            code: コード（関数本体など）
            
        Returns:
            使用されている変数名のセット
        """
        self.logger.info("コード内で使用されている変数名を抽出中...")
        
        variables = set()
        
        # 変数参照パターン
        # Utx112.Utm10 のような形式から変数名を抽出
        pattern = r'\b([A-Z]\w+)\.'
        
        matches = re.finditer(pattern, code)
        for match in matches:
            var_name = match.group(1)
            variables.add(var_name)
        
        # 単純な変数参照も抽出
        pattern2 = r'\b([A-Z]\w+)\s*[=<>!]'
        matches2 = re.finditer(pattern2, code)
        for match in matches2:
            var_name = match.group(1)
            variables.add(var_name)
        
        self.logger.info(f"{len(variables)}個の変数参照が見つかりました")
        return variables
