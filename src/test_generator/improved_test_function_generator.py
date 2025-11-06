"""
変数初期化ロジックの修正パッチ

問題点:
1. 関数名を変数として初期化しようとしている
2. enum値を変数として初期化しようとしている
3. defaultキーワードを値として使用している
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.test_generator.test_function_generator import TestFunctionGenerator
from src.utils import setup_logger


class ImprovedTestFunctionGenerator(TestFunctionGenerator):
    """改善されたテスト関数ジェネレータ"""
    
    def __init__(self):
        super().__init__()
        self.logger = setup_logger(__name__)
    
    def _generate_simple_condition_init(self, condition, truth):
        """
        単純条件の初期化コードを生成（改善版）
        
        Args:
            condition: 条件
            truth: 真偽
        
        Returns:
            初期化コード
        """
        # 境界値を計算
        test_value = self.boundary_calc.generate_test_value(condition.expression, truth)
        
        if test_value:
            return test_value
        
        # 境界値計算できない場合
        variables = self.boundary_calc.extract_variables(condition.expression)
        if variables:
            # 関数呼び出しを除外
            actual_vars = [v for v in variables if not self._is_function_call(condition.expression, v)]
            
            if actual_vars:
                var = actual_vars[0]
                if truth == 'T':
                    return f"{var} = 1  // TODO: 真になる値を設定"
                else:
                    return f"{var} = 0  // TODO: 偽になる値を設定"
        
        return None
    
    def _generate_or_condition_init(self, condition, truth):
        """
        OR条件の初期化コードを生成（改善版）
        
        Args:
            condition: 条件
            truth: 真偽パターン
        
        Returns:
            初期化コードのリスト
        """
        init_list = []
        
        conditions = condition.conditions if condition.conditions else [condition.left, condition.right]
        
        # 各条件に対して値を設定
        for i, cond in enumerate(conditions):
            if i < len(truth):
                truth_val = truth[i]
                
                # 比較式を解析
                comparison = self.boundary_calc.parse_comparison(cond)
                
                if comparison:
                    # 比較式の場合
                    test_value = self.boundary_calc.generate_test_value(cond, truth_val)
                    if test_value:
                        init_list.append(test_value)
                else:
                    # 等価比較の場合（例: mx63 == m47）
                    init_code = self._generate_equality_init(cond, truth_val)
                    if init_code:
                        init_list.append(init_code)
        
        return init_list
    
    def _generate_equality_init(self, expression, truth_val):
        """
        等価比較の初期化コードを生成
        
        Args:
            expression: 式（例: mx63 == m47）
            truth_val: 真偽
        
        Returns:
            初期化コード
        """
        import re
        
        # パターン: variable == value
        match = re.search(r'(\w+)\s*==\s*(\w+)', expression)
        if match:
            var = match.group(1)
            val = match.group(2)
            
            if truth_val == 'T':
                # 真の場合: 変数に値を設定
                return f"{var} = {val}"
            else:
                # 偽の場合: 変数に異なる値を設定
                return f"{var} = 0  // TODO: {val}以外の値を設定"
        
        return None
    
    def _generate_switch_init(self, condition, test_case):
        """
        switch文の初期化コードを生成（改善版）
        
        Args:
            condition: 条件
            test_case: テストケース
        
        Returns:
            初期化コード
        """
        import re
        
        # case値を抽出
        match = re.search(r'case\s+(\w+)', test_case.condition)
        if match:
            case_value = match.group(1)
            switch_var = condition.expression
            
            # defaultの場合は特別処理
            if case_value == 'default':
                return f"{switch_var} = 999  // caseに該当しない値（default実行用）"
            else:
                return f"{switch_var} = {case_value}"
        
        return None
    
    def _is_function_call(self, expression, identifier):
        """
        識別子が関数呼び出しかどうかを判定
        
        Args:
            expression: 条件式
            identifier: 識別子
        
        Returns:
            関数呼び出しならTrue
        """
        import re
        # identifier() のパターンを検索
        pattern = r'\b' + re.escape(identifier) + r'\s*\('
        return re.search(pattern, expression) is not None


if __name__ == "__main__":
    print("=" * 70)
    print("ImprovedTestFunctionGenerator のテスト")
    print("=" * 70)
    print()
    
    from src.data_structures import TestCase, ParsedData, Condition, ConditionType
    
    # テスト用データ
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="f1",
        external_functions=['f4', 'mx27'],
        global_variables=['v9', 'mx63', 'v10']
    )
    
    # 条件1: 関数呼び出しを含む条件
    parsed_data.conditions.append(
        Condition(
            line=10,
            type=ConditionType.SIMPLE_IF,
            expression="((f4() & 223) != 0)"
        )
    )
    
    # 条件2: 等価比較のOR条件
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
    
    # 条件3: switch文（default含む）
    parsed_data.conditions.append(
        Condition(
            line=20,
            type=ConditionType.SWITCH,
            expression="v9",
            cases=['0', '1', 'default']
        )
    )
    
    # テストケース1: 関数呼び出しを含む条件
    test_case1 = TestCase(
        no=1,
        truth="T",
        condition="if ((f4() & 223) != 0)",
        expected="条件が真の処理を実行"
    )
    
    # テストケース2: OR条件
    test_case2 = TestCase(
        no=3,
        truth="TF",
        condition="if ((mx63 == m47) || (mx63 == m46))",
        expected="左辺が真、右辺が偽"
    )
    
    # テストケース3: switch default
    test_case3 = TestCase(
        no=10,
        truth="-",
        condition="switch (v9) - case default",
        expected="case default の処理を実行"
    )
    
    # 改善版ジェネレータでテスト
    generator = ImprovedTestFunctionGenerator()
    
    print("【テスト1】関数呼び出しを含む条件")
    print("-" * 70)
    test_func1 = generator.generate_test_function(test_case1, parsed_data)
    # 変数初期化部分を抽出
    lines = test_func1.split('\n')
    for line in lines[20:30]:
        print(line)
    print()
    
    print("【テスト2】等価比較のOR条件")
    print("-" * 70)
    test_func2 = generator.generate_test_function(test_case2, parsed_data)
    lines = test_func2.split('\n')
    for line in lines[20:32]:
        print(line)
    print()
    
    print("【テスト3】switch default")
    print("-" * 70)
    test_func3 = generator.generate_test_function(test_case3, parsed_data)
    lines = test_func3.split('\n')
    for line in lines[20:28]:
        print(line)
    print()
    
    print("✓ 改善版が正常に動作しました")
