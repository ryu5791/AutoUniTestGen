"""
MockGeneratorモジュール

モック/スタブ関数を生成
"""

import sys
import os
from typing import List, Dict, Optional

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import ParsedData, MockFunction


class MockGenerator:
    """モックジェネレータ"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.mock_functions: List[MockFunction] = []
    
    def generate_mocks(self, parsed_data: ParsedData) -> str:
        """
        モック/スタブコードを生成
        
        Args:
            parsed_data: 解析済みデータ
        
        Returns:
            モックコード
        """
        self.logger.info("モック/スタブコードの生成を開始")
        
        # 外部関数からモック関数リストを作成
        self.mock_functions = []
        for func_name in parsed_data.external_functions:
            mock_func = self._create_mock_function(func_name)
            self.mock_functions.append(mock_func)
        
        # コードを生成
        code_parts = []
        
        # 1. モック用グローバル変数
        code_parts.append(self.generate_mock_variables())
        
        # 2. モック関数の実装
        code_parts.append(self.generate_mock_functions())
        
        # 3. リセット関数
        code_parts.append(self.generate_reset_function())
        
        self.logger.info(f"モック/スタブコードの生成が完了: {len(self.mock_functions)}個")
        
        return '\n\n'.join(code_parts)
    
    def _create_mock_function(self, func_name: str) -> MockFunction:
        """
        モック関数情報を作成
        
        Args:
            func_name: 関数名
        
        Returns:
            MockFunction
        """
        # 戻り値の型を推定（簡易実装）
        return_type = self._guess_return_type(func_name)
        
        return MockFunction(
            name=func_name,
            return_type=return_type,
            parameters=[],
            return_variable=f"mock_{func_name}_return_value",
            call_count_variable=f"mock_{func_name}_call_count"
        )
    
    def _guess_return_type(self, func_name: str) -> str:
        """
        関数名から戻り値の型を推定
        
        Args:
            func_name: 関数名
        
        Returns:
            型名
        """
        # 簡易的な型推定
        # 実際にはパースしたASTから取得すべき
        if func_name.startswith('f'):
            return 'uint16_t'
        elif func_name.startswith('mx'):
            return 'mx26'  # enum型を仮定
        else:
            return 'int'
    
    def generate_mock_variables(self) -> str:
        """
        モック用グローバル変数を生成
        
        Returns:
            変数定義のコード
        """
        lines = ["// ===== モック・スタブ用グローバル変数 ====="]
        
        for mock_func in self.mock_functions:
            # 戻り値変数（初期化はsetUp()で実施）
            lines.append(f"static {mock_func.return_type} {mock_func.return_variable};")
            
            # 呼び出し回数カウンタ（初期化はsetUp()で実施）
            lines.append(f"static int {mock_func.call_count_variable};")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_mock_functions(self) -> str:
        """
        モック関数の実装を生成
        
        Returns:
            モック関数のコード
        """
        lines = ["// ===== モック・スタブ実装 ====="]
        lines.append("")
        
        for mock_func in self.mock_functions:
            # 関数コメント
            lines.append(f"/**")
            lines.append(f" * {mock_func.name}のモック")
            lines.append(f" */")
            
            # 関数定義
            lines.append(f"static {mock_func.return_type} mock_{mock_func.name}(void) {{")
            lines.append(f"    {mock_func.call_count_variable}++;")
            lines.append(f"    return {mock_func.return_variable};")
            lines.append(f"}}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_reset_function(self) -> str:
        """
        モックをリセットする関数を生成
        
        Returns:
            リセット関数のコード
        """
        lines = ["// ===== モックリセット関数 ====="]
        lines.append("")
        lines.append("/**")
        lines.append(" * 全てのモックをリセット")
        lines.append(" */")
        lines.append("static void reset_all_mocks(void) {")
        
        for mock_func in self.mock_functions:
            lines.append(f"    {mock_func.return_variable} = 0;")
            lines.append(f"    {mock_func.call_count_variable} = 0;")
        
        lines.append("}")
        
        return '\n'.join(lines)
    
    def generate_prototypes(self) -> str:
        """
        モック関数のプロトタイプ宣言を生成
        
        Returns:
            プロトタイプ宣言のコード
        """
        lines = ["// ===== プロトタイプ宣言（モック・スタブ） ====="]
        
        for mock_func in self.mock_functions:
            lines.append(f"static {mock_func.return_type} mock_{mock_func.name}(void);")
        
        lines.append("static void reset_all_mocks(void);")
        
        return '\n'.join(lines)
    
    def generate_setup_code(self, test_case_no: int) -> str:
        """
        テストケースのセットアップコードを生成
        
        Args:
            test_case_no: テストケース番号
        
        Returns:
            セットアップコード
        """
        lines = []
        lines.append("    // モックをリセット")
        lines.append("    reset_all_mocks();")
        lines.append("")
        
        return '\n'.join(lines)
    
    def generate_assert_call_counts(self) -> str:
        """
        呼び出し回数のアサートコードを生成
        
        Returns:
            アサートコード
        """
        lines = []
        lines.append("    // 呼び出し回数の確認")
        
        for mock_func in self.mock_functions:
            lines.append(f"    // TEST_ASSERT_EQUAL(expected_count, {mock_func.call_count_variable});  // TODO: 期待回数を設定後コメント解除")
        
        return '\n'.join(lines)


if __name__ == "__main__":
    # MockGeneratorのテスト
    print("=" * 70)
    print("MockGenerator のテスト")
    print("=" * 70)
    print()
    
    from src.data_structures import ParsedData
    
    # テスト用のParseDataを作成
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="test_func",
        external_functions=['f4', 'mx27', 'mx52', 'f18']
    )
    
    # モックを生成
    generator = MockGenerator()
    mock_code = generator.generate_mocks(parsed_data)
    
    print("生成されたモックコード:")
    print("=" * 70)
    print(mock_code)
    print("=" * 70)
    print()
    
    # プロトタイプ宣言
    print("プロトタイプ宣言:")
    print("=" * 70)
    print(generator.generate_prototypes())
    print("=" * 70)
    print()
    
    # セットアップコード
    print("セットアップコード:")
    print("=" * 70)
    print(generator.generate_setup_code(1))
    print("=" * 70)
    print()
    
    # アサートコード
    print("アサートコード:")
    print("=" * 70)
    print(generator.generate_assert_call_counts())
    print("=" * 70)
    print()
    
    print("✓ MockGeneratorが正常に動作しました")
