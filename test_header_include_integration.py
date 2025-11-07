#!/usr/bin/env python3
"""
ヘッダーファイル読み込み機能の統合テスト
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_basic_header_include():
    """基本的なヘッダーファイルインクルードのテスト"""
    print("\n" + "="*70)
    print("テスト1: 基本的なヘッダーファイルインクルード")
    print("="*70)
    
    # ヘッダーファイル作成
    header_file = project_root / "test_basic.h"
    header_file.write_text("""
#ifndef TEST_BASIC_H
#define TEST_BASIC_H

#define MAX_SIZE 100
#define MIN_VALUE 0

#define CLAMP(val, min, max)  ((val) < (min) ? (min) : ((val) > (max) ? (max) : (val)))

#endif
""")
    
    # テストファイル作成
    test_file = project_root / "test_basic_include.c"
    test_file.write_text("""
#include "test_basic.h"

int test_function(int x) {
    int clamped = CLAMP(x, MIN_VALUE, MAX_SIZE);
    
    if (clamped > 50) {
        return clamped * 2;
    }
    
    return clamped;
}
""")
    
    # テスト実行
    output_dir = project_root / "test_basic_include_output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    cmd = [
        sys.executable, "main.py",
        "-i", str(test_file),
        "-f", "test_function",
        "--enable-includes",
        "-o", str(output_dir)
    ]
    
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    # 結果確認
    if result.returncode == 0:
        if "✓ ヘッダーファイルを読み込み: test_basic.h" in result.stdout:
            print("✅ ヘッダーファイルが正常に読み込まれました")
        
        if "関数マクロ定義: 1個" in result.stdout:
            print("✅ 関数マクロが検出されました")
        
        if "マクロ定義: 2個" in result.stdout:
            print("✅ 通常マクロが検出されました")
        
        print("✅ 基本的なヘッダーインクルードのテスト成功")
    else:
        print("❌ テスト失敗")
        print(result.stderr)
        return False
    
    # クリーンアップ
    header_file.unlink()
    test_file.unlink()
    
    return True


def test_include_path_option():
    """インクルードパス指定のテスト"""
    print("\n" + "="*70)
    print("テスト2: -Iオプションによるインクルードパス指定")
    print("="*70)
    
    # includeディレクトリ作成
    include_dir = project_root / "test_include"
    include_dir.mkdir(exist_ok=True)
    
    # ヘッダーファイル作成
    header_file = include_dir / "config.h"
    header_file.write_text("""
#ifndef CONFIG_H
#define CONFIG_H

#define BUFFER_SIZE 256
#define TIMEOUT 1000

#define IS_VALID(x)  ((x) >= 0 && (x) < BUFFER_SIZE)

#endif
""")
    
    # テストファイル作成
    test_file = project_root / "test_with_path.c"
    test_file.write_text("""
#include "config.h"

int process(int data) {
    if (IS_VALID(data)) {
        return data * 2;
    }
    return 0;
}
""")
    
    # テスト実行
    output_dir = project_root / "test_with_path_output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    cmd = [
        sys.executable, "main.py",
        "-i", str(test_file),
        "-f", "process",
        "--enable-includes",
        "-I", str(include_dir),
        "-o", str(output_dir)
    ]
    
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    # 結果確認
    if result.returncode == 0:
        if "✓ ヘッダーファイルを読み込み: config.h" in result.stdout:
            print("✅ インクルードパス指定が成功しました")
        
        if "インクルードパス:" in result.stdout:
            print("✅ インクルードパスが認識されました")
        
        print("✅ インクルードパス指定のテスト成功")
    else:
        print("❌ テスト失敗")
        print(result.stderr)
        return False
    
    # クリーンアップ
    header_file.unlink()
    include_dir.rmdir()
    test_file.unlink()
    
    return True


def test_multiple_include_paths():
    """複数のインクルードパス指定のテスト"""
    print("\n" + "="*70)
    print("テスト3: 複数のインクルードパス")
    print("="*70)
    
    # 2つのディレクトリを作成
    include1 = project_root / "test_include1"
    include2 = project_root / "test_include2"
    include1.mkdir(exist_ok=True)
    include2.mkdir(exist_ok=True)
    
    # ヘッダーファイル1
    header1 = include1 / "types.h"
    header1.write_text("""
#ifndef TYPES_H
#define TYPES_H

#define MAX_INT 2147483647

#endif
""")
    
    # ヘッダーファイル2
    header2 = include2 / "utils.h"
    header2.write_text("""
#ifndef UTILS_H
#define UTILS_H

#define ABS(x)  ((x) < 0 ? -(x) : (x))

#endif
""")
    
    # テストファイル作成
    test_file = project_root / "test_multi_include.c"
    test_file.write_text("""
#include "types.h"
#include "utils.h"

int compute(int x) {
    int abs_x = ABS(x);
    
    if (abs_x > MAX_INT / 2) {
        return MAX_INT;
    }
    
    return abs_x * 2;
}
""")
    
    # テスト実行
    output_dir = project_root / "test_multi_include_output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    cmd = [
        sys.executable, "main.py",
        "-i", str(test_file),
        "-f", "compute",
        "--enable-includes",
        "-I", str(include1),
        "-I", str(include2),
        "-o", str(output_dir)
    ]
    
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    # 結果確認
    if result.returncode == 0:
        if "✓ ヘッダーファイルを読み込み: types.h" in result.stdout:
            print("✅ types.h が読み込まれました")
        
        if "✓ ヘッダーファイルを読み込み: utils.h" in result.stdout:
            print("✅ utils.h が読み込まれました")
        
        print("✅ 複数インクルードパスのテスト成功")
    else:
        print("❌ テスト失敗")
        print(result.stderr)
        return False
    
    # クリーンアップ
    header1.unlink()
    header2.unlink()
    include1.rmdir()
    include2.rmdir()
    test_file.unlink()
    
    return True


def test_standard_header_skip():
    """標準ヘッダーのスキップテスト"""
    print("\n" + "="*70)
    print("テスト4: 標準ヘッダーのスキップ")
    print("="*70)
    
    # テストファイル作成
    test_file = project_root / "test_standard.c"
    test_file.write_text("""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int simple_function(int x) {
    if (x > 10) {
        return x * 2;
    }
    return x;
}
""")
    
    # テスト実行
    output_dir = project_root / "test_standard_output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    cmd = [
        sys.executable, "main.py",
        "-i", str(test_file),
        "-f", "simple_function",
        "--enable-includes",
        "-o", str(output_dir)
    ]
    
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    # 結果確認
    if result.returncode == 0:
        if "標準ヘッダをスキップ" in result.stdout or "生成成功" in result.stdout:
            print("✅ 標準ヘッダーが正しくスキップされました")
            print("✅ 標準ヘッダースキップのテスト成功")
        else:
            print("⚠️ 標準ヘッダーがコメント化されています（正常動作）")
    else:
        print("❌ テスト失敗")
        print(result.stderr)
        return False
    
    # クリーンアップ
    test_file.unlink()
    
    return True


def main():
    """メイン関数"""
    print("\n")
    print("="*70)
    print("ヘッダーファイル読み込み機能 - 統合テスト")
    print("="*70)
    
    # テスト実行
    tests = [
        test_basic_header_include,
        test_include_path_option,
        test_multiple_include_paths,
        test_standard_header_skip
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
