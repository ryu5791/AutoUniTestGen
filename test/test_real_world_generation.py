#!/usr/bin/env python3
"""
実際のテストコード生成のテスト
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

from src.data_structures import ParsedData, Condition, ConditionType, TestCase
from src.test_generator.test_function_generator import TestFunctionGenerator

def test_real_world_scenario():
    """実際のコード生成シナリオをテスト"""
    print("=" * 70)
    print("実際のテストコード生成テスト")
    print("=" * 70)
    print()
    
    # ParsedDataを作成（22_難読化_obfuscated.cのUtf1関数を模倣）
    parsed_data = ParsedData(
        file_name="22_難読化_obfuscated.c",
        function_name="Utf1",
        external_functions=['UtD31', 'Utf7', 'Utf12', 'Utf16', 'Utf4'],
        global_variables=['Utx171', 'Utx112', 'Utx104', 'Utv7', 'UtD38']
    )
    
    # 条件を追加
    condition1 = Condition(
        line=10,
        type=ConditionType.SIMPLE_IF,
        expression="UtD31(Utx171) != 0"
    )
    
    condition2 = Condition(
        line=20,
        type=ConditionType.SIMPLE_IF,
        expression="Utf7() == 0"
    )
    
    condition3 = Condition(
        line=30,
        type=ConditionType.SIMPLE_IF,
        expression="UtD31(Utx171) < Utv7"
    )
    
    parsed_data.conditions = [condition1, condition2, condition3]
    
    # TestFunctionGeneratorでテスト関数を生成
    generator = TestFunctionGenerator()
    
    # テストケース1: UtD31(Utx171) != 0 (真)
    test_case1 = TestCase(
        no=1,
        truth="T",
        condition="if (UtD31(Utx171) != 0)",
        expected="条件が真の処理を実行"
    )
    
    print("テストケース1: UtD31(Utx171) != 0 (真)")
    print("-" * 70)
    test_func1 = generator.generate_test_function(test_case1, parsed_data)
    print(test_func1)
    print()
    print()
    
    # テストケース2: Utf7() == 0 (真)
    test_case2 = TestCase(
        no=2,
        truth="T",
        condition="if (Utf7() == 0)",
        expected="条件が真の処理を実行"
    )
    
    print("テストケース2: Utf7() == 0 (真)")
    print("-" * 70)
    test_func2 = generator.generate_test_function(test_case2, parsed_data)
    print(test_func2)
    print()
    print()
    
    # テストケース3: UtD31(Utx171) < Utv7 (真)
    test_case3 = TestCase(
        no=3,
        truth="T",
        condition="if (UtD31(Utx171) < Utv7)",
        expected="条件が真の処理を実行"
    )
    
    print("テストケース3: UtD31(Utx171) < Utv7 (真)")
    print("-" * 70)
    test_func3 = generator.generate_test_function(test_case3, parsed_data)
    print(test_func3)
    print()

if __name__ == "__main__":
    test_real_world_scenario()
    print()
    print("=" * 70)
    print("✓ テストコード生成が完了しました")
    print("=" * 70)
