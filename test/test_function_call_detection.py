#!/usr/bin/env python3
"""
関数呼び出し検出機能のテスト
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

from src.test_generator.boundary_value_calculator import BoundaryValueCalculator
from src.test_generator.test_function_generator import TestFunctionGenerator
from src.data_structures import ParsedData, Condition, ConditionType

def test_function_call_detection():
    """関数呼び出しの検出テスト"""
    print("=" * 70)
    print("関数呼び出し検出テスト")
    print("=" * 70)
    print()
    
    calc = BoundaryValueCalculator()
    
    # テストケース1: 関数呼び出しと数値の比較
    print("テスト1: Utf12() != 0")
    expr1 = "Utf12() != 0"
    result1 = calc.parse_comparison(expr1)
    print(f"  入力: {expr1}")
    print(f"  結果: {result1}")
    print(f"  関数呼び出し検出: {result1.get('is_function_call', False) if result1 else False}")
    
    # テスト値生成を確認
    test_val_T = calc.generate_test_value(expr1, 'T')
    test_val_F = calc.generate_test_value(expr1, 'F')
    print(f"  真の場合の初期化コード: {test_val_T}")
    print(f"  偽の場合の初期化コード: {test_val_F}")
    print()
    
    # テストケース2: 変数と関数呼び出しの比較
    print("テスト2: v10 == Utf7()")
    expr2 = "v10 == Utf7()"
    result2 = calc.parse_comparison(expr2)
    print(f"  入力: {expr2}")
    print(f"  結果: {result2}")
    print(f"  右辺が関数: {result2.get('is_right_function', False) if result2 else False}")
    
    test_val_T = calc.generate_test_value(expr2, 'T')
    test_val_F = calc.generate_test_value(expr2, 'F')
    print(f"  真の場合の初期化コード: {test_val_T}")
    print(f"  偽の場合の初期化コード: {test_val_F}")
    print()
    
    # テストケース3: 通常の変数と数値の比較（関数呼び出しなし）
    print("テスト3: v10 > 30 (通常の比較)")
    expr3 = "v10 > 30"
    result3 = calc.parse_comparison(expr3)
    print(f"  入力: {expr3}")
    print(f"  結果: {result3}")
    print(f"  関数呼び出し検出: {result3.get('is_function_call', False) if result3 else False}")
    
    test_val_T = calc.generate_test_value(expr3, 'T')
    test_val_F = calc.generate_test_value(expr3, 'F')
    print(f"  真の場合の初期化コード: {test_val_T}")
    print(f"  偽の場合の初期化コード: {test_val_F}")
    print()
    
    # テストケース4: 関数呼び出しパターンの検出
    print("テスト4: _is_function_call() メソッドのテスト")
    test_patterns = [
        "Utf12()",
        "Utf7()",
        "UtD31(Utx171)",
        "variable",
        "array[0]",
        "struct.member"
    ]
    
    for pattern in test_patterns:
        is_func = calc._is_function_call(pattern)
        print(f"  {pattern:20s} -> {'関数呼び出し' if is_func else '通常の識別子'}")
    print()

def test_with_test_function_generator():
    """TestFunctionGeneratorでの統合テスト"""
    print("=" * 70)
    print("TestFunctionGeneratorでの統合テスト")
    print("=" * 70)
    print()
    
    # ParsedDataを作成
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="Utf1",
        external_functions=['Utf7', 'Utf12', 'UtD31'],
        global_variables=['v10', 'Utx171']
    )
    
    # 条件を追加
    condition1 = Condition(
        line=10,
        type=ConditionType.SIMPLE_IF,
        expression="Utf12() != 0"
    )
    
    condition2 = Condition(
        line=20,
        type=ConditionType.SIMPLE_IF,
        expression="v10 == Utf7()"
    )
    
    condition3 = Condition(
        line=30,
        type=ConditionType.SIMPLE_IF,
        expression="UtD31(Utx171) != 0"
    )
    
    parsed_data.conditions = [condition1, condition2, condition3]
    
    # TestFunctionGeneratorで初期化コードを生成
    generator = TestFunctionGenerator()
    
    print("条件1: Utf12() != 0 (真)")
    init1_T = generator._generate_simple_condition_init(condition1, 'T', parsed_data)
    print(f"  初期化コード: {init1_T}")
    print()
    
    print("条件1: Utf12() != 0 (偽)")
    init1_F = generator._generate_simple_condition_init(condition1, 'F', parsed_data)
    print(f"  初期化コード: {init1_F}")
    print()
    
    print("条件2: v10 == Utf7() (真)")
    init2_T = generator._generate_simple_condition_init(condition2, 'T', parsed_data)
    print(f"  初期化コード: {init2_T}")
    print()
    
    print("条件2: v10 == Utf7() (偽)")
    init2_F = generator._generate_simple_condition_init(condition2, 'F', parsed_data)
    print(f"  初期化コード: {init2_F}")
    print()
    
    print("条件3: UtD31(Utx171) != 0 (真)")
    init3_T = generator._generate_simple_condition_init(condition3, 'T', parsed_data)
    print(f"  初期化コード: {init3_T}")
    print()

if __name__ == "__main__":
    test_function_call_detection()
    print()
    test_with_test_function_generator()
    print()
    print("=" * 70)
    print("✓ すべてのテストが完了しました")
    print("=" * 70)
