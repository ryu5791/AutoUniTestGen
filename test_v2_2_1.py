"""
v2.2.1テスト - 型定義の完全な抽出テスト
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser.c_code_parser import CCodeParser
from src.test_generator.unity_test_generator import UnityTestGenerator
from src.truth_table.truth_table_generator import TruthTableGenerator


def test_nested_typedef():
    """ネストした型定義の抽出テスト"""
    print("\n" + "=" * 70)
    print("TEST: ネストした型定義の完全な抽出")
    print("=" * 70)
    
    # 複雑なネストした型定義
    sample_code = """
typedef union {
    uint16_t Utm22;
    uint8_t Utm92[2];
    struct {
        uint8_t Utm94 : 1;
        uint8_t Utm95 : 1;
        uint8_t Utm96 : 1;
    } Utx84;
} Utx68;

typedef union {
    uint8_t Utm92[8];
    struct {
        uint8_t Utm93;
        Utx68 Utx89;
        uint8_t Utm110[5];
    } Utm1;
} Utx50;

void test_func(void) {
    if (Utm10 > 0) {
        return;
    }
}
"""
    
    # ファイルに書き込み
    test_file = "/tmp/test_nested_typedef.c"
    with open(test_file, 'w') as f:
        f.write(sample_code)
    
    # パーサーで解析
    parser = CCodeParser()
    parsed_data = parser.parse(test_file, "test_func")
    
    if not parsed_data:
        print("✗ 解析失敗")
        return False
    
    print(f"✓ {len(parsed_data.typedefs)}個の型定義を抽出")
    
    # 各型定義の内容を確認
    unknown_count = 0
    for td in parsed_data.typedefs:
        print(f"\n--- {td.name} ({td.typedef_type}) ---")
        print(td.definition[:200] + "..." if len(td.definition) > 200 else td.definition)
        
        # typedef /* unknown */ がないことを確認
        if "/* unknown */" in td.definition:
            unknown_count += 1
            print(f"✗ 完全な定義が抽出できていません")
    
    # Utx68とUtx50が完全に抽出されているか確認
    utx68 = next((td for td in parsed_data.typedefs if td.name == "Utx68"), None)
    utx50 = next((td for td in parsed_data.typedefs if td.name == "Utx50"), None)
    
    success = True
    
    if utx68:
        if "/* unknown */" in utx68.definition:
            print(f"\n✗ Utx68の定義が不完全です")
            success = False
        else:
            print(f"\n✓ Utx68の完全な定義を抽出しました")
    
    if utx50:
        if "/* unknown */" in utx50.definition:
            print(f"✗ Utx50の定義が不完全です")
            success = False
        else:
            print(f"✓ Utx50の完全な定義を抽出しました")
    
    if unknown_count > 0:
        print(f"\n⚠️ {unknown_count}個の型定義が不完全でした")
    else:
        print(f"\n✅ すべての型定義を完全に抽出しました！")
    
    return success and unknown_count == 0


def test_real_file_full_extraction():
    """実際のファイルで完全な抽出をテスト"""
    print("\n" + "=" * 70)
    print("TEST: 実際のファイルでの完全な抽出")
    print("=" * 70)
    
    test_file = "/mnt/project/22_難読化_obfuscated.c"
    
    if not os.path.exists(test_file):
        print(f"✗ ファイルが見つかりません: {test_file}")
        return False
    
    # パーサーで解析
    parser = CCodeParser()
    parsed_data = parser.parse(test_file, "Utf1")
    
    if not parsed_data:
        print("✗ 解析失敗")
        return False
    
    print(f"✓ 解析成功")
    print(f"  - 型定義: {len(parsed_data.typedefs)}個")
    
    # typedef /* unknown */ の数をカウント
    unknown_count = 0
    complete_count = 0
    
    for td in parsed_data.typedefs:
        if "/* unknown */" in td.definition:
            unknown_count += 1
        else:
            complete_count += 1
    
    print(f"\n型定義の抽出状況:")
    print(f"  - 完全に抽出: {complete_count}個 ✓")
    print(f"  - 不完全: {unknown_count}個")
    
    if unknown_count > 0:
        print(f"\n不完全な型定義:")
        for td in parsed_data.typedefs:
            if "/* unknown */" in td.definition:
                print(f"  - {td.name} (行 {td.line_number})")
    
    # 真偽表とテストコードを生成
    truth_gen = TruthTableGenerator()
    truth_table = truth_gen.generate(parsed_data)
    
    test_gen = UnityTestGenerator()
    test_code = test_gen.generate(truth_table, parsed_data)
    
    # ファイルに保存
    output_file = "/tmp/test_Utf1_v2_2_1.c"
    test_code.save(output_file)
    print(f"\n✓ テストコードを保存: {output_file}")
    
    # 生成されたコードの一部を表示
    code_str = test_code.to_string()
    
    # 型定義セクションを表示
    print("\n生成された型定義の例（最初の100行）:")
    print("-" * 70)
    lines = code_str.split('\n')
    in_typedef_section = False
    line_count = 0
    for line in lines:
        if "型定義" in line:
            in_typedef_section = True
        if in_typedef_section:
            print(line)
            line_count += 1
            if line_count >= 100 or line.startswith("// ===== プロトタイプ"):
                break
    print("-" * 70)
    
    improvement_rate = (complete_count / len(parsed_data.typedefs) * 100) if parsed_data.typedefs else 0
    print(f"\n完全抽出率: {improvement_rate:.1f}%")
    
    if improvement_rate >= 80:
        print("✅ テスト成功: 80%以上の型定義を完全に抽出")
        return True
    else:
        print(f"⚠️ 改善の余地あり: {improvement_rate:.1f}%")
        return False


def main():
    """メイン関数"""
    print("\n" + "=" * 70)
    print("AutoUniTestGen v2.2.1 テスト")
    print("型定義の完全な抽出機能の検証")
    print("=" * 70)
    
    tests = [
        ("ネストした型定義", test_nested_typedef),
        ("実際のファイル", test_real_file_full_extraction),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ テスト'{name}'で例外が発生: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # サマリー
    print("\n" + "=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 70)
    print(f"結果: {passed}/{total} テスト成功")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました！")
        print("\nv2.2.1の改善が正常に動作しています:")
        print("  ✓ 型定義の完全な抽出")
        print("  ✓ ネストした波括弧への対応")
        print("  ✓ typedef /* unknown */ の削減")
    else:
        print(f"⚠️ {total - passed}個のテストが失敗しました")
    
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
