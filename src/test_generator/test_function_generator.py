"""
TestFunctionGeneratorモジュール

Unityテスト関数を生成
"""

import sys
import os
import re
from typing import List, Dict, Optional

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger, sanitize_identifier
from src.data_structures import TestCase, ParsedData, Condition, ConditionType
from src.test_generator.boundary_value_calculator import BoundaryValueCalculator
from src.test_generator.comment_generator import CommentGenerator


class TestFunctionGenerator:
    """テスト関数ジェネレータ"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.boundary_calc = BoundaryValueCalculator()
        self.comment_gen = CommentGenerator()
    
    def generate_test_function(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        テスト関数を生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            テスト関数のコード
        """
        lines = []
        
        # ヘッダコメント
        comment = self.comment_gen.generate_comment(test_case, parsed_data)
        lines.append(comment)
        
        # 関数名を生成
        func_name = self._generate_test_name(test_case, parsed_data)
        
        # 関数定義
        lines.append(f"void {func_name}(void) {{")
        
        # 変数初期化
        init_code = self._generate_variable_init(test_case, parsed_data)
        if init_code:
            lines.append(init_code)
        
        # モック設定
        mock_setup = self._generate_mock_setup(test_case, parsed_data)
        if mock_setup:
            lines.append(mock_setup)
        
        # 対象関数呼び出し
        lines.append(f"    // 対象関数を実行")
        lines.append(f"    {parsed_data.function_name}();")
        lines.append("")
        
        # アサーション
        assertions = self._generate_assertions(test_case, parsed_data)
        if assertions:
            lines.append(assertions)
        
        # 呼び出し回数チェック
        call_count_check = self._generate_call_count_check(test_case, parsed_data)
        if call_count_check:
            lines.append(call_count_check)
        
        # 関数終了
        lines.append("}")
        
        return '\n'.join(lines)
    
    def _generate_test_name(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        テスト名を生成
        
        ルール: test_[番号]_[判定文]_[真偽]
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            テスト関数名
        """
        # テスト番号（2桁）
        test_no = f"{test_case.no:02d}"
        
        # 判定文から識別子を生成
        # 対応する条件を検索
        matching_condition = None
        for cond in parsed_data.conditions:
            if cond.expression in test_case.condition:
                matching_condition = cond
                break
        
        if matching_condition:
            # 条件式から主要な変数や演算を抽出
            condition_part = self._extract_condition_identifier(matching_condition)
        else:
            # フォールバック
            condition_part = "condition"
        
        # 真偽パターン
        truth_part = test_case.truth.replace(' ', '') if test_case.truth else "test"
        
        # 組み合わせ
        func_name = f"test_{test_no}_{condition_part}_{truth_part}"
        
        # 識別子として有効な形に
        func_name = sanitize_identifier(func_name)
        
        # 長すぎる場合は短縮
        if len(func_name) > 60:
            func_name = func_name[:60]
        
        return func_name
    
    def _extract_condition_identifier(self, condition: Condition) -> str:
        """
        条件から識別子を抽出
        
        Args:
            condition: 条件
        
        Returns:
            識別子
        """
        expr = condition.expression
        
        # 括弧や空白を削除
        expr = expr.replace('(', '').replace(')', '').replace(' ', '_')
        
        # 演算子を置換
        replacements = {
            '==': 'eq',
            '!=': 'ne',
            '>=': 'ge',
            '<=': 'le',
            '>': 'gt',
            '<': 'lt',
            '||': 'or',
            '&&': 'and',
            '&': 'and',
            '|': 'or',
            '[': '_',
            ']': '',
        }
        
        for old, new in replacements.items():
            expr = expr.replace(old, new)
        
        # 複数のアンダースコアを1つに
        expr = re.sub(r'_+', '_', expr)
        
        # 先頭と末尾のアンダースコアを削除
        expr = expr.strip('_')
        
        # 長さ制限
        if len(expr) > 40:
            # 最初の変数名を優先
            parts = expr.split('_')
            if parts:
                expr = '_'.join(parts[:3])  # 最初の3パーツ
        
        return expr
    
    def _generate_variable_init(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        変数初期化コードを生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コード
        """
        lines = []
        lines.append("    // 変数を初期化")
        
        # 対応する条件を検索
        matching_condition = None
        for cond in parsed_data.conditions:
            if cond.expression in test_case.condition:
                matching_condition = cond
                break
        
        if not matching_condition:
            lines.append("    // TODO: 変数を初期化")
            lines.append("")
            return '\n'.join(lines)
        
        # 条件タイプに応じて初期化コードを生成
        if matching_condition.type == ConditionType.SIMPLE_IF:
            init = self._generate_simple_condition_init(matching_condition, test_case.truth, parsed_data)
            if init:
                lines.append(f"    {init};")
        
        elif matching_condition.type == ConditionType.OR_CONDITION:
            init_list = self._generate_or_condition_init(matching_condition, test_case.truth, parsed_data)
            for init in init_list:
                lines.append(f"    {init};")
        
        elif matching_condition.type == ConditionType.AND_CONDITION:
            init_list = self._generate_and_condition_init(matching_condition, test_case.truth, parsed_data)
            for init in init_list:
                lines.append(f"    {init};")
        
        elif matching_condition.type == ConditionType.SWITCH:
            init = self._generate_switch_init(matching_condition, test_case, parsed_data)
            if init:
                lines.append(f"    {init};")
        
        lines.append("")
        return '\n'.join(lines)
    
    def _generate_simple_condition_init(self, condition: Condition, truth: str, parsed_data: ParsedData) -> Optional[str]:
        """
        単純条件の初期化コードを生成
        
        Args:
            condition: 条件
            truth: 真偽
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コード
        """
        # 境界値を計算
        test_value = self.boundary_calc.generate_test_value(condition.expression, truth)
        
        if test_value:
            # 生成された初期化コードが関数やenum定数を使っていないか検証
            test_value = self._validate_and_fix_init_code(test_value, parsed_data)
            return test_value
        
        # 境界値計算できない場合
        variables = self.boundary_calc.extract_variables(condition.expression)
        if variables:
            var = variables[0]
            # 関数かenum定数でないことを確認
            if self._is_function_or_enum(var, parsed_data):
                return f"// TODO: {var}は関数またはenum定数のため初期化できません"
            
            if truth == 'T':
                return f"{var} = 1  // TODO: 真になる値を設定"
            else:
                return f"{var} = 0  // TODO: 偽になる値を設定"
        
        return None
    
    def _generate_or_condition_init(self, condition: Condition, truth: str, parsed_data: ParsedData) -> List[str]:
        """
        OR条件の初期化コードを生成
        
        Args:
            condition: 条件
            truth: 真偽パターン
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コードのリスト
        """
        init_list = []
        
        conditions = condition.conditions if condition.conditions else [condition.left, condition.right]
        
        # 各条件に対して値を設定
        for i, cond in enumerate(conditions):
            if i < len(truth):
                truth_val = truth[i]
                test_value = self.boundary_calc.generate_test_value(cond, truth_val)
                
                if test_value:
                    # 関数やenum定数の誤使用を修正
                    test_value = self._validate_and_fix_init_code(test_value, parsed_data)
                    init_list.append(test_value)
                else:
                    # デフォルト値
                    variables = self.boundary_calc.extract_variables(cond)
                    if variables:
                        var = variables[0]
                        # 関数またはenum定数でないことを確認
                        if self._is_function_or_enum(var, parsed_data):
                            init_list.append(f"// TODO: {var}は関数またはenum定数のため初期化できません")
                        else:
                            val = '1' if truth_val == 'T' else '0'
                            init_list.append(f"{var} = {val}  // TODO: 適切な値を設定")
        
        return init_list
    
    def _generate_and_condition_init(self, condition: Condition, truth: str, parsed_data: ParsedData) -> List[str]:
        """
        AND条件の初期化コードを生成
        
        Args:
            condition: 条件
            truth: 真偽パターン
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コードのリスト
        """
        # OR条件と同じロジック
        return self._generate_or_condition_init(condition, truth, parsed_data)
    
    def _generate_switch_init(self, condition: Condition, test_case: TestCase, parsed_data: ParsedData) -> Optional[str]:
        """
        switch文の初期化コードを生成
        
        Args:
            condition: 条件
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コード
        """
        switch_var = condition.expression
        
        # default caseの場合（先にチェック）
        if 'case default' in test_case.condition.lower() or test_case.condition.lower().endswith('default'):
            # caseに該当しない値を設定（999など）
            return f"{switch_var} = 999  // default: caseに該当しない値"
        
        # 通常のcase値を抽出
        match = re.search(r'case\s+(\w+)', test_case.condition)
        if match:
            case_value = match.group(1)
            
            # case_valueが関数またはenum定数かチェック
            if self._is_function(case_value, parsed_data):
                # 関数の場合はモックの戻り値を使用
                return f"{switch_var} = mock_{case_value}_return_value"
            elif self._is_enum_constant(case_value, parsed_data):
                # enum定数の場合は別の変数に代入
                return f"{switch_var} = {case_value}"
            else:
                return f"{switch_var} = {case_value}"
        
        return None


    def _generate_mock_setup(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        モック設定コードを生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            モック設定コード
        """
        lines = []
        lines.append("    // モックを設定")
        
        # 外部関数のモック戻り値を設定
        # TODO: 実際の値は条件に応じて決定
        for func_name in parsed_data.external_functions:
            lines.append(f"    mock_{func_name}_return_value = 0;  // TODO: 適切な値を設定")
        
        lines.append("")
        return '\n'.join(lines)
    
    def _generate_assertions(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        アサーションコードを生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            アサーションコード
        """
        lines = []
        lines.append("    // 結果を確認")
        
        # グローバル変数の確認
        for var in parsed_data.global_variables[:3]:  # 最初の3つ
            lines.append(f"    TEST_ASSERT_EQUAL(/* 期待値 */, {var});")
        
        lines.append("")
        return '\n'.join(lines)
    
    def _generate_call_count_check(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        呼び出し回数チェックコードを生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            呼び出し回数チェックコード
        """
        lines = []
        lines.append("    // 呼び出し回数を確認")
        
        for func_name in parsed_data.external_functions:
            # 条件式に含まれているか確認
            if func_name in test_case.condition:
                expected_count = 1
            else:
                expected_count = 0
            
            lines.append(f"    TEST_ASSERT_EQUAL({expected_count}, mock_{func_name}_call_count);")
        
        lines.append("")
        return '\n'.join(lines)


    def _is_function(self, name: str, parsed_data: ParsedData) -> bool:
        """
        指定された名前が関数かどうか判定
        
        Args:
            name: 識別子名
            parsed_data: 解析済みデータ
        
        Returns:
            関数の場合True
        """
        return name in parsed_data.external_functions
    
    def _is_enum_constant(self, name: str, parsed_data: ParsedData) -> bool:
        """
        指定された名前がenum定数かどうか判定
        
        Args:
            name: 識別子名
            parsed_data: 解析済みデータ
        
        Returns:
            enum定数の場合True
        """
        return name in parsed_data.enum_values
    
    def _is_function_or_enum(self, name: str, parsed_data: ParsedData) -> bool:
        """
        指定された名前が関数またはenum定数かどうか判定
        
        Args:
            name: 識別子名
            parsed_data: 解析済みデータ
        
        Returns:
            関数またはenum定数の場合True
        """
        return self._is_function(name, parsed_data) or self._is_enum_constant(name, parsed_data)
    
    def _validate_and_fix_init_code(self, init_code: str, parsed_data: ParsedData) -> str:
        """
        初期化コードを検証して問題があれば修正
        
        Args:
            init_code: 初期化コード
            parsed_data: 解析済みデータ
        
        Returns:
            修正後の初期化コード
        """
        # "変数 = 値" の形式から変数と値を抽出
        match = re.match(r'(\w+)\s*=\s*(.+)', init_code)
        if not match:
            return init_code
        
        var_name = match.group(1)
        value_part = match.group(2).strip()
        
        # 値の部分に関数が含まれている場合
        if self._is_function(value_part, parsed_data):
            # 関数の場合はモックの戻り値を使用
            return f"{var_name} = mock_{value_part}_return_value  // 修正: {value_part}は関数"
        
        # 値の部分にenum定数が含まれている場合はそのまま（正しい使い方）
        
        # 変数自体が関数の場合（エラー）
        if self._is_function(var_name, parsed_data):
            return f"// ERROR: {var_name}は関数のため変数として初期化できません。モック設定を使用してください。"
        
        # 変数自体がenum定数の場合（エラー）
        if self._is_enum_constant(var_name, parsed_data):
            # enum定数は代入できないので、適切な変数を見つける
            # グローバル変数の中から適切なものを探す
            for gvar in parsed_data.global_variables:
                if not self._is_function_or_enum(gvar, parsed_data):
                    return f"{gvar} = {value_part}  // 修正: {var_name}はenum定数のため{gvar}に代入"
            return f"// ERROR: {var_name}はenum定数のため変数として初期化できません"
        
        return init_code


if __name__ == "__main__":
    # TestFunctionGeneratorのテスト
    print("=" * 70)
    print("TestFunctionGenerator のテスト")
    print("=" * 70)
    print()
    
    from src.data_structures import TestCase, ParsedData, Condition, ConditionType
    
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
    
    parsed_data.conditions.append(
        Condition(
            line=15,
            type=ConditionType.OR_CONDITION,
            expression="((mx63 == m47) || (mx63 == m46))",
            operator='or',
            left="(mx63 == m47)",
            right="(mx63 == m46)",
            conditions=["(mx63 == m47)", "(mx63 == m46)"]
        )
    )
    
    # テストケース
    test_case1 = TestCase(
        no=1,
        truth="T",
        condition="if (v10 > 30)",
        expected="条件が真の処理を実行"
    )
    
    test_case2 = TestCase(
        no=3,
        truth="TF",
        condition="if ((mx63 == m47) || (mx63 == m46))",
        expected="左辺が真、右辺が偽"
    )
    
    # テスト関数を生成
    generator = TestFunctionGenerator()
    
    print("テスト1: 単純条件のテスト関数")
    print("=" * 70)
    print(generator.generate_test_function(test_case1, parsed_data))
    print()
    print()
    
    print("テスト2: OR条件のテスト関数")
    print("=" * 70)
    print(generator.generate_test_function(test_case2, parsed_data))
    print()
    
    print("✓ TestFunctionGeneratorが正常に動作しました")

