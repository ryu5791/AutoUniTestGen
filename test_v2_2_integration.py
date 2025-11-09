"""
v2.2統合テスト

型定義・変数宣言の自動生成機能のテスト
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser.c_code_parser import CCodeParser
from src.truth_table.truth_table_generator import TruthTableGenerator
from src.test_generator.unity_test_generator import UnityTestGenerator


def test_typedef_extraction():
    """型定義の抽出テスト"""
    print("\n" + "=" * 70)
    print("TEST: 型定義の抽出")
    print("=" * 70)
    
    # サンプルソースコード
    sample_code = """
typedef union {
    uint16_t Utm22;
    uint8_t Utm92[2];
} Utx68;

typedef union {
    uint8_t Utm92[8];
    struct {
        uint8_t Utm93;
        Utx68 Utx89;
    } Utm1;
} Utx50;

void Utf1(void) {
    if (Utm10 > 0) {
        return;
    }
}
"""
    
    # ファイルに書き込み
    test_file = "/tmp/test_typedef.c"
    with open(test_file, 'w') as f:
        f.write(sample_code)
    
    # パーサーで解析
    parser = CCodeParser()
    parsed_data = parser.parse(test_file, "Utf1")
    
    if not parsed_data:
        print("✗ 解析失敗")
        return False
    
    # 型定義の確認
    print(f"✓ {len(parsed_data.typedefs)}個の型定義を抽出")
    for td in parsed_data.typedefs:
        print(f"  - {td.name} ({td.typedef_type})")
        if td.dependencies:
            print(f"    依存: {', '.join(td.dependencies)}")
    
    # 期待: Utx68とUtx50の2つ
    if len(parsed_data.typedefs) < 2:
        print(f"✗ 期待される型定義数: 2, 実際: {len(parsed_data.typedefs)}")
        return False
    
    print("✅ テスト成功: 型定義の抽出")
    return True


def test_variable_extraction():
    """変数宣言の抽出テスト"""
    print("\n" + "=" * 70)
    print("TEST: 変数宣言の抽出")
    print("=" * 70)
    
    # サンプルソースコード
    sample_code = """
uint8_t Utm10;
uint8_t Utm11;

void Utf1(void) {
    if (Utm10 > 0 && Utm11 < 10) {
        return;
    }
}
"""
    
    # ファイルに書き込み
    test_file = "/tmp/test_variable.c"
    with open(test_file, 'w') as f:
        f.write(sample_code)
    
    # パーサーで解析
    parser = CCodeParser()
    parsed_data = parser.parse(test_file, "Utf1")
    
    if not parsed_data:
        print("✗ 解析失敗")
        return False
    
    # 変数宣言の確認
    print(f"✓ {len(parsed_data.variables)}個の変数宣言を抽出")
    for var in parsed_data.variables:
        print(f"  - {var.name} ({var.var_type})")
        print(f"    定義: {var.definition}")
    
    # 期待: Utm10とUtm11の2つ
    if len(parsed_data.variables) < 2:
        print(f"✗ 期待される変数数: 2, 実際: {len(parsed_data.variables)}")
        return False
    
    print("✅ テスト成功: 変数宣言の抽出")
    return True


def test_dependency_resolution():
    """依存関係の解決テスト"""
    print("\n" + "=" * 70)
    print("TEST: 依存関係の解決")
    print("=" * 70)
    
    from src.parser.typedef_extractor import TypedefInfo
    from src.parser.dependency_resolver import DependencyResolver
    
    # テスト用の型定義（Utx50はUtx68に依存）
    typedefs = [
        TypedefInfo(
            name="Utx50",
            typedef_type="union",
            definition="typedef union { Utx68 x; } Utx50;",
            dependencies=["Utx68"],
            line_number=5
        ),
        TypedefInfo(
            name="Utx68",
            typedef_type="union",
            definition="typedef union { uint8_t x; } Utx68;",
            dependencies=[],
            line_number=1
        ),
    ]
    
    # 依存関係を解決
    resolver = DependencyResolver()
    sorted_typedefs = resolver.resolve_order(typedefs)
    
    print(f"✓ ソート順序:")
    for i, td in enumerate(sorted_typedefs, 1):
        print(f"  {i}. {td.name}")
    
    # Utx68がUtx50より先に来ることを確認
    names = [td.name for td in sorted_typedefs]
    utx68_idx = names.index("Utx68")
    utx50_idx = names.index("Utx50")
    
    if utx68_idx > utx50_idx:
        print(f"✗ 依存順序が正しくありません: Utx68={utx68_idx}, Utx50={utx50_idx}")
        return False
    
    print("✅ テスト成功: 依存関係の解決")
    return True


def test_code_generation():
    """テストコード生成テスト"""
    print("\n" + "=" * 70)
    print("TEST: テストコード生成")
    print("=" * 70)
    
    # サンプルソースコード
    sample_code = """
typedef union {
    uint8_t data[2];
} MyType;

uint8_t global_var;

void test_func(void) {
    if (global_var > 0) {
        return;
    }
}
"""
    
    # ファイルに書き込み
    test_file = "/tmp/test_codegen.c"
    with open(test_file, 'w') as f:
        f.write(sample_code)
    
    # パーサーで解析
    parser = CCodeParser()
    parsed_data = parser.parse(test_file, "test_func")
    
    if not parsed_data:
        print("✗ 解析失敗")
        return False
    
    # 真偽表を生成
    truth_gen = TruthTableGenerator()
    truth_table = truth_gen.generate(parsed_data)
    
    # テストコードを生成
    test_gen = UnityTestGenerator()
    test_code = test_gen.generate(truth_table, parsed_data)
    
    # 生成されたコードを確認
    code_str = test_code.to_string()
    
    # 型定義が含まれていることを確認
    if "MyType" in code_str:
        print("✓ 型定義が含まれています")
    else:
        print("✗ 型定義が含まれていません")
        return False
    
    # 変数宣言が含まれていることを確認
    if "extern uint8_t global_var" in code_str:
        print("✓ 変数宣言が含まれています")
    else:
        print("✗ 変数宣言が含まれていません")
        return False
    
    # ファイルに保存
    output_file = "/tmp/test_generated_v2_2.c"
    test_code.save(output_file)
    print(f"✓ テストコードを保存: {output_file}")
    
    # 一部を表示
    print("\n生成されたコードの一部:")
    print("-" * 70)
    lines = code_str.split('\n')
    # 型定義セクションを表示
    in_typedef_section = False
    for line in lines:
        if "型定義" in line:
            in_typedef_section = True
        if in_typedef_section:
            print(line)
            if line.startswith("// ===== 外部変数"):
                break
    print("-" * 70)
    
    print("✅ テスト成功: テストコード生成")
    return True


def test_real_file():
    """実際のファイルでのテスト"""
    print("\n" + "=" * 70)
    print("TEST: 実際のファイル (22_難読化_obfuscated.c)")
    print("=" * 70)
    
    # プロジェクトファイルを使用
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
    print(f"  - 変数宣言: {len(parsed_data.variables)}個")
    print(f"  - 条件分岐: {len(parsed_data.conditions)}個")
    
    # 型定義の一部を表示
    if parsed_data.typedefs:
        print("\n型定義の例（最初の3つ）:")
        for td in parsed_data.typedefs[:3]:
            print(f"  - {td.name} ({td.typedef_type}, {td.line_number}行目)")
            if td.dependencies:
                print(f"    依存: {', '.join(td.dependencies[:5])}")
    
    # 真偽表を生成
    truth_gen = TruthTableGenerator()
    truth_table = truth_gen.generate(parsed_data)
    print(f"\n✓ 真偽表生成: {len(truth_table.test_cases)}個のテストケース")
    
    # テストコードを生成
    test_gen = UnityTestGenerator()
    test_code = test_gen.generate(truth_table, parsed_data)
    
    # ファイルに保存
    output_file = "/tmp/test_Utf1_v2_2.c"
    test_code.save(output_file)
    print(f"✓ テストコードを保存: {output_file}")
    
    # 統計情報
    code_str = test_code.to_string()
    lines = code_str.split('\n')
    print(f"\n生成されたコード:")
    print(f"  - 総行数: {len(lines)}行")
    print(f"  - テスト関数数: {len(truth_table.test_cases) * 2}個")
    
    print("\n✅ テスト成功: 実際のファイル")
    return True


def main():
    """メイン関数"""
    print("\n" + "=" * 70)
    print("AutoUniTestGen v2.2 統合テスト")
    print("=" * 70)
    
    tests = [
        ("型定義の抽出", test_typedef_extraction),
        ("変数宣言の抽出", test_variable_extraction),
        ("依存関係の解決", test_dependency_resolution),
        ("テストコード生成", test_code_generation),
        ("実際のファイル", test_real_file),
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
        print("\nv2.2の新機能が正常に動作しています:")
        print("  ✓ 型定義の自動抽出・生成")
        print("  ✓ 変数宣言の自動抽出・生成")
        print("  ✓ 依存関係の自動解決")
    else:
        print(f"⚠️ {total - passed}個のテストが失敗しました")
    
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
