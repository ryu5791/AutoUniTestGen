"""
UnityTestGeneratorモジュール

全てのコンポーネントを統合してUnityテストコードを生成
"""

import sys
import os
from typing import Optional

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import ParsedData, TruthTableData, TestCode
from src.test_generator.mock_generator import MockGenerator
from src.test_generator.test_function_generator import TestFunctionGenerator
from src.test_generator.prototype_generator import PrototypeGenerator
from src.test_generator.comment_generator import CommentGenerator


class UnityTestGenerator:
    """Unityテストジェネレータ"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.mock_gen = MockGenerator()
        self.test_func_gen = TestFunctionGenerator()
        self.proto_gen = PrototypeGenerator()
        self.comment_gen = CommentGenerator()
    
    def generate(self, truth_table: TruthTableData, parsed_data: ParsedData) -> TestCode:
        """
        Unityテストコードを生成
        
        Args:
            truth_table: 真偽表データ
            parsed_data: 解析済みデータ
        
        Returns:
            TestCode
        """
        self.logger.info("Unityテストコードの生成を開始")
        
        test_code = TestCode()
        
        # 1. ヘッダー
        test_code.header = self._generate_header(parsed_data)
        
        # 2. #include文
        test_code.includes = self._generate_includes()
        
        # 3. 型定義
        test_code.type_definitions = self._generate_type_definitions()
        
        # 4. プロトタイプ宣言
        test_code.prototypes = self.proto_gen.generate_prototypes(truth_table, parsed_data)
        
        # 5. モック変数とモック関数
        mock_code = self.mock_gen.generate_mocks(parsed_data)
        parts = mock_code.split('\n\n')
        if len(parts) >= 2:
            test_code.mock_variables = parts[0]
            test_code.mock_functions = '\n\n'.join(parts[1:])
        else:
            test_code.mock_functions = mock_code
        
        # 6. テスト関数群
        test_code.test_functions = self._generate_all_test_functions(truth_table, parsed_data)
        
        # 7. setUp/tearDown
        test_code.setup_teardown = self._generate_setup_teardown()
        
        self.logger.info(f"Unityテストコードの生成が完了: {len(truth_table.test_cases)}個のテスト関数")
        
        return test_code
    
    def _generate_header(self, parsed_data: ParsedData) -> str:
        """
        ヘッダーコメントを生成
        
        Args:
            parsed_data: 解析済みデータ
        
        Returns:
            ヘッダーコメント
        """
        lines = []
        lines.append("/*")
        lines.append(f" * test_{parsed_data.function_name}_mcdc.c")
        lines.append(f" * {parsed_data.function_name}関数のMC/DC 100%カバレッジ単体テスト")
        lines.append(" *")
        lines.append(" * このファイルは自動生成されました")
        lines.append(" * MC/DC (Modified Condition/Decision Coverage) 100%達成を目的としたテスト")
        lines.append(" */")
        
        return '\n'.join(lines)
    
    def _generate_includes(self) -> str:
        """
        #include文を生成
        
        Returns:
            #include文
        """
        lines = []
        lines.append("#include \"unity.h\"")
        lines.append("#include <stdint.h>")
        lines.append("#include <stdbool.h>")
        lines.append("#include <string.h>")
        lines.append("#include <limits.h>")
        
        return '\n'.join(lines)
    
    def _generate_type_definitions(self) -> str:
        """
        型定義を生成
        
        Returns:
            型定義
        """
        lines = []
        lines.append("// ===== テスト対象関数のプロトタイプ宣言 =====")
        lines.append("// extern void target_function(void);")
        lines.append("")
        lines.append("// ===== テスト対象関数で使用される型定義 =====")
        lines.append("// typedef enum { ... } MyEnum;")
        lines.append("")
        lines.append("// ===== 外部変数（テスト対象関数で使用） =====")
        lines.append("// extern int global_var;")
        
        return '\n'.join(lines)
    
    def _generate_all_test_functions(self, truth_table: TruthTableData, parsed_data: ParsedData) -> str:
        """
        全てのテスト関数を生成
        
        Args:
            truth_table: 真偽表データ
            parsed_data: 解析済みデータ
        
        Returns:
            テスト関数群
        """
        lines = []
        lines.append("// ===== テスト関数 =====")
        lines.append("")
        
        # テストケースサマリー
        summary = self.comment_gen.generate_test_summary(truth_table.test_cases)
        lines.append(summary)
        lines.append("")
        
        # 各テスト関数を生成
        for test_case in truth_table.test_cases:
            test_func = self.test_func_gen.generate_test_function(test_case, parsed_data)
            lines.append(test_func)
            lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_setup_teardown(self) -> str:
        """
        setUp/tearDown関数を生成
        
        Returns:
            setUp/tearDown関数
        """
        lines = []
        lines.append("// ===== setUp/tearDown =====")
        lines.append("")
        lines.append("/**")
        lines.append(" * 各テストの前に実行")
        lines.append(" */")
        lines.append("void setUp(void) {")
        lines.append("    // モックをリセット")
        lines.append("    reset_all_mocks();")
        lines.append("}")
        lines.append("")
        lines.append("/**")
        lines.append(" * 各テストの後に実行")
        lines.append(" */")
        lines.append("void tearDown(void) {")
        lines.append("    // クリーンアップ処理")
        lines.append("}")
        
        return '\n'.join(lines)


if __name__ == "__main__":
    # UnityTestGeneratorのテスト
    print("=" * 70)
    print("UnityTestGenerator のテスト")
    print("=" * 70)
    print()
    
    from src.data_structures import ParsedData, TruthTableData, TestCase, Condition, ConditionType
    
    # テスト用データ
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="test_func",
        external_functions=['f4', 'mx27'],
        global_variables=['v9', 'mx63', 'v10']
    )
    
    # 条件を追加
    parsed_data.conditions.append(
        Condition(
            line=10,
            type=ConditionType.SIMPLE_IF,
            expression="(v10 > 30)"
        )
    )
    
    truth_table = TruthTableData(
        function_name="test_func",
        test_cases=[
            TestCase(no=1, truth="T", condition="if (v10 > 30)", expected="条件が真の処理を実行"),
            TestCase(no=2, truth="F", condition="if (v10 > 30)", expected="条件が偽の処理を実行"),
        ],
        total_tests=2
    )
    
    # Unityテストコードを生成
    generator = UnityTestGenerator()
    test_code = generator.generate(truth_table, parsed_data)
    
    # 生成されたコードを表示
    print("生成されたUnityテストコード:")
    print("=" * 70)
    full_code = test_code.to_string()
    
    # 最初の100行を表示
    lines = full_code.split('\n')
    for i, line in enumerate(lines[:100], 1):
        print(f"{i:3d}: {line}")
    
    if len(lines) > 100:
        print(f"\n... 他 {len(lines) - 100} 行")
    
    print()
    print("=" * 70)
    print(f"総行数: {len(lines)}行")
    print()
    
    # ファイルに保存
    output_file = "/tmp/test_generated_unity.c"
    test_code.save(output_file)
    print(f"✓ ファイルに保存: {output_file}")
    print()
    
    print("✓ UnityTestGeneratorが正常に動作しました")
