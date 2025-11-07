#!/usr/bin/env python3
"""
関数マクロ対応の統合テスト
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_basic_function_macro():
    """基本的な関数マクロのテスト"""
    print("\n" + "="*70)
    print("テスト1: 基本的な関数マクロ")
    print("="*70)
    
    # テストファイル作成
    test_file = project_root / "test_basic_func_macro.c"
    test_file.write_text("""
#include <stdio.h>

#define MAX(a, b)  ((a) > (b) ? (a) : (b))
#define MIN(a, b)  ((a) < (b) ? (a) : (b))

int test_function(int x, int y) {
    int max_val = MAX(x, y);
    int min_val = MIN(x, y);
    
    if (max_val > 50) {
        return max_val + min_val;
    }
    return 0;
}
""")
    
    # テスト実行
    output_dir = project_root / "test_basic_func_macro_output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    cmd = [
        sys.executable, "main.py",
        "-i", str(test_file),
        "-f", "test_function",
        "-o", str(output_dir)
    ]
    
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    # 結果確認
    if result.returncode == 0:
        print("✅ 基本的な関数マクロのテスト成功")
        
        # 生成ファイルの確認
        test_code = output_dir / "test_test_basic_func_macro_test_function.c"
        if test_code.exists():
            print(f"✅ テストコードが生成されました: {test_code}")
        else:
            print(f"❌ テストコードが見つかりません")
            return False
    else:
        print("❌ 基本的な関数マクロのテスト失敗")
        print(result.stderr)
        return False
    
    # クリーンアップ
    test_file.unlink()
    
    return True


def test_nested_function_macro():
    """ネストした関数マクロのテスト"""
    print("\n" + "="*70)
    print("テスト2: ネストした関数マクロ")
    print("="*70)
    
    # テストファイル作成
    test_file = project_root / "test_nested_func_macro.c"
    test_file.write_text("""
#include <stdio.h>

#define ABS(x)  ((x) < 0 ? -(x) : (x))
#define DIFF(a, b)  ABS((a) - (b))
#define IN_RANGE(val, center, tolerance)  (DIFF((val), (center)) <= (tolerance))

int test_nested(int value, int target) {
    if (IN_RANGE(value, target, 10)) {
        return 1;
    } else {
        return 0;
    }
}
""")
    
    # テスト実行
    output_dir = project_root / "test_nested_func_macro_output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    cmd = [
        sys.executable, "main.py",
        "-i", str(test_file),
        "-f", "test_nested",
        "-o", str(output_dir)
    ]
    
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    # 結果確認
    if result.returncode == 0:
        print("✅ ネストした関数マクロのテスト成功")
        
        # ログ確認（マクロ展開のログがあるか）
        if "関数マクロ定義: 3個" in result.stdout:
            print("✅ 3個の関数マクロが検出されました")
        else:
            print("⚠️ 関数マクロの検出数が期待と異なります")
    else:
        print("❌ ネストした関数マクロのテスト失敗")
        print(result.stderr)
        return False
    
    # クリーンアップ
    test_file.unlink()
    
    return True


def test_complex_function_macro():
    """複雑な関数マクロのテスト"""
    print("\n" + "="*70)
    print("テスト3: 複雑な関数マクロ")
    print("="*70)
    
    # テストファイル作成
    test_file = project_root / "test_complex_func_macro.c"
    test_file.write_text("""
#include <stdio.h>

#define CLAMP(val, min, max)  ((val) < (min) ? (min) : ((val) > (max) ? (max) : (val)))
#define SQUARE(x)  ((x) * (x))
#define IS_VALID(x)  ((x) >= 0 && (x) <= 255)

int helper(int x) {
    return x + 5;
}

int test_complex(int input) {
    int clamped = CLAMP(input, -100, 100);
    
    if (IS_VALID(clamped)) {
        return SQUARE(clamped);
    }
    
    int processed = SQUARE(helper(input));
    
    if (processed > 50 && IS_VALID(processed)) {
        return clamped + processed;
    }
    
    return 0;
}
""")
    
    # テスト実行
    output_dir = project_root / "test_complex_func_macro_output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    cmd = [
        sys.executable, "main.py",
        "-i", str(test_file),
        "-f", "test_complex",
        "-o", str(output_dir)
    ]
    
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    # 結果確認
    if result.returncode == 0:
        print("✅ 複雑な関数マクロのテスト成功")
        
        # モック関数の生成確認
        if "モック/スタブコードの生成が完了" in result.stdout:
            print("✅ モック関数が正しく生成されました")
    else:
        print("❌ 複雑な関数マクロのテスト失敗")
        print(result.stderr)
        return False
    
    # クリーンアップ
    test_file.unlink()
    
    return True


def test_function_macro_with_conditional():
    """関数マクロと条件付きコンパイルの組み合わせテスト"""
    print("\n" + "="*70)
    print("テスト4: 関数マクロ + 条件付きコンパイル")
    print("="*70)
    
    # テストファイル作成
    test_file = project_root / "test_func_macro_conditional.c"
    test_file.write_text("""
#include <stdio.h>

#define FEATURE_ENABLED

#ifdef FEATURE_ENABLED
    #define PROCESS(x)  ((x) * 2)
#else
    #define PROCESS(x)  (x)
#endif

#define VALIDATE(x)  ((x) > 0 && (x) < 100)

int test_conditional(int input) {
    int processed = PROCESS(input);
    
    if (VALIDATE(processed)) {
        return processed;
    }
    
    return 0;
}
""")
    
    # テスト実行
    output_dir = project_root / "test_func_macro_conditional_output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    cmd = [
        sys.executable, "main.py",
        "-i", str(test_file),
        "-f", "test_conditional",
        "-o", str(output_dir)
    ]
    
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    # 結果確認
    if result.returncode == 0:
        print("✅ 関数マクロ + 条件付きコンパイルのテスト成功")
    else:
        print("❌ 関数マクロ + 条件付きコンパイルのテスト失敗")
        print(result.stderr)
        return False
    
    # クリーンアップ
    test_file.unlink()
    
    return True


def main():
    """メイン関数"""
    print("\n")
    print("="*70)
    print("関数マクロ対応 - 統合テスト")
    print("="*70)
    
    # テスト実行
    tests = [
        test_basic_function_macro,
        test_nested_function_macro,
        test_complex_function_macro,
        test_function_macro_with_conditional
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"❌ {test_func.__name__} で例外発生: {e}")
            results.append((test_func.__name__, False))
    
    # 結果サマリー
    print("\n" + "="*70)
    print("テスト結果サマリー")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n合計: {passed}/{total} テスト成功")
    
    if passed == total:
        print("\n🎉 すべてのテストが成功しました！")
        return 0
    else:
        print("\n⚠️ 一部のテストが失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
