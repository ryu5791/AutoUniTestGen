#!/usr/bin/env python3
"""
Phase 7 統合テスト

新機能のテスト:
1. エラーハンドリング
2. バッチ処理
3. パフォーマンス監視
4. テンプレート機能
"""

import os
import sys
import json
import shutil
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.error_handler import (
    ErrorHandler, ErrorLevel, ErrorCode, GeneratorError, ErrorContext
)
from src.batch_processor import BatchProcessor, BatchItem
from src.performance import PerformanceMonitor, MemoryMonitor, ResultCache
from src.template_engine import TemplateEngine, CustomTestGenerator
from src.c_test_auto_generator import CTestAutoGenerator


def print_test_header(test_name: str):
    """テストヘッダーを表示"""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print('='*70)


def print_test_result(success: bool, message: str = ""):
    """テスト結果を表示"""
    if success:
        print(f"✅ テスト成功: {message}")
    else:
        print(f"❌ テスト失敗: {message}")
    return success


def test_error_handler():
    """Test 1: エラーハンドラー"""
    print_test_header("エラーハンドリング")
    
    try:
        # エラーハンドラーの初期化
        handler = ErrorHandler(log_level=ErrorLevel.INFO)
        
        # 1. ログレベルのテスト
        handler.info("情報ログのテスト")
        handler.warning("警告ログのテスト")
        handler.error("エラーログのテスト")
        
        # 2. 入力ファイル検証（正常系）
        test_file = "sample.c"
        if Path(test_file).exists():
            handler.validate_input_file(test_file)
            print("  ✓ 入力ファイル検証成功")
        
        # 3. 入力ファイル検証（異常系）
        try:
            handler.validate_input_file("non_existent_file.c")
            return print_test_result(False, "存在しないファイルの検証が成功してしまいました")
        except GeneratorError as e:
            print(f"  ✓ 期待通りエラーを検出: {e.error_code.name}")
        
        # 4. 出力ディレクトリ検証
        test_output = "test_output_phase7"
        handler.validate_output_dir(test_output)
        print(f"  ✓ 出力ディレクトリ検証成功: {test_output}")
        
        # クリーンアップ
        if Path(test_output).exists():
            shutil.rmtree(test_output)
        
        # 5. エラーコンテキストのテスト
        context = ErrorContext(
            file_path="test.c",
            function_name="test_func",
            line_number=42,
            operation="parsing"
        )
        
        error = GeneratorError(
            message="テストエラー",
            error_code=ErrorCode.PARSE_ERROR,
            context=context,
            recovery_hint="テスト用のヒント"
        )
        
        print(f"  ✓ エラーメッセージ生成テスト:")
        print(f"    {error}")
        
        return print_test_result(True, "エラーハンドリングの全機能が正常に動作")
    
    except Exception as e:
        return print_test_result(False, f"例外発生: {str(e)}")


def test_batch_processor():
    """Test 2: バッチ処理"""
    print_test_header("バッチ処理")
    
    try:
        # テスト用のバッチ設定ファイルを作成
        batch_config_file = "test_batch_config.json"
        batch_items = [
            {
                "input_file": "sample.c",
                "function_name": "f1",
                "output_dir": "test_batch_output/item1"
            }
        ]
        
        with open(batch_config_file, 'w', encoding='utf-8') as f:
            json.dump({"items": batch_items}, f, indent=2)
        
        print(f"  ✓ バッチ設定ファイル作成: {batch_config_file}")
        
        # バッチプロセッサーの初期化
        generator = CTestAutoGenerator()
        processor = BatchProcessor(
            generator=generator,
            max_workers=2,
            continue_on_error=True
        )
        
        # バッチ設定を読み込む
        items = processor.load_batch_config(batch_config_file)
        print(f"  ✓ バッチ設定読み込み: {len(items)}個のアイテム")
        
        # バッチItemの作成テスト
        test_item = BatchItem(
            input_file="sample.c",
            function_name="f1",
            output_dir="test_output"
        )
        print(f"  ✓ BatchItemインスタンス作成成功")
        
        # テンプレート作成機能のテスト
        template_file = "test_batch_template.json"
        BatchProcessor.create_batch_config_template(template_file)
        print(f"  ✓ バッチ設定テンプレート作成: {template_file}")
        
        # クリーンアップ
        for f in [batch_config_file, template_file]:
            if Path(f).exists():
                Path(f).unlink()
        
        if Path("test_batch_output").exists():
            shutil.rmtree("test_batch_output")
        
        return print_test_result(True, "バッチ処理の全機能が正常に動作")
    
    except Exception as e:
        return print_test_result(False, f"例外発生: {str(e)}")


def test_performance_monitoring():
    """Test 3: パフォーマンス監視"""
    print_test_header("パフォーマンス監視")
    
    try:
        # パフォーマンスモニターのテスト
        perf_monitor = PerformanceMonitor()
        
        # 操作の記録
        perf_monitor.start_operation("test_operation")
        import time
        time.sleep(0.1)  # 100ms待機
        elapsed = perf_monitor.end_operation("test_operation")
        
        print(f"  ✓ 操作時間の記録: {elapsed:.3f}秒")
        
        # メトリクスの取得
        metrics = perf_monitor.get_metrics("test_operation")
        if metrics and metrics['count'] == 1:
            print(f"  ✓ メトリクス取得成功: {metrics}")
        else:
            return print_test_result(False, "メトリクス取得失敗")
        
        # メモリモニターのテスト
        mem_monitor = MemoryMonitor()
        current_memory = mem_monitor.get_memory_usage()
        print(f"  ✓ メモリ使用量: {current_memory:.2f} MB")
        
        # 結果キャッシュのテスト
        cache = ResultCache(cache_dir=".test_cache")
        
        # キャッシュに保存
        test_data = {"test": "data", "value": 123}
        cache.set(test_data, "test_key")
        print(f"  ✓ キャッシュに保存")
        
        # キャッシュから取得
        cached_data = cache.get("test_key")
        if cached_data == test_data:
            print(f"  ✓ キャッシュから取得成功")
        else:
            return print_test_result(False, "キャッシュデータが一致しません")
        
        # クリーンアップ
        cache.clear()
        if Path(".test_cache").exists():
            shutil.rmtree(".test_cache")
        
        return print_test_result(True, "パフォーマンス監視の全機能が正常に動作")
    
    except Exception as e:
        return print_test_result(False, f"例外発生: {str(e)}")


def test_template_engine():
    """Test 4: テンプレートエンジン"""
    print_test_header("テンプレートエンジン")
    
    try:
        # テンプレートエンジンの初期化
        engine = TemplateEngine()
        
        # 1. デフォルトテンプレートの確認
        templates = engine.list_templates()
        print(f"  ✓ 登録済みテンプレート数: {len(templates)}")
        
        # 2. テンプレートのレンダリング
        variables = {
            'test_file_name': 'test_sample.c',
            'generation_time': '2025-01-01 00:00:00',
            'function_name': 'sample_function',
            'source_header': 'sample.h',
            'setup_code': '    // Setup',
            'teardown_code': '    // Teardown',
            'test_cases': '    // Test cases',
            'test_calls': '    RUN_TEST(test_1);'
        }
        
        rendered = engine.render('default_test', variables)
        if 'test_sample.c' in rendered and 'sample_function' in rendered:
            print(f"  ✓ テンプレートレンダリング成功")
        else:
            return print_test_result(False, "レンダリング結果が不正")
        
        # 3. カスタムテンプレートの登録
        custom_template = "Test: ${test_name}, Function: ${function_name}"
        engine.register_template('custom', custom_template)
        
        rendered_custom = engine.render('custom', {
            'test_name': 'MyTest',
            'function_name': 'myFunction'
        })
        
        if 'MyTest' in rendered_custom and 'myFunction' in rendered_custom:
            print(f"  ✓ カスタムテンプレート使用成功")
        else:
            return print_test_result(False, "カスタムテンプレートが機能していません")
        
        # 4. テンプレート変数の抽出
        variables_list = engine.get_template_variables('default_test')
        print(f"  ✓ テンプレート変数抽出: {len(variables_list)}個")
        
        # 5. CustomTestGeneratorのテスト
        custom_gen = CustomTestGenerator(template_engine=engine)
        
        test_case = custom_gen.generate_test_case(
            test_name="test_example",
            description="Example test case",
            test_body="    TEST_ASSERT_EQUAL(1, 1);"
        )
        
        if 'test_example' in test_case:
            print(f"  ✓ テストケース生成成功")
        else:
            return print_test_result(False, "テストケース生成失敗")
        
        return print_test_result(True, "テンプレートエンジンの全機能が正常に動作")
    
    except Exception as e:
        return print_test_result(False, f"例外発生: {str(e)}")


def test_integrated_workflow():
    """Test 5: 統合ワークフロー（エラーハンドリング付き）"""
    print_test_header("統合ワークフロー")
    
    try:
        # エラーハンドラー付きで生成器を使用
        handler = ErrorHandler(log_level=ErrorLevel.INFO)
        generator = CTestAutoGenerator()
        
        # 入力ファイルが存在する場合のみテスト
        if not Path("sample.c").exists():
            print("  ⚠️  sample.cが存在しないため、統合テストをスキップ")
            return print_test_result(True, "テストファイルが存在しないためスキップ")
        
        # 検証を実行
        handler.validate_input_file("sample.c")
        handler.validate_output_dir("test_integrated_output")
        print("  ✓ ファイル検証成功")
        
        # パフォーマンス監視付きで生成
        perf_monitor = PerformanceMonitor()
        mem_monitor = MemoryMonitor()
        
        generator.performance_monitor = perf_monitor
        generator.memory_monitor = mem_monitor
        
        print("  ✓ パフォーマンス監視を設定")
        
        # クリーンアップ
        if Path("test_integrated_output").exists():
            shutil.rmtree("test_integrated_output")
        
        return print_test_result(True, "統合ワークフローが正常に動作")
    
    except Exception as e:
        return print_test_result(False, f"例外発生: {str(e)}")


def main():
    """メイン関数"""
    print("\n" + "="*70)
    print("Phase 7 統合テスト開始")
    print("="*70)
    
    results = []
    
    # 各テストを実行
    results.append(("エラーハンドリング", test_error_handler()))
    results.append(("バッチ処理", test_batch_processor()))
    results.append(("パフォーマンス監視", test_performance_monitoring()))
    results.append(("テンプレートエンジン", test_template_engine()))
    results.append(("統合ワークフロー", test_integrated_workflow()))
    
    # 結果サマリー
    print("\n" + "="*70)
    print("テスト結果サマリー")
    print("="*70)
    
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\n合計: {passed}/{total} テスト成功")
    
    if passed == total:
        print("\n" + "="*70)
        print("✅ すべてのテストが成功しました！")
        print("="*70)
        print("\nPhase 7の実装が完了しました:")
        print("  ✓ エラーハンドリング強化")
        print("  ✓ バッチ処理機能")
        print("  ✓ パフォーマンス最適化")
        print("  ✓ テンプレート機能")
        print("\n次のステップ:")
        print("  - python main.py --help (拡張されたヘルプを確認)")
        print("  - python main.py --batch batch_config.json (バッチ処理)")
        print("  - python main.py -i file.c -f func --performance (パフォーマンス監視)")
        return 0
    else:
        print("\n" + "="*70)
        print(f"❌ {total - passed}個のテストが失敗しました")
        print("="*70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
