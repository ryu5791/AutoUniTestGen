"""
CodeExtractorモジュール

各種抽出器を統合した高レベルインターフェース
"""

from dataclasses import dataclass
from typing import List
import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.code_extractor.function_extractor import FunctionExtractor
from src.code_extractor.typedef_extractor import TypedefExtractor
from src.code_extractor.variable_extractor import VariableExtractor
from src.code_extractor.macro_extractor import MacroExtractor


@dataclass
class ExtractedCode:
    """抽出されたコード情報"""
    function_body: str = ""  # 関数本体
    typedefs: List[str] = None  # 型定義
    macros: List[str] = None  # マクロ定義
    global_variables: List[str] = None  # グローバル変数宣言
    includes: List[str] = None  # 必要なインクルード
    
    def __post_init__(self):
        """デフォルト値の設定"""
        if self.typedefs is None:
            self.typedefs = []
        if self.macros is None:
            self.macros = []
        if self.global_variables is None:
            self.global_variables = []
        if self.includes is None:
            self.includes = []
    
    def to_code_section(self) -> str:
        """
        コードセクションとして整形して返す
        
        Returns:
            整形されたコードセクション
        """
        sections = []
        
        sections.append("// ===== テスト対象関数の依存コード =====")
        sections.append("")
        
        if self.macros:
            sections.append("// ===== マクロ定義 =====")
            sections.extend(self.macros)
            sections.append("")
        
        if self.typedefs:
            sections.append("// ===== 型定義 =====")
            sections.extend(self.typedefs)
            sections.append("")
        
        if self.global_variables:
            sections.append("// ===== グローバル変数 =====")
            sections.extend(self.global_variables)
            sections.append("")
        
        if self.function_body:
            sections.append("// ===== テスト対象関数 =====")
            sections.append(self.function_body)
            sections.append("")
        
        return '\n'.join(sections)
    
    def has_content(self) -> bool:
        """
        何らかのコンテンツが含まれているかチェック
        
        Returns:
            コンテンツがある場合True
        """
        return bool(self.function_body or self.typedefs or self.macros or 
                   self.global_variables or self.includes)


class CodeExtractor:
    """コード抽出統合クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.function_extractor = FunctionExtractor()
        self.typedef_extractor = TypedefExtractor()
        self.variable_extractor = VariableExtractor()
        self.macro_extractor = MacroExtractor()
    
    def extract_all_dependencies(self, source_code: str, function_name: str, 
                                include_dependencies: bool = True) -> ExtractedCode:
        """
        関数とその依存関係を全て抽出
        
        Args:
            source_code: 元のソースコード
            function_name: 対象関数名
            include_dependencies: 依存関係（型定義、マクロなど）を含めるか
            
        Returns:
            ExtractedCode オブジェクト
        """
        self.logger.info(f"関数 '{function_name}' とその依存関係を抽出中...")
        
        result = ExtractedCode()
        
        # 1. 関数本体を抽出
        function_body = self.function_extractor.extract_function_body(source_code, function_name)
        if function_body:
            result.function_body = function_body
            self.logger.info(f"✓ 関数本体を抽出しました（{len(function_body)}バイト）")
        else:
            self.logger.warning(f"✗ 関数 '{function_name}' が見つかりませんでした")
            return result
        
        if not include_dependencies:
            return result
        
        # 2. 関数内で使用されている型を抽出
        types_used = self.typedef_extractor.extract_types_used_in_code(function_body)
        if types_used:
            self.logger.info(f"関数内で {len(types_used)} 個の型が使用されています")
            # 型定義を抽出
            typedefs = self.typedef_extractor.extract_typedefs(source_code, list(types_used))
            result.typedefs = typedefs
            self.logger.info(f"✓ {len(typedefs)} 個の型定義を抽出しました")
        
        # 3. 関数内で使用されているマクロを抽出
        macros_used = self.macro_extractor.extract_macros_used_in_code(function_body)
        if macros_used:
            self.logger.info(f"関数内で {len(macros_used)} 個のマクロが使用されています")
            # マクロ定義を抽出
            macros = self.macro_extractor.extract_macros(source_code, list(macros_used))
            result.macros = macros
            self.logger.info(f"✓ {len(macros)} 個のマクロ定義を抽出しました")
        
        # 4. 関数内で使用されている変数を抽出
        variables_used = self.variable_extractor.extract_variables_used_in_code(function_body)
        if variables_used:
            self.logger.info(f"関数内で {len(variables_used)} 個の変数が使用されています")
            # グローバル変数宣言を抽出
            global_vars = self.variable_extractor.extract_global_variables(source_code)
            # 使用されている変数のみフィルタリング
            filtered_vars = [var for var in global_vars 
                           if any(var_name in var for var_name in variables_used)]
            result.global_variables = filtered_vars
            self.logger.info(f"✓ {len(filtered_vars)} 個のグローバル変数宣言を抽出しました")
        
        self.logger.info("依存関係の抽出が完了しました")
        return result
    
    def extract_function_only(self, source_code: str, function_name: str) -> ExtractedCode:
        """
        関数本体のみを抽出（依存関係は含めない）
        
        Args:
            source_code: 元のソースコード
            function_name: 対象関数名
            
        Returns:
            ExtractedCode オブジェクト（function_bodyのみ）
        """
        return self.extract_all_dependencies(source_code, function_name, include_dependencies=False)
