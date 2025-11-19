"""
冒頭のプロトタイプセクションにテスト関数のプロトタイプが含まれていないことを確認
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.data_structures import ParsedData, TruthTableData, TestCase, FunctionInfo
from src.test_generator.unity_test_generator import UnityTestGenerator

def test_no_duplicate_prototypes():
    """冒頭のプロトタイプセクションにテスト関数のプロトタイプが重複していないことを確認"""
    print("=" * 70)
    print("TEST: 冒頭のプロトタイプセクションの確認")
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
        ],
        total_tests=2
    )
    
    # テストコード生成
    generator = UnityTestGenerator(include_target_function=False)
    test_code = generator.generate(truth_table, parsed_data)
    
    # 結果確認
    code = test_code.to_string()
    lines = code.split('\n')
    
    # プロトタイプセクションを抽出
    prototype_section = []
    in_prototype_section = False
    for i, line in enumerate(lines):
        if "===== プロトタイプ宣言 =====" in line:
            in_prototype_section = True
        elif "===== モック・スタブ用グローバル変数 =====" in line:
            break
        elif in_prototype_section:
            prototype_section.append((i, line))
    
    print("\n冒頭のプロトタイプセクション:")
    print("-" * 70)
    for line_no, line in prototype_section:
        print(f"{line_no:4d}: {line}")
    print("-" * 70)
    print()
    
    # 検証
    print("検証:")
    print("-" * 70)
    
    # テスト関数のプロトタイプが含まれていないことを確認
    has_test_function_prototype = False
    for line_no, line in prototype_section:
        if "void test_" in line and line.strip().endswith(";"):
            has_test_function_prototype = True
            print(f"❌ テスト関数のプロトタイプが見つかりました（行 {line_no}）: {line.strip()}")
    
    if not has_test_function_prototype:
        print("✓ 冒頭のプロトタイプセクションにテスト関数のプロトタイプは含まれていません")
    
    # モック関数のプロトタイプが含まれていることを確認
    has_mock_prototype = False
    for line_no, line in prototype_section:
        if "mock_" in line and line.strip().endswith(";"):
            has_mock_prototype = True
            print(f"✓ モック関数のプロトタイプが見つかりました（行 {line_no}）: {line.strip()}")
    
    assert has_mock_prototype, "モック関数のプロトタイプが見つかりません"
    
    # ヘルパー関数のプロトタイプが含まれていることを確認
    has_helper_prototype = False
    for line_no, line in prototype_section:
        if ("setUp" in line or "tearDown" in line) and line.strip().endswith(";"):
            has_helper_prototype = True
            print(f"✓ ヘルパー関数のプロトタイプが見つかりました（行 {line_no}）: {line.strip()}")
    
    assert has_helper_prototype, "ヘルパー関数のプロトタイプが見つかりません"
    
    # テスト関数のプロトタイプが重複していないことを確認
    assert not has_test_function_prototype, \
        "テスト関数のプロトタイプが冒頭のプロトタイプセクションに含まれています（重複）"
    
    print("-" * 70)
    print("✅ 冒頭のプロトタイプセクションは正しい構成です")
    print()
    
    # 期待される構造を表示
    print("期待される冒頭のプロトタイプセクション:")
    print("-" * 70)
    print("// ===== プロトタイプ宣言 =====")
    print("")
    print("// モック・スタブ関数")
    print("static int mock_Utf10(void);")
    print("static int mock_Utf11(void);")
    print("static void reset_all_mocks(void);")
    print("")
    print("// テスト関数のプロトタイプは各関数本体の直前に配置されています")
    print("")
    print("// ヘルパー関数")
    print("static void setUp(void);")
    print("static void tearDown(void);")
    print("-" * 70)
    print()

if __name__ == "__main__":
    print("=" * 70)
    print("プロトタイプセクション構成テスト")
    print("=" * 70)
    print()
    
    try:
        test_no_duplicate_prototypes()
        
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
