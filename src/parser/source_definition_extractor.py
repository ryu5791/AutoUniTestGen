"""
SourceDefinitionExtractorモジュール

元のC言語ソースファイルから直接マクロ定義と型定義を抽出する
ASTパースが失敗した場合のフォールバック用
"""

import re
from typing import List, Dict, Tuple
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class SourceDefinitionExtractor:
    """ソースファイルから定義を直接抽出"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def extract_macro_definitions(self, source_code: str) -> Tuple[Dict[str, str], List[str]]:
        """
        マクロ定義を抽出
        
        Args:
            source_code: ソースコード
        
        Returns:
            Tuple[Dict[str, str], List[str]]: (マクロ辞書, マクロ定義文字列のリスト)
        """
        macros = {}
        macro_definitions = []
        
        lines = source_code.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # #defineで始まる行を検出
            if line.startswith('#define'):
                # 継続行を処理（バックスラッシュで終わる行）
                full_line = line
                while full_line.endswith('\\') and i + 1 < len(lines):
                    i += 1
                    full_line = full_line[:-1] + ' ' + lines[i].strip()
                
                macro_definitions.append(full_line)
                
                # マクロ名と値を抽出
                match = re.match(r'#define\s+(\w+)(?:\(.*?\))?\s+(.*)', full_line)
                if match:
                    name = match.group(1)
                    value = match.group(2).strip()
                    macros[name] = value
                else:
                    # 値なしのマクロ
                    match = re.match(r'#define\s+(\w+)', full_line)
                    if match:
                        name = match.group(1)
                        macros[name] = ''
            
            i += 1
        
        self.logger.info(f"マクロ定義を{len(macro_definitions)}個抽出しました")
        return macros, macro_definitions
    
    def extract_typedef_definitions(self, source_code: str) -> List[str]:
        """
        型定義を抽出
        
        Args:
            source_code: ソースコード
        
        Returns:
            List[str]: 型定義文字列のリスト
        """
        typedef_definitions = []
        
        lines = source_code.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # typedefで始まる行を検出
            if line.startswith('typedef'):
                # 複数行にわたる型定義を収集
                full_typedef = line
                brace_depth = line.count('{') - line.count('}')
                
                # セミコロンが見つかるまで、またはブレースが閉じるまで続ける
                while i + 1 < len(lines) and (';' not in full_typedef or brace_depth > 0):
                    i += 1
                    next_line = lines[i].strip()
                    full_typedef += '\n' + next_line
                    brace_depth += next_line.count('{') - next_line.count('}')
                    
                    # セミコロンが見つかり、ブレースが閉じていれば終了
                    if ';' in next_line and brace_depth == 0:
                        break
                
                typedef_definitions.append(full_typedef)
            
            i += 1
        
        self.logger.info(f"型定義を{len(typedef_definitions)}個抽出しました")
        return typedef_definitions
    
    def extract_all_definitions(self, source_code: str) -> Dict[str, any]:
        """
        すべての定義を抽出
        
        Args:
            source_code: ソースコード
        
        Returns:
            Dict: マクロと型定義を含む辞書
        """
        macros, macro_definitions = self.extract_macro_definitions(source_code)
        typedef_definitions = self.extract_typedef_definitions(source_code)
        
        return {
            'macros': macros,
            'macro_definitions': macro_definitions,
            'typedef_definitions': typedef_definitions
        }
