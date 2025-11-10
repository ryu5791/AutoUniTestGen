"""
関数呼び出し検出の動作確認テスト
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.test_generator.boundary_value_calculator import BoundaryValueCalculator
from src.test_generator.test_function_generator import TestFunctionGenerator
from src.data_structures import ParsedData, TestCase, Condition, ConditionType, FunctionInfo

def test_function_call_detection():
    """関数呼び出しの検出テスト"""
    print("=" * 80)
    print("関数呼び出し検出のテスト")
    print("=" * 80)
    print()
    
    calc = BoundaryValueCalculator()
    
    # テストケース1: Utf12() != 0
    print("【ケース1】関数呼び出しと数値の比較")
    print("-" * 80)
    expr1 = "Utf12() != 0"
    print(f"条件式: if ({expr1})")
    print()
    
    # parse_comparisonの結果を確認
    parsed = calc.parse_comparison(expr1)
    print(f"解析結果:")
    print(f"  左辺: {parsed['left']}")
    print(f"  演算子: {parsed['operator']}")
    print(f"  右辺: {parsed['right']}")
    print(f"  右辺タイプ: {parsed['right_type']}")
    print()
    
    # 関数呼び出しの検出
    is_func = calc._is_function_call(parsed['left'])
    print(f"左辺が関数呼び出しか: {is_func}")
    assert is_func, "Utf12()は関数呼び出しとして検出されるべき"
    print("✓ 関数呼び出しとして正しく検出")
    print()
    
    # 初期化コードの生成
    print("生成される初期化コード:")
    values = calc.generate_comparison_values(expr1, 'T')
    for code in values:
        print(f"  {code}")
    assert len(values) == 1
    assert "TODO" in values[0]
    assert "Utf12()" in values[0]
    print("✓ TODOコメントが適切に生成される")
    print()
    
    # テストケース2: UtD31(Utx171) < Utv7
    print("【ケース2】マクロ展開された関数呼び出し")
    print("-" * 80)
    expr2 = "Utf12() < Utv7"  # UtD31(Utx171) が Utf12() に展開されたケース
    print(f"条件式: if ({expr2})")
    print("（元の式: if (UtD31(Utx171) < Utv7)）")
    print()
    
    parsed2 = calc.parse_comparison(expr2)
    print(f"解析結果:")
    print(f"  左辺: {parsed2['left']}")
    print(f"  演算子: {parsed2['operator']}")
    print(f"  右辺: {parsed2['right']}")
    print()
    
    # 左辺が関数呼び出し
    is_func_left = calc._is_function_call(parsed2['left'])
    is_func_right = calc._is_function_call(parsed2['right'])
    print(f"左辺が関数呼び出しか: {is_func_left}")
    print(f"右辺が関数呼び出しか: {is_func_right}")
    print()
    
    print("生成される初期化コード:")
    values2 = calc.generate_comparison_values(expr2, 'T')
    for code in values2:
        print(f"  {code}")
    assert len(values2) == 1
    assert "TODO" in values2[0]
    print("✓ 関数呼び出しが含まれる場合、TODOコメントが生成される")
    print()
    
    # テストケース3: 通常の変数（関数呼び出しでない）
    print("【ケース3】通常の変数（比較）")
    print("-" * 80)
    expr3 = "Utv7 != 0"
    print(f"条件式: if ({expr3})")
    print()
    
    parsed3 = calc.parse_comparison(expr3)
    is_func3 = calc._is_function_call(parsed3['left'])
    print(f"左辺が関数呼び出しか: {is_func3}")
    assert not is_func3, "Utv7は通常の変数として扱われるべき"
    print("✓ 通常の変数として正しく認識")
    print()
    
    print("生成される初期化コード:")
    values3 = calc.generate_comparison_values(expr3, 'T')
    for code in values3:
        print(f"  {code}")
    assert len(values3) == 1
    assert "TODO" not in values3[0]
    assert "Utv7 = 1" in values3[0]
    print("✓ 通常の初期化コードが生成される")
    print()
    
    print("=" * 80)
    print("✅ すべてのテストが成功")
    print("=" * 80)

def test_function_call_in_test_generation():
    """テスト関数生成での動作確認"""
    print("\n" + "=" * 80)
    print("テスト関数生成での動作確認")
    print("=" * 80)
    print()
    
    # テストデータの準備
    parsed_data = ParsedData(
        file_name="sample.c",
        function_name="Utf1",
        external_functions=['Utf12'],
        global_variables=['Utv7']
    )
    
    parsed_data.function_info = FunctionInfo(
        name="Utf1",
        return_type="void",
        parameters=[]
    )
    
    # 条件を追加（関数呼び出しを含む）
    condition = Condition(
        line=1925,
        type=ConditionType.SIMPLE_IF,
        expression="Utf12() != 0"
    )
    parsed_data.conditions = [condition]
    
    # テストケース
    test_case = TestCase(
        no=2,
        truth='T',
        condition="if (Utf12() != 0)",
        expected="真の場合の処理を実行"
    )
    
    # テスト関数生成
    generator = TestFunctionGenerator()
    test_function = generator.generate_test_function(test_case, parsed_data)
    
    print("【生成されたテスト関数】")
    print("-" * 80)
    
    # 初期化部分を抽出
    lines = test_function.split('\n')
    init_section = []
    capture = False
    for line in lines:
        if '// 変数を初期化' in line:
            capture = True
        if capture:
            init_section.append(line)
            if line.strip() == '' or '// モック' in line:
                break
    
    for line in init_section:
        print(line)
    
    print("-" * 80)
    print()
    
    # 検証
    init_text = '\n'.join(init_section)
    assert "TODO" in init_text, "TODOコメントが含まれるべき"
    assert "Utf12()" in init_text, "関数名が含まれるべき"
    assert "Utf12() = " not in init_text, "関数呼び出しへの代入は含まれないべき"
    
    print("✓ 関数呼び出しへの代入が防がれている")
    print("✓ 適切なTODOコメントが生成されている")
    print()
    
    print("=" * 80)
    print("✅ テスト関数生成での動作確認: 成功")
    print("=" * 80)

def test_before_after_comparison():
    """Before/After比較"""
    print("\n" + "=" * 80)
    print("Before/After 比較")
    print("=" * 80)
    print()
    
    calc = BoundaryValueCalculator()
    
    expr = "Utf12() != 0"
    
    print("【問題のあったケース】")
    print("-" * 80)
    print(f"条件式: if ({expr})")
    print()
    
    print("■ Before (v2.3.2修正前):")
    print("    // 変数を初期化")
    print("    (Utf12() = 1;  // 左辺")
    print("    0) = 0;  // 右辺（異なる値）")
    print("    ↑ コンパイルエラー:")
    print("      - 関数呼び出しに代入しようとしている")
    print("      - 括弧の処理が不適切")
    print()
    
    print("■ After (v2.3.2修正後):")
    values = calc.generate_comparison_values(expr, 'T')
    for code in values:
        print(f"    {code}")
    print("    ↑ 改善:")
    print("      - 関数呼び出しを検出")
    print("      - 代入を試みず、TODOコメントを生成")
    print("      - コンパイルエラーを回避")
    print()
    
    print("=" * 80)
    print("✅ 修正により、コンパイルエラーが解消されました")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_function_call_detection()
        test_function_call_in_test_generation()
        test_before_after_comparison()
        
        print("\n" + "=" * 80)
        print("🎉 関数呼び出し検出: すべてのテストが成功しました！")
        print("=" * 80)
        print()
        print("修正内容:")
        print("  1. 関数呼び出しの検出ロジック追加 (_is_function_call)")
        print("  2. generate_test_value での関数呼び出しチェック")
        print("  3. generate_comparison_values での関数呼び出しチェック")
        print("  4. 関数呼び出しの場合はTODOコメントを生成")
        print()
        print("効果:")
        print("  ✓ コンパイルエラーの回避")
        print("  ✓ ユーザーへの明確なガイダンス")
        print("  ✓ 関数呼び出しと変数の適切な区別")
        
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
