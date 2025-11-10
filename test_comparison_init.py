"""
比較式の初期化コード生成テスト（構造体メンバ対応）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.test_generator.boundary_value_calculator import BoundaryValueCalculator

def test_parse_comparison():
    """parse_comparisonメソッドのテスト"""
    print("=" * 70)
    print("TEST: parse_comparison - 構造体メンバアクセス対応")
    print("=" * 70)
    
    calc = BoundaryValueCalculator()
    
    # テストケース1: 構造体メンバの不等号
    expr1 = "Utx112.Utm10 != Utx104.Utm10"
    result1 = calc.parse_comparison(expr1)
    print(f"\n式: {expr1}")
    print(f"結果: {result1}")
    assert result1['left'] == 'Utx112.Utm10', f"左辺が正しく抽出されていない: {result1['left']}"
    assert result1['operator'] == '!=', f"演算子が正しく抽出されていない: {result1['operator']}"
    assert result1['right'] == 'Utx104.Utm10', f"右辺が正しく抽出されていない: {result1['right']}"
    assert result1['right_type'] == 'identifier', f"右辺の型が正しくない: {result1['right_type']}"
    print("✓ テスト1成功")
    
    # テストケース2: 通常の変数の等号
    expr2 = "var1 == var2"
    result2 = calc.parse_comparison(expr2)
    print(f"\n式: {expr2}")
    print(f"結果: {result2}")
    assert result2['left'] == 'var1'
    assert result2['operator'] == '=='
    assert result2['right'] == 'var2'
    print("✓ テスト2成功")
    
    # テストケース3: 数値との比較
    expr3 = "counter > 30"
    result3 = calc.parse_comparison(expr3)
    print(f"\n式: {expr3}")
    print(f"結果: {result3}")
    assert result3['left'] == 'counter'
    assert result3['operator'] == '>'
    assert result3['right'] == '30'
    assert result3['right_type'] == 'number'
    print("✓ テスト3成功")
    
    # テストケース4: 複数レベルの構造体メンバ
    expr4 = "obj.sub.value >= 100"
    result4 = calc.parse_comparison(expr4)
    print(f"\n式: {expr4}")
    print(f"結果: {result4}")
    assert result4['left'] == 'obj.sub.value'
    assert result4['operator'] == '>='
    print("✓ テスト4成功")
    
    print("\n" + "=" * 70)
    print("✅ parse_comparisonテスト: すべて成功")
    print("=" * 70)

def test_extract_variables():
    """extract_variablesメソッドのテスト"""
    print("\n" + "=" * 70)
    print("TEST: extract_variables - 構造体メンバアクセス対応")
    print("=" * 70)
    
    calc = BoundaryValueCalculator()
    
    # テストケース1: 構造体メンバ
    expr1 = "Utx112.Utm10 != Utx104.Utm10"
    vars1 = calc.extract_variables(expr1)
    print(f"\n式: {expr1}")
    print(f"抽出された変数: {vars1}")
    assert 'Utx112.Utm10' in vars1, "Utx112.Utm10が抽出されていない"
    assert 'Utx104.Utm10' in vars1, "Utx104.Utm10が抽出されていない"
    print("✓ テスト1成功")
    
    # テストケース2: 通常の変数
    expr2 = "counter > 30"
    vars2 = calc.extract_variables(expr2)
    print(f"\n式: {expr2}")
    print(f"抽出された変数: {vars2}")
    assert 'counter' in vars2
    print("✓ テスト2成功")
    
    # テストケース3: 複数レベルの構造体
    expr3 = "obj.sub.value == 10"
    vars3 = calc.extract_variables(expr3)
    print(f"\n式: {expr3}")
    print(f"抽出された変数: {vars3}")
    assert 'obj.sub.value' in vars3
    print("✓ テスト3成功")
    
    print("\n" + "=" * 70)
    print("✅ extract_variablesテスト: すべて成功")
    print("=" * 70)

def test_generate_comparison_values():
    """generate_comparison_valuesメソッドのテスト"""
    print("\n" + "=" * 70)
    print("TEST: generate_comparison_values - 両辺の値設定")
    print("=" * 70)
    
    calc = BoundaryValueCalculator()
    
    # テストケース1: 不等号（真）
    print("\n--- テスト1: 不等号（真の場合）---")
    expr1 = "Utx112.Utm10 != Utx104.Utm10"
    values1 = calc.generate_comparison_values(expr1, 'T')
    print(f"式: {expr1}")
    print(f"真偽: T")
    print("生成されたコード:")
    for code in values1:
        print(f"  {code}")
    assert len(values1) == 2, "2つの初期化コードが生成されるべき"
    assert "Utx112.Utm10 = 1" in values1[0], "左辺が1に設定されるべき"
    assert "Utx104.Utm10 = 0" in values1[1], "右辺が0（異なる値）に設定されるべき"
    print("✓ テスト1成功")
    
    # テストケース2: 不等号（偽）
    print("\n--- テスト2: 不等号（偽の場合）---")
    values2 = calc.generate_comparison_values(expr1, 'F')
    print(f"式: {expr1}")
    print(f"真偽: F")
    print("生成されたコード:")
    for code in values2:
        print(f"  {code}")
    assert len(values2) == 2
    assert "Utx112.Utm10 = 0" in values2[0]
    assert "Utx104.Utm10 = 0" in values2[1], "右辺も0（同じ値）に設定されるべき"
    print("✓ テスト2成功")
    
    # テストケース3: 等号（真）
    print("\n--- テスト3: 等号（真の場合）---")
    expr3 = "var1 == var2"
    values3 = calc.generate_comparison_values(expr3, 'T')
    print(f"式: {expr3}")
    print(f"真偽: T")
    print("生成されたコード:")
    for code in values3:
        print(f"  {code}")
    assert len(values3) == 2
    assert "var1 = 1" in values3[0]
    assert "var2 = 1" in values3[1], "等号が真なので同じ値"
    print("✓ テスト3成功")
    
    # テストケース4: 等号（偽）
    print("\n--- テスト4: 等号（偽の場合）---")
    values4 = calc.generate_comparison_values(expr3, 'F')
    print(f"式: {expr3}")
    print(f"真偽: F")
    print("生成されたコード:")
    for code in values4:
        print(f"  {code}")
    assert len(values4) == 2
    assert "var1 = 1" in values4[0]
    assert "var2 = 0" in values4[1], "等号が偽なので異なる値"
    print("✓ テスト4成功")
    
    # テストケース5: 大なり（真）
    print("\n--- テスト5: 大なり（真の場合）---")
    expr5 = "counter > threshold"
    values5 = calc.generate_comparison_values(expr5, 'T')
    print(f"式: {expr5}")
    print(f"真偽: T")
    print("生成されたコード:")
    for code in values5:
        print(f"  {code}")
    assert len(values5) == 2
    assert "counter = 2" in values5[0]
    assert "threshold = 1" in values5[1], "counter > thresholdが真"
    print("✓ テスト5成功")
    
    # テストケース6: 小なり（真）
    print("\n--- テスト6: 小なり（真の場合）---")
    expr6 = "value < limit"
    values6 = calc.generate_comparison_values(expr6, 'T')
    print(f"式: {expr6}")
    print(f"真偽: T")
    print("生成されたコード:")
    for code in values6:
        print(f"  {code}")
    assert len(values6) == 2
    assert "value = 1" in values6[0]
    assert "limit = 2" in values6[1], "value < limitが真"
    print("✓ テスト6成功")
    
    # テストケース7: 数値との比較（片方のみ設定）
    print("\n--- テスト7: 数値との比較 ---")
    expr7 = "counter > 30"
    values7 = calc.generate_comparison_values(expr7, 'T')
    print(f"式: {expr7}")
    print(f"真偽: T")
    print("生成されたコード:")
    for code in values7:
        print(f"  {code}")
    assert len(values7) == 1, "数値との比較は1つの初期化コードのみ"
    assert "counter = 31" in values7[0]
    print("✓ テスト7成功")
    
    # テストケース8: 関数呼び出しとの比較（NEW）
    print("\n--- テスト8: 関数呼び出しとの比較 ---")
    expr8 = "Utf12() != 0"
    values8 = calc.generate_comparison_values(expr8, 'T')
    print(f"式: {expr8}")
    print(f"真偽: T")
    print("生成されたコード:")
    for code in values8:
        print(f"  {code}")
    assert len(values8) == 1, "関数呼び出しはTODOコメントのみ"
    assert "TODO" in values8[0], "TODOコメントが含まれるべき"
    assert "Utf12()" in values8[0], "関数名が含まれるべき"
    print("✓ テスト8成功")
    
    # テストケース9: 関数呼び出し同士の比較（NEW）
    print("\n--- テスト9: 関数呼び出し同士の比較 ---")
    expr9 = "func1() == func2()"
    values9 = calc.generate_comparison_values(expr9, 'T')
    print(f"式: {expr9}")
    print(f"真偽: T")
    print("生成されたコード:")
    for code in values9:
        print(f"  {code}")
    assert len(values9) == 1, "関数呼び出しはTODOコメントのみ"
    assert "TODO" in values9[0], "TODOコメントが含まれるべき"
    print("✓ テスト9成功")
    
    print("\n" + "=" * 70)
    print("✅ generate_comparison_valuesテスト: すべて成功")
    print("=" * 70)

def test_integration():
    """統合テスト: 実際のテスト関数生成での動作確認"""
    print("\n" + "=" * 70)
    print("TEST: 統合テスト - テスト関数生成での動作確認")
    print("=" * 70)
    
    from src.data_structures import ParsedData, TruthTableData, TestCase, Condition, ConditionType, FunctionInfo
    from src.test_generator.test_function_generator import TestFunctionGenerator
    
    # テストデータの準備
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="Utf1",
        external_functions=[],
        global_variables=[]
    )
    
    parsed_data.function_info = FunctionInfo(
        name="Utf1",
        return_type="void",
        parameters=[]
    )
    
    # 条件を追加
    condition = Condition(
        line=10,
        type=ConditionType.SIMPLE_IF,
        expression="Utx112.Utm10 != Utx104.Utm10"
    )
    parsed_data.conditions = [condition]
    
    # テストケース
    test_case = TestCase(
        no=1,
        truth='T',
        condition="if (Utx112.Utm10 != Utx104.Utm10)",
        expected="真"
    )
    
    # テスト関数生成
    generator = TestFunctionGenerator()
    test_function = generator.generate_test_function(test_case, parsed_data)
    
    print("\n生成されたテスト関数:")
    print("-" * 70)
    print(test_function)
    print("-" * 70)
    
    # 検証
    assert "Utx112.Utm10 = 1" in test_function, "Utx112.Utm10の初期化が含まれていない"
    assert "Utx104.Utm10 = 0" in test_function, "Utx104.Utm10の初期化が含まれていない"
    assert "異なる値" in test_function or "左辺" in test_function, "コメントが適切でない"
    
    print("\n✓ 統合テスト成功")
    print("  - 構造体メンバの両辺に適切な値が設定されている")
    print("  - 不等号（!=）の真の場合に、異なる値（1と0）が設定されている")
    
    print("\n" + "=" * 70)
    print("✅ 統合テスト: 成功")
    print("=" * 70)

if __name__ == "__main__":
    print("=" * 70)
    print("比較式初期化コード生成テスト（構造体メンバ対応 v2.3.2）")
    print("=" * 70)
    print()
    
    try:
        test_parse_comparison()
        test_extract_variables()
        test_generate_comparison_values()
        test_integration()
        
        print("\n" + "=" * 70)
        print("🎉 すべてのテストが成功しました！")
        print("=" * 70)
        print("\n改善内容:")
        print("  ✓ 構造体メンバアクセス（A.B.C）の正しい抽出")
        print("  ✓ 比較式の左辺・演算子・右辺の個別認識")
        print("  ✓ 識別子同士の比較での両辺の値設定")
        print("  ✓ 各演算子に応じた適切な値の生成")
        print("  ✓ TODOコメントの大幅削減")
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
