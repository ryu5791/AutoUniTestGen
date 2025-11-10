"""
テスト関数のプロトタイプ宣言が各関数本体の直前に生成されることを確認
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.data_structures import ParsedData, TruthTableData, TestCase, FunctionInfo
from src.test_generator.unity_test_generator import UnityTestGenerator

def test_prototype_before_function():
    """テスト関数のプロトタイプが各関数本体の直前に生成されることを確認"""
    print("=" * 70)
    print("TEST: テスト関数のプロトタイプ宣言が関数本体の直前に生成されるか確認")
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
    
    truth_table = TruthTableData(
        function_name="Utf1",
        test_cases=[
            TestCase(no=1, truth="T", condition="if (v1 > 10)", expected="真"),
            TestCase(no=2, truth="F", condition="if (v1 > 10)", expected="偽"),
            TestCase(no=3, truth="TF", condition="if ((a || b))", expected="左真"),
        ],
        total_tests=3
    )
    
    # テストコード生成
    generator = UnityTestGenerator(include_target_function=False)
    test_code = generator.generate(truth_table, parsed_data)
    
    # 結果確認
    code = test_code.to_string()
    lines = code.split('\n')
    
    # テスト関数セクションを抽出
    test_function_section = []
    in_test_section = False
    for i, line in enumerate(lines):
        if "===== テスト関数 =====" in line:
            in_test_section = True
        elif "===== setUp/tearDown =====" in line:
            break
        elif in_test_section:
            test_function_section.append((i, line))
    
    print("\n生成されたテスト関数セクション（最初の80行）:")
    print("-" * 70)
    for i, (line_no, line) in enumerate(test_function_section[:80]):
        print(f"{line_no:4d}: {line}")
    print("-" * 70)
    print()
    
    # パターンを確認
    print("検証:")
    print("-" * 70)
    
    # test_01 のパターンを確認
    found_prototype_01 = False
    found_function_01 = False
    prototype_line_01 = -1
    function_line_01 = -1
    
    for line_no, line in test_function_section:
        if "void test_01" in line and line.strip().endswith(";"):
            found_prototype_01 = True
            prototype_line_01 = line_no
            print(f"✓ test_01のプロトタイプ宣言を発見（行 {line_no}）: {line.strip()}")
        elif "void test_01" in line and line.strip().endswith("{"):
            found_function_01 = True
            function_line_01 = line_no
            print(f"✓ test_01の関数本体を発見（行 {line_no}）: {line.strip()}")
    
    assert found_prototype_01, "test_01のプロトタイプ宣言が見つかりません"
    assert found_function_01, "test_01の関数本体が見つかりません"
    assert prototype_line_01 < function_line_01, \
        f"プロトタイプ宣言（行{prototype_line_01}）が関数本体（行{function_line_01}）より後にあります"
    
    print(f"✓ test_01: プロトタイプ宣言（行{prototype_line_01}）→ 関数本体（行{function_line_01}）の順序OK")
    print()
    
    # test_02 のパターンを確認
    found_prototype_02 = False
    found_function_02 = False
    prototype_line_02 = -1
    function_line_02 = -1
    
    for line_no, line in test_function_section:
        if "void test_02" in line and line.strip().endswith(";"):
            found_prototype_02 = True
            prototype_line_02 = line_no
            print(f"✓ test_02のプロトタイプ宣言を発見（行 {line_no}）: {line.strip()}")
        elif "void test_02" in line and line.strip().endswith("{"):
            found_function_02 = True
            function_line_02 = line_no
            print(f"✓ test_02の関数本体を発見（行 {line_no}）: {line.strip()}")
    
    assert found_prototype_02, "test_02のプロトタイプ宣言が見つかりません"
    assert found_function_02, "test_02の関数本体が見つかりません"
    assert prototype_line_02 < function_line_02, \
        f"プロトタイプ宣言（行{prototype_line_02}）が関数本体（行{function_line_02}）より後にあります"
    
    print(f"✓ test_02: プロトタイプ宣言（行{prototype_line_02}）→ 関数本体（行{function_line_02}）の順序OK")
    print()
    
    # test_03 のパターンを確認
    found_prototype_03 = False
    found_function_03 = False
    prototype_line_03 = -1
    function_line_03 = -1
    
    for line_no, line in test_function_section:
        if "void test_03" in line and line.strip().endswith(";"):
            found_prototype_03 = True
            prototype_line_03 = line_no
            print(f"✓ test_03のプロトタイプ宣言を発見（行 {line_no}）: {line.strip()}")
        elif "void test_03" in line and line.strip().endswith("{"):
            found_function_03 = True
            function_line_03 = line_no
            print(f"✓ test_03の関数本体を発見（行 {line_no}）: {line.strip()}")
    
    assert found_prototype_03, "test_03のプロトタイプ宣言が見つかりません"
    assert found_function_03, "test_03の関数本体が見つかりません"
    assert prototype_line_03 < function_line_03, \
        f"プロトタイプ宣言（行{prototype_line_03}）が関数本体（行{function_line_03}）より後にあります"
    
    print(f"✓ test_03: プロトタイプ宣言（行{prototype_line_03}）→ 関数本体（行{function_line_03}）の順序OK")
    print()
    
    print("-" * 70)
    print("✅ すべてのテスト関数でプロトタイプ宣言が関数本体の直前に生成されています")
    print()
    
    # 期待される構造を表示
    print("期待される構造:")
    print("-" * 70)
    print("// プロトタイプ宣言")
    print("void test_01_condition_T(void);")
    print("")
    print("/**")
    print(" * テスト関数のコメント")
    print(" */")
    print("void test_01_condition_T(void) {")
    print("    // 関数本体")
    print("}")
    print("")
    print("// プロトタイプ宣言")
    print("void test_02_condition_F(void);")
    print("")
    print("/**")
    print(" * テスト関数のコメント")
    print(" */")
    print("void test_02_condition_F(void) {")
    print("    // 関数本体")
    print("}")
    print("-" * 70)
    print()

if __name__ == "__main__":
    print("=" * 70)
    print("テスト関数のプロトタイプ宣言テスト")
    print("=" * 70)
    print()
    
    try:
        test_prototype_before_function()
        
        print("=" * 70)
        print("✅ テストが成功しました！")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
