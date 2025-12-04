"""
UnityTestGeneratorモジュール

全てのコンポーネントを統合してUnityテストコードを生成
"""

import sys
import os
from typing import Optional, List

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import ParsedData, TruthTableData, TestCode, TestCase
from src.test_generator.mock_generator import MockGenerator
from src.test_generator.test_function_generator import TestFunctionGenerator
from src.test_generator.prototype_generator import PrototypeGenerator
from src.test_generator.comment_generator import CommentGenerator
from src.code_extractor.code_extractor import CodeExtractor  # v2.2: 関数抽出機能


class UnityTestGenerator:
    """Unityテストジェネレータ"""
    
    def __init__(self, include_target_function: bool = True):
        """
        初期化
        
        Args:
            include_target_function: テスト対象関数の本体を含めるか（v2.2の新機能）
        """
        self.logger = setup_logger(__name__)
        self.mock_gen = MockGenerator()
        self.test_func_gen = TestFunctionGenerator()
        self.proto_gen = PrototypeGenerator()
        self.comment_gen = CommentGenerator()
        self.code_extractor = CodeExtractor()  # v2.2: 関数抽出機能
        self.include_target_function = include_target_function  # v2.2
    
    def generate(self, truth_table: TruthTableData, parsed_data: ParsedData, 
                 source_code: Optional[str] = None) -> TestCode:
        """
        Unityテストコードを生成
        
        Args:
            truth_table: 真偽表データ
            parsed_data: 解析済みデータ
            source_code: 元のソースコード（v2.2: 関数本体抽出用、Noneの場合は抽出しない）
        
        Returns:
            TestCode
        """
        self.logger.info("Unityテストコードの生成を開始")
        
        test_code = TestCode()
        
        # 1. ヘッダー
        test_code.header = self._generate_header(parsed_data)
        
        # 2. #include文
        test_code.includes = self._generate_includes()
        
        # 3. 型定義（v2.2: parsed_dataを渡して自動生成）
        test_code.type_definitions = self._generate_type_definitions(parsed_data)
        
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
        
        # 8. v2.2: テスト対象関数の本体を抽出して追加
        if self.include_target_function and source_code:
            self.logger.info("v2.2: テスト対象関数の本体を抽出中...")
            target_code = self._extract_target_function(source_code, parsed_data.function_name)
            if target_code:
                test_code.target_function_code = target_code
                self.logger.info("✓ v2.2: テスト対象関数の本体を追加しました")
            else:
                self.logger.warning("✗ v2.2: テスト対象関数の本体が抽出できませんでした")
        
        # 9. v2.3: main関数を生成
        test_code.main_function = self._generate_main_function(truth_table, parsed_data)
        
        self.logger.info(f"Unityテストコードの生成が完了: {len(truth_table.test_cases)}個のテスト関数")
        
        return test_code
    
    def generate_standalone(self, truth_table: TruthTableData, parsed_data: ParsedData, 
                           source_code: str) -> str:
        """
        元のソースファイル全体にテストコードを追加したスタンドアロン版を生成（v2.4.3）
        
        Args:
            truth_table: 真偽表データ
            parsed_data: 解析済みデータ
            source_code: 元のソースコード全体
        
        Returns:
            str: スタンドアロンテストコード（元のソース + テストコード）
        """
        self.logger.info("v2.4.3: スタンドアロン版テストコードの生成を開始")
        
        # v4.3.4.1: 外部関数のプロトタイプ宣言をstaticに変換
        modified_source = self._convert_external_prototypes_to_static(
            source_code, parsed_data.external_functions
        )
        
        # 元のソースコードをベースにする
        parts = [modified_source]
        
        # 区切り線を追加
        parts.append("\n\n" + "//" + "=" * 78)
        parts.append("// 以下、自動生成されたテストコード")
        parts.append("//" + "=" * 78 + "\n")
        
        # Unity framework のインクルード
        parts.append('#include "unity.h"')
        
        # モック変数とモック関数
        mock_code = self.mock_gen.generate_mocks(parsed_data)
        if mock_code:
            parts.append("\n// ===== モック変数とモック関数 =====")
            parts.append(mock_code)
        
        # テスト関数群
        test_functions = self._generate_all_test_functions(truth_table, parsed_data)
        if test_functions:
            parts.append("\n// ===== テスト関数群 =====")
            parts.append(test_functions)
        
        # setUp/tearDown
        setup_teardown = self._generate_setup_teardown()
        if setup_teardown:
            parts.append("\n// ===== setUp/tearDown =====")
            parts.append(setup_teardown)
        
        # main関数
        main_function = self._generate_main_function(truth_table, parsed_data)
        if main_function:
            parts.append("\n// ===== main関数 =====")
            parts.append(main_function)
        
        result = '\n'.join(parts)
        
        self.logger.info(f"✓ v2.4.3: スタンドアロン版テストコード生成完了")
        
        return result
    
    def _convert_external_prototypes_to_static(self, source_code: str, 
                                                external_functions: list) -> str:
        """
        外部関数のプロトタイプ宣言をstaticに変換（v4.3.4.1）
        
        モック関数と同じシグネチャにするため、元のプロトタイプ宣言にstaticを追加
        
        Args:
            source_code: 元のソースコード
            external_functions: 外部関数名のリスト
        
        Returns:
            変換後のソースコード
        """
        import re
        
        if not external_functions:
            return source_code
        
        modified = source_code
        
        for func_name in external_functions:
            # プロトタイプ宣言のパターン: 戻り値型 関数名(...);
            # static がまだ付いていないものを対象
            # 例: void Utf18(const Utx174 Utx40);
            #     uint8_t Utf8(void);
            pattern = rf'^(\s*)((?:(?:const\s+)?(?:unsigned\s+|signed\s+)?(?:\w+)(?:\s*\*)?)\s+)({re.escape(func_name)})\s*\(([^)]*)\)\s*;'
            
            def add_static(match):
                indent = match.group(1)
                return_type = match.group(2)
                name = match.group(3)
                params = match.group(4)
                # すでにstaticが付いていないか確認
                if 'static' in return_type:
                    return match.group(0)
                return f'{indent}static {return_type}{name}({params});'
            
            modified = re.sub(pattern, add_static, modified, flags=re.MULTILINE)
        
        return modified
    
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
    
    def _generate_type_definitions(self, parsed_data: ParsedData = None) -> str:
        """
        型定義を生成
        
        Args:
            parsed_data: 解析済みデータ（v2.2: 型定義・変数宣言の自動生成用）
        
        Returns:
            型定義
        """
        lines = []
        
        # v2.4.2: マクロ定義を先頭に追加
        if parsed_data and parsed_data.macro_definitions:
            lines.append("// ===== マクロ定義 =====")
            for macro_def in parsed_data.macro_definitions:
                lines.append(macro_def)
            lines.append("")
        
        # v2.2: テスト対象関数のプロトタイプ宣言
        lines.append("// ===== テスト対象関数のプロトタイプ宣言 =====")
        if parsed_data and parsed_data.function_info:
            func_info = parsed_data.function_info
            params = []
            if func_info.parameters:
                for param in func_info.parameters:
                    param_type = param.get('type', 'int')
                    param_name = param.get('name', '')
                    params.append(f"{param_type} {param_name}")
            param_str = ', '.join(params) if params else 'void'
            lines.append(f"extern {func_info.return_type} {func_info.name}({param_str});")
        elif parsed_data and parsed_data.function_name:
            # function_infoがない場合でも、関数名があればプロトタイプを生成
            lines.append(f"extern void {parsed_data.function_name}(void);")
            lines.append(f"// 注意: 関数情報が不完全なため、戻り値と引数を手動で修正してください")
        else:
            lines.append("// extern void target_function(void);")
            lines.append("// 警告: テスト対象関数の情報が取得できませんでした")
        lines.append("")
        
        # v2.2: 型定義の自動生成
        lines.append("// ===== テスト対象関数で使用される型定義 =====")
        if parsed_data and parsed_data.typedefs:
            # 依存関係を解決してソート
            from src.parser.dependency_resolver import DependencyResolver
            resolver = DependencyResolver()
            sorted_typedefs = resolver.resolve_order(parsed_data.typedefs)
            
            self.logger.info(f"型定義を {len(sorted_typedefs)} 個生成します")
            for typedef in sorted_typedefs:
                lines.append(typedef.definition)
                lines.append("")
        else:
            lines.append("// 型定義が検出されませんでした")
            lines.append("// 必要に応じて元のソースから手動でコピーしてください")
            lines.append("")
        
        # v2.2: 変数宣言の自動生成
        lines.append("// ===== 外部変数（テスト対象関数で使用） =====")
        if parsed_data and parsed_data.variables:
            extern_vars = [var for var in parsed_data.variables if var.is_extern]
            if extern_vars:
                self.logger.info(f"外部変数を {len(extern_vars)} 個生成します")
                for var in extern_vars:
                    lines.append(var.definition)
            else:
                lines.append("// 外部変数が検出されませんでした")
        else:
            lines.append("// 外部変数が検出されませんでした")
        
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
        
        # 各テスト関数を生成（プロトタイプ宣言 + 本体）
        for test_case in truth_table.test_cases:
            # テスト関数名を生成
            func_name = self.test_func_gen._generate_test_name(test_case, parsed_data)
            
            # プロトタイプ宣言を追加
            lines.append(f"// プロトタイプ宣言")
            lines.append(f"void {func_name}(void);")
            lines.append("")
            
            # テスト関数本体を生成
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
    
    def _extract_target_function(self, source_code: str, function_name: str) -> Optional[str]:
        """
        テスト対象関数の本体を抽出（v2.2の新機能）
        
        Args:
            source_code: 元のソースコード
            function_name: 対象関数名
            
        Returns:
            抽出されたコードセクション
        """
        try:
            # 関数本体のみを抽出（依存関係は今回は含めない）
            extracted = self.code_extractor.extract_function_only(source_code, function_name)
            
            if extracted and extracted.has_content():
                return extracted.to_code_section()
            
            return None
            
        except Exception as e:
            self.logger.error(f"関数抽出中にエラーが発生: {e}")
            return None
    
    def _generate_main_function(self, truth_table: TruthTableData, parsed_data: ParsedData) -> str:
        """
        main関数を生成（v2.3の新機能）
        
        Args:
            truth_table: 真偽表データ
            parsed_data: 解析済みデータ
            
        Returns:
            main関数のコード
        """
        lines = []
        lines.append("// ===== main関数 =====")
        lines.append("")
        lines.append("/**")
        lines.append(" * テストスイートのエントリーポイント")
        lines.append(" */")
        lines.append("int main(void) {")
        lines.append("    UNITY_BEGIN();")
        lines.append("    ")
        
        # ヘッダー情報
        lines.append("    printf(\"==============================================\\n\");")
        lines.append(f"    printf(\"{parsed_data.function_name} Function MC/DC 100%% Coverage Test Suite\\n\");")
        lines.append("    printf(\"==============================================\\n\");")
        lines.append("    printf(\"Target: MC/DC (Modified Condition/Decision Coverage) 100%%\\n\");")
        lines.append(f"    printf(\"Total Test Cases: {truth_table.total_tests}\\n\");")
        lines.append("    printf(\"==============================================\\n\\n\");")
        lines.append("    ")
        
        # 条件の種類別にテストケースをグループ化
        grouped_tests = self._group_test_cases_by_condition(truth_table.test_cases)
        
        # グループごとにRUN_TESTを生成
        for group_idx, (condition_desc, test_cases) in enumerate(grouped_tests, 1):
            if group_idx > 1:
                lines.append("    ")
            
            # グループのヘッダー
            start_no = test_cases[0].no
            end_no = test_cases[-1].no
            lines.append(f"    printf(\"--- {condition_desc} (No.{start_no}-{end_no}) ---\\n\");")
            
            # 各テストケースのRUN_TEST
            for test_case in test_cases:
                func_name = self.test_func_gen._generate_test_name(test_case, parsed_data)
                lines.append(f"    RUN_TEST({func_name});")
        
        lines.append("    ")
        lines.append("    return UNITY_END();")
        lines.append("}")
        
        return '\n'.join(lines)
    
    def _group_test_cases_by_condition(self, test_cases: List[TestCase]) -> List[tuple]:
        """
        テストケースを条件別にグループ化
        
        Args:
            test_cases: テストケースのリスト
            
        Returns:
            (条件の説明, テストケースのリスト)のタプルのリスト
        """
        if not test_cases:
            return []
        
        groups = []
        current_condition = None
        current_group = []
        
        for test_case in test_cases:
            # 条件を簡略化（長すぎる場合は切り詰め）
            condition = test_case.condition
            if len(condition) > 50:
                condition = condition[:47] + "..."
            
            if current_condition is None:
                current_condition = condition
                current_group = [test_case]
            elif current_condition == condition:
                current_group.append(test_case)
            else:
                # グループを保存
                groups.append((self._get_condition_description(current_condition), current_group))
                # 新しいグループを開始
                current_condition = condition
                current_group = [test_case]
        
        # 最後のグループを保存
        if current_group:
            groups.append((self._get_condition_description(current_condition), current_group))
        
        return groups
    
    def _get_condition_description(self, condition: str) -> str:
        """
        条件の説明を生成
        
        Args:
            condition: 条件式
            
        Returns:
            説明文
        """
        # "if (...)" や "switch (...)" から条件部分を抽出
        if "if" in condition:
            return "Condition Tests"
        elif "switch" in condition:
            return "Switch Case Tests"
        else:
            return "Tests"


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
