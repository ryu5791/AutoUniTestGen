#!/usr/bin/env python3
"""
構造体メンバーアクセスのテスト
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.test_generator.boundary_value_calculator import BoundaryValueCalculator

def test_struct_member_access():
    """構造体メンバーアクセスのテスト"""
    print("=" * 70)
    print("構造体メンバーアクセステスト")
    print("=" * 70)
    print()
    
    calc = BoundaryValueCalculator()
    
    # テストケース1: 構造体メンバー同士の比較
    print("テスト1: Utx112.Utm10 != Utx104.Utm10")
    expr1 = "Utx112.Utm10 != Utx104.Utm10"
    result1 = calc.parse_comparison(expr1)
    print(f"  入力: {expr1}")
    print(f"  結果: {result1}")
    
    test_val_T = calc.generate_test_value(expr1, 'T')
    test_val_F = calc.generate_test_value(expr1, 'F')
    print(f"  真の場合の初期化コード: {test_val_T}")
    print(f"  偽の場合の初期化コード: {test_val_F}")
    print()
    
    # テストケース2: 構造体メンバーと数値の比較
    print("テスト2: Utx104.Utm11.Utm12 == 5")
    expr2 = "Utx104.Utm11.Utm12 == 5"
    result2 = calc.parse_comparison(expr2)
    print(f"  入力: {expr2}")
    print(f"  結果: {result2}")
    
    test_val_T = calc.generate_test_value(expr2, 'T')
    test_val_F = calc.generate_test_value(expr2, 'F')
    print(f"  真の場合の初期化コード: {test_val_T}")
    print(f"  偽の場合の初期化コード: {test_val_F}")
    print()
    
    # テストケース3: 配列要素の構造体メンバー
    print("テスト3: array[0].member > 10")
    expr3 = "array[0].member > 10"
    result3 = calc.parse_comparison(expr3)
    print(f"  入力: {expr3}")
    print(f"  結果: {result3}")
    
    test_val_T = calc.generate_test_value(expr3, 'T')
    test_val_F = calc.generate_test_value(expr3, 'F')
    print(f"  真の場合の初期化コード: {test_val_T}")
    print(f"  偽の場合の初期化コード: {test_val_F}")
    print()
    
    # テストケース4: ネストした構造体
    print("テスト4: Utx172.Utm11.Utm15 != 0")
    expr4 = "Utx172.Utm11.Utm15 != 0"
    result4 = calc.parse_comparison(expr4)
    print(f"  入力: {expr4}")
    print(f"  結果: {result4}")
    
    test_val_T = calc.generate_test_value(expr4, 'T')
    test_val_F = calc.generate_test_value(expr4, 'F')
    print(f"  真の場合の初期化コード: {test_val_T}")
    print(f"  偽の場合の初期化コード: {test_val_F}")
    print()
    
    # テストケース5: 複数レベルのネスト
    print("テスト5: Utx20.Utm1.Utm16 == Utm57")
    expr5 = "Utx20.Utm1.Utm16 == Utm57"
    result5 = calc.parse_comparison(expr5)
    print(f"  入力: {expr5}")
    print(f"  結果: {result5}")
    
    test_val_T = calc.generate_test_value(expr5, 'T')
    test_val_F = calc.generate_test_value(expr5, 'F')
    print(f"  真の場合の初期化コード: {test_val_T}")
    print(f"  偽の場合の初期化コード: {test_val_F}")
    print()

if __name__ == "__main__":
    test_struct_member_access()
    print()
    print("=" * 70)
    print("✓ すべてのテストが完了しました")
    print("=" * 70)
