"""
main関数生成のテスト
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.data_structures import ParsedData, TruthTableData, TestCase, FunctionInfo
from src.test_generator.unity_test_generator import UnityTestGenerator

def test_main_function_generation():
    """main関数が正しく生成されることを確認"""
    print("=" * 70)
    print("TEST: main関数の生成")
    print("=" * 70)
    
    # テストデータ
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="Utf1",
        external_functions=['Utf10', 'Utf11'],
        global_variables=['v1']
    )
    
    parsed_data.function_info = FunctionInfo(
        name="Utf1",
        return_type="void",
        parameters=[]
    )
    
    # 複数の条件を持つテストケース
    truth_table = TruthTableData(
        function_name="Utf1",
        test_cases=[
            TestCase(no=1, truth="T", condition="if (v1 > 10)", expected="真"),
            TestCase(no=2, truth="F", condition="if (v1 > 10)", expected="偽"),
            TestCase(no=3, truth="T", condition="if (v2 < 5)", expected="真"),
            TestCase(no=4, truth="F", condition="if (v2 < 5)", expected="偽"),
            TestCase(no=5, truth="TF", condition="if ((a || b))", expected="左真"),
            TestCase(no=6, truth="FT", condition="if ((a || b))", expected="右真"),
            TestCase(no=7, truth="FF", condition="if ((a || b))", expected="両偽"),
        ],
        total_tests=7
    )
    
    # テストコード生成
    generator = UnityTestGenerator(include_target_function=False)
    test_code = generator.generate(truth_table, parsed_data)
    
    # 結果確認
    code = test_code.to_string()
    
    # main関数セクションを抽出
    lines = code.split('\n')
    main_section = []
    in_main_section = False
    for i, line in enumerate(lines):
        if "===== main関数 =====" in line:
            in_main_section = True
        if in_main_section:
            main_section.append((i, line))
            if line.strip() == "}":
                break
    
    print("\n生成されたmain関数:")
    print("-" * 70)
    for line_no, line in main_section:
        print(f"{line_no:4d}: {line}")
    print("-" * 70)
    print()
    
    # 検証
    print("検証:")
    print("-" * 70)
    
    # main関数が存在することを確認
    assert "int main(void) {" in code, "main関数が生成されていない"
    print("✓ main関数が生成されている")
    
    # UNITY_BEGIN()が含まれることを確認
    assert "UNITY_BEGIN();" in code, "UNITY_BEGIN()が含まれていない"
    print("✓ UNITY_BEGIN()が含まれている")
    
    # UNITY_END()が含まれることを確認
    assert "return UNITY_END();" in code, "UNITY_END()が含まれていない"
    print("✓ return UNITY_END()が含まれている")
    
    # ヘッダー情報が含まれることを確認
    assert "Utf1 Function MC/DC 100%" in code, "関数名がヘッダーに含まれていない"
    print("✓ 関数名がヘッダーに含まれている")
    
    assert "Total Test Cases: 7" in code, "テストケース数が含まれていない"
    print("✓ テストケース数が含まれている")
    
    # RUN_TESTが含まれることを確認
    assert "RUN_TEST(test_01" in code, "RUN_TEST(test_01)が含まれていない"
    print("✓ RUN_TEST(test_01)が含まれている")
    
    assert "RUN_TEST(test_07" in code, "RUN_TEST(test_07)が含まれていない"
    print("✓ RUN_TEST(test_07)が含まれている")
    
    # グループヘッダーが含まれることを確認
    has_group_header = False
    for line_no, line in main_section:
        if "No." in line and "---" in line:
            has_group_header = True
            print(f"✓ グループヘッダーが含まれている: {line.strip()}")
            break
    
    assert has_group_header, "グループヘッダーが含まれていない"
    
    print("-" * 70)
    print("✅ main関数が正しく生成されています")
    print()
    
    # 期待される構造を表示
    print("期待される構造:")
    print("-" * 70)
    print("int main(void) {")
    print("    UNITY_BEGIN();")
    print("    ")
    print("    printf(\"==============================================\\n\");")
    print("    printf(\"Utf1 Function MC/DC 100%% Coverage Test Suite\\n\");")
    print("    printf(\"==============================================\\n\");")
    print("    printf(\"Target: MC/DC (Modified Condition/Decision Coverage) 100%%\\n\");")
    print("    printf(\"Total Test Cases: 7\\n\");")
    print("    printf(\"==============================================\\n\\n\");")
    print("    ")
    print("    printf(\"--- Condition Tests (No.1-2) ---\\n\");")
    print("    RUN_TEST(test_01_condition_T);")
    print("    RUN_TEST(test_02_condition_F);")
    print("    ")
    print("    printf(\"--- Condition Tests (No.3-4) ---\\n\");")
    print("    RUN_TEST(test_03_condition_T);")
    print("    RUN_TEST(test_04_condition_F);")
    print("    ")
    print("    return UNITY_END();")
    print("}")
    print("-" * 70)
    print()

def test_main_function_with_many_tests():
    """多数のテストケースでmain関数が正しく生成されることを確認"""
    print("=" * 70)
    print("TEST: 多数のテストケースでのmain関数生成")
    print("=" * 70)
    
    # テストデータ
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="state_loop",
        external_functions=['func1'],
        global_variables=['v1']
    )
    
    parsed_data.function_info = FunctionInfo(
        name="state_loop",
        return_type="void",
        parameters=[]
    )
    
    # 42個のテストケースを生成
    test_cases = []
    for i in range(1, 43):
        test_cases.append(
            TestCase(no=i, truth="T" if i % 2 == 1 else "F", 
                    condition=f"if (condition_{(i-1)//2 + 1})", 
                    expected="真" if i % 2 == 1 else "偽")
        )
    
    truth_table = TruthTableData(
        function_name="state_loop",
        test_cases=test_cases,
        total_tests=42
    )
    
    # テストコード生成
    generator = UnityTestGenerator(include_target_function=False)
    test_code = generator.generate(truth_table, parsed_data)
    
    # 結果確認
    code = test_code.to_string()
    
    # 検証
    print("\n検証:")
    print("-" * 70)
    
    # 全てのテストケースのRUN_TESTが含まれることを確認
    for i in range(1, 43):
        assert f"RUN_TEST(test_{i:02d}" in code, f"RUN_TEST(test_{i:02d})が含まれていない"
    print(f"✓ 全42個のRUN_TESTが含まれている")
    
    # テストケース数が正しいことを確認
    assert "Total Test Cases: 42" in code, "テストケース数が正しくない"
    print("✓ テストケース数が正しい（42個）")
    
    print("-" * 70)
    print("✅ 多数のテストケースでもmain関数が正しく生成されています")
    print()

if __name__ == "__main__":
    print("=" * 70)
    print("main関数生成テスト")
    print("=" * 70)
    print()
    
    try:
        test_main_function_generation()
        test_main_function_with_many_tests()
        
        print("=" * 70)
        print("✅ すべてのテストが成功しました！")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
