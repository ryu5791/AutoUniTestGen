"""
プロトタイプ宣言生成の改善をテスト
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.data_structures import ParsedData, TruthTableData, TestCase, FunctionInfo
from src.test_generator.unity_test_generator import UnityTestGenerator

def test_with_complete_data():
    """完全なデータでのテスト"""
    print("=" * 70)
    print("TEST 1: 完全なデータでのプロトタイプ生成")
    print("=" * 70)
    
    # 完全なデータ
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="Utf1",
        external_functions=['Utf10', 'Utf11', 'Utf12'],
        global_variables=['v1', 'v2']
    )
    
    # 関数情報を設定
    parsed_data.function_info = FunctionInfo(
        name="Utf1",
        return_type="int",
        parameters=[
            {'type': 'uint8_t', 'name': 'param1'},
            {'type': 'uint16_t*', 'name': 'param2'}
        ]
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
    
    # テスト対象関数のプロトタイプを確認
    assert "extern int Utf1(uint8_t param1, uint16_t* param2);" in code, \
        "テスト対象関数のプロトタイプが生成されていない"
    
    # テスト関数のプロトタイプを確認
    assert "static void test_01" in code, "テスト関数1のプロトタイプが生成されていない"
    assert "static void test_02" in code, "テスト関数2のプロトタイプが生成されていない"
    assert "static void test_03" in code, "テスト関数3のプロトタイプが生成されていない"
    
    # モック関数のプロトタイプを確認
    assert "static int mock_Utf10(void);" in code, "モック関数のプロトタイプが生成されていない"
    
    print("✅ 完全なデータでのテスト成功")
    print()
    
    # プロトタイプセクションを表示
    lines = code.split('\n')
    in_prototype_section = False
    prototype_lines = []
    for line in lines:
        if "===== プロトタイプ宣言 =====" in line:
            in_prototype_section = True
        elif "===== モック・スタブ用グローバル変数 =====" in line:
            break
        elif in_prototype_section:
            prototype_lines.append(line)
    
    print("生成されたプロトタイプセクション:")
    print('\n'.join(prototype_lines[:50]))  # 最初の50行
    print()

def test_with_incomplete_data():
    """不完全なデータでのテスト"""
    print("=" * 70)
    print("TEST 2: 不完全なデータでのプロトタイプ生成")
    print("=" * 70)
    
    # 不完全なデータ（function_infoなし）
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="Utf1",
        external_functions=['Utf10'],
        global_variables=[]
    )
    # function_infoは設定しない
    
    truth_table = TruthTableData(
        function_name="Utf1",
        test_cases=[
            TestCase(no=1, truth="T", condition="if (v1 > 10)", expected="真"),
        ],
        total_tests=1
    )
    
    # テストコード生成
    generator = UnityTestGenerator(include_target_function=False)
    test_code = generator.generate(truth_table, parsed_data)
    
    # 結果確認
    code = test_code.to_string()
    
    # デフォルトのプロトタイプが生成されているか確認
    assert "extern void Utf1(void);" in code, \
        "デフォルトのプロトタイプが生成されていない"
    
    # 注意メッセージが含まれているか確認
    assert "注意:" in code or "警告:" in code or "手動" in code, \
        "不完全なデータの場合の注意メッセージがない"
    
    print("✅ 不完全なデータでのテスト成功")
    print()
    
    # テスト対象関数のプロトタイプセクションを表示
    lines = code.split('\n')
    for i, line in enumerate(lines):
        if "===== テスト対象関数のプロトタイプ宣言 =====" in line:
            print("生成されたテスト対象関数のプロトタイプセクション:")
            for j in range(i, min(i+10, len(lines))):
                print(lines[j])
            break
    print()

def test_with_no_data():
    """データがない場合のテスト"""
    print("=" * 70)
    print("TEST 3: データがない場合のプロトタイプ生成")
    print("=" * 70)
    
    # データなし
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="",  # 関数名なし
        external_functions=[],
        global_variables=[]
    )
    
    truth_table = TruthTableData(
        function_name="",
        test_cases=[],
        total_tests=0
    )
    
    # テストコード生成
    generator = UnityTestGenerator(include_target_function=False)
    test_code = generator.generate(truth_table, parsed_data)
    
    # 結果確認
    code = test_code.to_string()
    
    # 警告メッセージが含まれているか確認
    assert "警告:" in code or "検出されませんでした" in code, \
        "データがない場合の警告メッセージがない"
    
    print("✅ データがない場合のテスト成功")
    print()

if __name__ == "__main__":
    print("=" * 70)
    print("プロトタイプ宣言生成の改善テスト")
    print("=" * 70)
    print()
    
    try:
        test_with_complete_data()
        test_with_incomplete_data()
        test_with_no_data()
        
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
