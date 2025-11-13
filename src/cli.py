#!/usr/bin/env python3
"""
C言語単体テスト自動生成ツール - CLIインターフェース (Phase 7 Enhanced)

コマンドライン引数を処理してテスト生成を実行
Phase 7の新機能:
- エラーハンドリング強化
- バッチ処理
- パフォーマンス最適化
- テンプレート機能
"""

import argparse
import sys
from pathlib import Path

# 相対importと絶対importの両方に対応
try:
    # パッケージとして実行された場合（python -m src.cli）
    from .c_test_auto_generator import CTestAutoGenerator
    from .config import ConfigManager
    from .error_handler import ErrorHandler, ErrorLevel, get_error_handler
    from .batch_processor import BatchProcessor
    from .performance import (
        PerformanceMonitor, MemoryMonitor, ResultCache,
        get_performance_monitor, get_memory_monitor, get_result_cache
    )
    from .template_engine import TemplateEngine, create_template_files
except ImportError:
    # 直接実行された場合（python src/cli.py）
    # srcディレクトリの親をパスに追加
    import os
    parent_dir = Path(__file__).resolve().parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from src.c_test_auto_generator import CTestAutoGenerator
    from src.config import ConfigManager
    from src.error_handler import ErrorHandler, ErrorLevel, get_error_handler
    from src.batch_processor import BatchProcessor
    from src.performance import (
        PerformanceMonitor, MemoryMonitor, ResultCache,
        get_performance_monitor, get_memory_monitor, get_result_cache
    )
    from src.template_engine import TemplateEngine, create_template_files


VERSION = "2.2"


def create_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーを作成"""
    parser = argparse.ArgumentParser(
        prog='c-test-gen',
        description='C言語単体テスト自動生成ツール - MC/DC真偽表、Unityテストコード、I/O表を自動生成',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # すべて生成（真偽表、テストコード、I/O表）
  %(prog)s -i sample.c -f calculate -o output

  # 真偽表のみ生成
  %(prog)s -i sample.c -f calculate -o output --truth-only

  # テストコードのみ生成
  %(prog)s -i sample.c -f calculate -o output --test-only

  # I/O表のみ生成
  %(prog)s -i sample.c -f calculate -o output --io-only

  # 設定ファイルを使用
  %(prog)s -i sample.c -f calculate -c config.json
  
  # バッチ処理
  %(prog)s --batch batch_config.json
  
  # バッチ処理（並列実行）
  %(prog)s --batch batch_config.json --parallel --workers 4
  
  # ディレクトリ一括処理
  %(prog)s --batch-dir src/ --pattern "*.c"
  
  # カスタムテンプレート使用
  %(prog)s -i sample.c -f calc --template my_template
  
  # パフォーマンス監視
  %(prog)s -i sample.c -f calc --performance

  # バージョン表示
  %(prog)s --version
        """
    )
    
    # 必須引数（バッチモード以外）
    parser.add_argument(
        '-i', '--input',
        type=str,
        metavar='FILE',
        help='入力するC言語ソースファイルパス'
    )
    
    parser.add_argument(
        '-f', '--function',
        type=str,
        metavar='FUNC',
        help='テスト対象関数名'
    )
    
    # オプション引数
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output',
        metavar='DIR',
        help='出力ディレクトリパス (デフォルト: output)'
    )
    
    parser.add_argument(
        '-D', '--define',
        action='append',
        metavar='MACRO[=VALUE]',
        help='マクロを定義 (例: -D TYPE1 -D MAX_SIZE=100)'
    )
    
    parser.add_argument(
        '-I', '--include-path',
        action='append',
        metavar='PATH',
        help='ヘッダーファイルの検索パス (例: -I ./include -I ../common)'
    )
    
    parser.add_argument(
        '--enable-includes',
        action='store_true',
        help='ヘッダーファイル（.h）の読み込みを有効化'
    )
    
    parser.add_argument(
        '--preset',
        type=str,
        metavar='NAME',
        help='モデルプリセットを使用 (例: --preset model_a)'
    )
    
    parser.add_argument(
        '--list-presets',
        action='store_true',
        help='利用可能なモデルプリセット一覧を表示'
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        metavar='FILE',
        help='設定ファイルパス (JSON形式)'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='既存ファイルを確認なしで上書き'
    )
    
    parser.add_argument(
        '--no-overwrite',
        action='store_true',
        help='既存ファイルがある場合はエラーで終了'
    )
    
    # v2.4.3: スタンドアロンモードオプション
    parser.add_argument(
        '--no-standalone',
        action='store_true',
        help='スタンドアロンモードを無効化（元のソースとテストコードを分離）'
    )
    
    # 出力ファイル名指定
    parser.add_argument(
        '--truth-table',
        type=str,
        metavar='FILE',
        help='真偽表ファイル名 (デフォルト: 自動生成)'
    )
    
    parser.add_argument(
        '--test-code',
        type=str,
        metavar='FILE',
        help='テストコードファイル名 (デフォルト: 自動生成)'
    )
    
    parser.add_argument(
        '--io-table',
        type=str,
        metavar='FILE',
        help='I/O表ファイル名 (デフォルト: 自動生成)'
    )
    
    # 生成モード選択（排他的）
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--truth-only',
        action='store_true',
        help='真偽表のみ生成'
    )
    
    mode_group.add_argument(
        '--test-only',
        action='store_true',
        help='テストコードのみ生成'
    )
    
    mode_group.add_argument(
        '--io-only',
        action='store_true',
        help='I/O表のみ生成'
    )
    
    # Phase 7: バッチ処理オプション
    batch_group = parser.add_argument_group('バッチ処理オプション')
    batch_group.add_argument(
        '--batch',
        type=str,
        metavar='FILE',
        help='バッチ設定ファイル (JSON形式)'
    )
    
    batch_group.add_argument(
        '--batch-dir',
        type=str,
        metavar='DIR',
        help='ディレクトリ内のすべてのファイルをバッチ処理'
    )
    
    batch_group.add_argument(
        '--pattern',
        type=str,
        default='*.c',
        metavar='PATTERN',
        help='バッチディレクトリのファイルパターン (デフォルト: *.c)'
    )
    
    batch_group.add_argument(
        '--parallel',
        action='store_true',
        help='バッチ処理を並列実行'
    )
    
    batch_group.add_argument(
        '--workers',
        type=int,
        default=4,
        metavar='N',
        help='並列処理のワーカー数 (デフォルト: 4)'
    )
    
    batch_group.add_argument(
        '--continue-on-error',
        action='store_true',
        help='エラーが発生しても処理を継続'
    )
    
    batch_group.add_argument(
        '--save-results',
        type=str,
        metavar='FILE',
        help='バッチ処理結果をJSONファイルに保存'
    )
    
    # Phase 7: パフォーマンスオプション
    perf_group = parser.add_argument_group('パフォーマンスオプション')
    perf_group.add_argument(
        '--performance',
        action='store_true',
        help='パフォーマンス監視を有効化'
    )
    
    perf_group.add_argument(
        '--no-cache',
        action='store_true',
        help='結果キャッシュを無効化'
    )
    
    perf_group.add_argument(
        '--memory-limit',
        type=int,
        default=1000,
        metavar='MB',
        help='メモリ使用量の制限 (MB, デフォルト: 1000)'
    )
    
    # Phase 7: ログオプション
    log_group = parser.add_argument_group('ログオプション')
    log_group.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='ログレベル (デフォルト: INFO)'
    )
    
    log_group.add_argument(
        '--log-file',
        type=str,
        metavar='FILE',
        help='ログファイルパス'
    )
    
    # Phase 7: テンプレートオプション
    template_group = parser.add_argument_group('テンプレートオプション')
    template_group.add_argument(
        '--template',
        type=str,
        metavar='NAME',
        help='使用するテンプレート名'
    )
    
    template_group.add_argument(
        '--template-dir',
        type=str,
        metavar='DIR',
        help='テンプレートディレクトリ'
    )
    
    template_group.add_argument(
        '--list-templates',
        action='store_true',
        help='利用可能なテンプレートを表示'
    )
    
    template_group.add_argument(
        '--create-templates',
        type=str,
        metavar='DIR',
        help='サンプルテンプレートファイルを作成'
    )
    
    # v2.2: コード生成オプション
    codegen_group = parser.add_argument_group('v2.2 コード生成オプション')
    codegen_group.add_argument(
        '--include-target-function',
        action='store_true',
        default=True,
        help='テスト対象関数の本体をテストコードに含める（デフォルト: 有効）'
    )
    
    codegen_group.add_argument(
        '--no-include-target-function',
        dest='include_target_function',
        action='store_false',
        help='テスト対象関数の本体をテストコードに含めない'
    )
    
    # その他
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {VERSION}'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細な出力を表示'
    )
    
    parser.add_argument(
        '--create-config',
        type=str,
        metavar='FILE',
        help='デフォルト設定ファイルを作成して終了'
    )
    
    parser.add_argument(
        '--create-batch-config',
        type=str,
        metavar='FILE',
        help='バッチ設定ファイルのテンプレートを作成して終了'
    )
    
    return parser


def validate_args(args: argparse.Namespace) -> bool:
    """
    引数を検証
    
    Args:
        args: パース済み引数
    
    Returns:
        bool: 検証成功したかどうか
    """
    # バッチモードの場合は異なる検証
    if args.batch or args.batch_dir:
        if args.batch:
            batch_path = Path(args.batch)
            if not batch_path.exists():
                print(f"❌ エラー: バッチ設定ファイルが見つかりません: {args.batch}", file=sys.stderr)
                return False
        
        if args.batch_dir:
            dir_path = Path(args.batch_dir)
            if not dir_path.exists() or not dir_path.is_dir():
                print(f"❌ エラー: バッチディレクトリが見つかりません: {args.batch_dir}", file=sys.stderr)
                return False
        
        return True
    
    # 通常モードの検証
    if not args.input or not args.function:
        print("❌ エラー: -i (--input) と -f (--function) は必須です", file=sys.stderr)
        print("ヘルプを表示: python main.py --help", file=sys.stderr)
        return False
    
    # 入力ファイルの存在確認
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ エラー: 入力ファイルが見つかりません: {args.input}", file=sys.stderr)
        return False
    
    if not input_path.is_file():
        print(f"❌ エラー: 入力パスがファイルではありません: {args.input}", file=sys.stderr)
        return False
    
    # 拡張子確認
    if input_path.suffix not in ['.c', '.h']:
        print(f"⚠️ 警告: 入力ファイルの拡張子が.cまたは.hではありません: {input_path.suffix}")
    
    # 設定ファイルの存在確認（指定されている場合）
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ エラー: 設定ファイルが見つかりません: {args.config}", file=sys.stderr)
            return False
    
    return True


def main():
    """メイン関数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # プリセット一覧表示モード
    if args.list_presets:
        from .model_preset_manager import ModelPresetManager
        manager = ModelPresetManager()
        manager.list_presets()
        sys.exit(0)
    
    # 設定ファイル作成モード
    if args.create_config:
        success = ConfigManager.create_default_config(args.create_config)
        sys.exit(0 if success else 1)
    
    # バッチ設定ファイル作成モード
    if args.create_batch_config:
        from .batch_processor import BatchProcessor
        BatchProcessor.create_batch_config_template(args.create_batch_config)
        sys.exit(0)
    
    # テンプレートファイル作成モード
    if args.create_templates:
        create_template_files(args.create_templates)
        sys.exit(0)
    
    # エラーハンドラーの初期化
    log_level = ErrorLevel[args.log_level] if hasattr(args, 'log_level') else ErrorLevel.INFO
    error_handler = ErrorHandler(log_level=log_level, log_file=args.log_file if hasattr(args, 'log_file') else None)
    
    # パフォーマンスモニターの初期化（オプション）
    perf_monitor = None
    mem_monitor = None
    result_cache = None
    
    if args.performance:
        perf_monitor = get_performance_monitor()
        mem_monitor = get_memory_monitor()
        error_handler.info("パフォーマンス監視を有効化しました")
    
    # キャッシュの初期化
    if not args.no_cache:
        result_cache = get_result_cache()
        error_handler.info("結果キャッシュを有効化しました")
    
    # テンプレート一覧表示モード
    if args.list_templates:
        template_engine = TemplateEngine(template_dir=args.template_dir if hasattr(args, 'template_dir') else None)
        print("\n利用可能なテンプレート:")
        for template_name in template_engine.list_templates():
            print(f"  - {template_name}")
        sys.exit(0)
    
    # 引数検証
    if not validate_args(args):
        sys.exit(1)
    
    # ヘッダー表示
    print("=" * 70)
    print(f"C言語単体テスト自動生成ツール v{VERSION}")
    print("=" * 70)
    print()
    
    # 設定読み込み
    config_manager = ConfigManager(args.config)
    config = config_manager.load()
    
    # マクロ定義を収集
    config_dict = config.to_dict()
    defines = {}
    
    # --presetオプションからマクロ定義を取得
    if hasattr(args, 'preset') and args.preset:
        from .model_preset_manager import ModelPresetManager
        preset_manager = ModelPresetManager()
        preset_defines = preset_manager.get_preset(args.preset)
        if preset_defines:
            defines.update(preset_defines)
            error_handler.info(f"プリセット '{args.preset}' を適用: {list(preset_defines.keys())}")
        else:
            sys.exit(1)
    
    # -Dオプションからマクロ定義を抽出（プリセットを上書き）
    if hasattr(args, 'define') and args.define:
        for define_str in args.define:
            if '=' in define_str:
                # -D MACRO=VALUE 形式
                name, value = define_str.split('=', 1)
                defines[name.strip()] = value.strip()
            else:
                # -D MACRO 形式（値なし → 1として定義）
                defines[define_str.strip()] = '1'
        
        error_handler.info(f"追加のマクロ定義: {list(args.define)}")
    
    # configに設定
    if defines:
        config_dict['defines'] = defines
        error_handler.info(f"最終的なマクロ定義: {defines}")
    
    # -Iオプションからインクルードパスを抽出
    include_paths = []
    if hasattr(args, 'include_path') and args.include_path:
        include_paths = args.include_path
        config_dict['include_paths'] = include_paths
        error_handler.info(f"インクルードパス: {include_paths}")
    
    # --enable-includesオプション
    if hasattr(args, 'enable_includes') and args.enable_includes:
        config_dict['enable_includes'] = True
        error_handler.info("ヘッダーファイル読み込みを有効化")
        if not include_paths:
            error_handler.info("インクルードパスが指定されていないため、カレントディレクトリのみを検索します")
    
    # v2.2: --include-target-functionオプション
    if hasattr(args, 'include_target_function'):
        config_dict['include_target_function'] = args.include_target_function
        if args.include_target_function:
            error_handler.info("v2.2: テスト対象関数の本体をテストコードに含めます")
        else:
            error_handler.info("v2.2: テスト対象関数の本体をテストコードに含めません")
    
    # v2.4.3: --no-standaloneオプション
    if hasattr(args, 'no_standalone') and args.no_standalone:
        config_dict['standalone_mode'] = False
        error_handler.info("v2.4.3: スタンドアロンモードを無効化（元のソースとテストコードを分離）")
    else:
        config_dict['standalone_mode'] = True
        error_handler.info("v2.4.3: スタンドアロンモード（元のソースファイルにテストコードを追加）")
    
    # 生成器初期化
    generator = CTestAutoGenerator(config=config_dict)
    
    # パフォーマンス監視を生成器に設定
    if perf_monitor:
        generator.performance_monitor = perf_monitor
    if mem_monitor:
        generator.memory_monitor = mem_monitor
    if result_cache:
        generator.result_cache = result_cache
    
    try:
        # バッチ処理モード
        if args.batch or args.batch_dir:
            error_handler.info("バッチ処理モードで実行します")
            
            batch_processor = BatchProcessor(
                generator=generator,
                error_handler=error_handler,
                max_workers=args.workers,
                continue_on_error=args.continue_on_error
            )
            
            if args.batch:
                # バッチ設定ファイルから処理
                items = batch_processor.load_batch_config(args.batch)
                results = batch_processor.process_batch(items, parallel=args.parallel)
            else:
                # ディレクトリを一括処理
                results = batch_processor.process_directory(
                    directory=args.batch_dir,
                    pattern=args.pattern,
                    output_base_dir=args.output,
                    parallel=args.parallel
                )
            
            # 結果を保存
            if args.save_results:
                batch_processor.save_results(args.save_results)
            
            # パフォーマンスメトリクスを表示
            if perf_monitor:
                perf_monitor.print_summary()
            if mem_monitor:
                mem_monitor.print_memory_status()
            
            success = all(r.success for r in results)
            sys.exit(0 if success else 1)
        
        # 通常モード（単一ファイル処理）
        # 入力ファイルの検証
        error_handler.validate_input_file(args.input)
        
        # 出力ディレクトリをユニーク化（番号付加）
        from pathlib import Path
        
        def get_unique_output_dir_cli(base_dir):
            """既存ディレクトリがある場合、(1), (2)... と番号を付加"""
            base_path = Path(base_dir)
            if not base_path.exists():
                return base_path
            counter = 1
            while True:
                new_path = Path(f"{base_dir}({counter})")
                if not new_path.exists():
                    return new_path
                counter += 1
                if counter > 1000:
                    raise RuntimeError(f"出力ディレクトリの番号が1000を超えました")
        
        # ユニークな出力ディレクトリを取得
        original_output = args.output
        unique_output = get_unique_output_dir_cli(args.output)
        
        if str(unique_output) != original_output:
            print(f"📁 既存ディレクトリを検出: 出力先を '{unique_output}' に変更しました")
        
        # args.outputをユニーク化したパスに更新
        args.output = str(unique_output)
        
        # 出力ディレクトリの検証（上書き制御）
        force_overwrite = getattr(args, 'overwrite', False)
        no_overwrite = getattr(args, 'no_overwrite', False)
        
        # 矛盾するオプションのチェック
        if force_overwrite and no_overwrite:
            print("❌ エラー: --overwrite と --no-overwrite は同時に指定できません", file=sys.stderr)
            sys.exit(1)
        
        error_handler.validate_output_dir(
            args.output, 
            check_existing=True, 
            force_overwrite=force_overwrite
        )
        
        # 個別ファイルの上書きチェック用に保存
        generator.no_overwrite = no_overwrite
        
        # 生成モード判定と実行
        if args.truth_only:
            # 真偽表のみ
            print("📊 モード: 真偽表のみ生成")
            output_path = Path(args.output) / (args.truth_table or f"{Path(args.input).stem}_{args.function}_truth_table.xlsx")
            result = generator.generate_truth_table_only(
                c_file_path=args.input,
                target_function=args.function,
                output_path=str(output_path)
            )
        
        elif args.test_only:
            # テストコードのみ
            print("🧪 モード: テストコードのみ生成")
            output_path = Path(args.output) / (args.test_code or f"test_{Path(args.input).stem}_{args.function}.c")
            result = generator.generate_test_code_only(
                c_file_path=args.input,
                target_function=args.function,
                output_path=str(output_path)
            )
        
        elif args.io_only:
            # I/O表のみ
            print("📝 モード: I/O表のみ生成")
            output_path = Path(args.output) / (args.io_table or f"{Path(args.input).stem}_{args.function}_io_table.xlsx")
            result = generator.generate_io_table_only(
                c_file_path=args.input,
                target_function=args.function,
                output_path=str(output_path)
            )
        
        else:
            # すべて生成（デフォルト）
            print("🎯 モード: すべて生成（真偽表、テストコード、I/O表）")
            result = generator.generate_all(
                c_file_path=args.input,
                target_function=args.function,
                output_dir=args.output,
                truth_table_name=args.truth_table,
                test_code_name=args.test_code,
                io_table_name=args.io_table
            )
        
        # 結果表示
        print()
        print("=" * 70)
        print(result)
        print("=" * 70)
        
        # パフォーマンスメトリクスを表示
        if perf_monitor:
            perf_monitor.print_summary()
        if mem_monitor:
            mem_monitor.print_memory_status()
        
        # エラーサマリーを表示
        if error_handler.error_history:
            print(error_handler.get_error_summary())
        
        sys.exit(0 if result.success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました")
        sys.exit(130)
    
    except Exception as e:
        error_handler.error(f"予期しないエラーが発生しました: {str(e)}")
        
        # エラーコンテキストを作成
        from .error_handler import ErrorContext, ErrorCode, GeneratorError
        
        if isinstance(e, GeneratorError):
            print(f"\n{e}", file=sys.stderr)
        else:
            context = ErrorContext(
                file_path=args.input if hasattr(args, 'input') and args.input else None,
                function_name=args.function if hasattr(args, 'function') and args.function else None,
                operation="main"
            )
            
            gen_error = GeneratorError(
                message=str(e),
                error_code=ErrorCode.UNKNOWN_ERROR,
                context=context,
                original_error=e
            )
            print(f"\n{gen_error}", file=sys.stderr)
        
        if args.verbose:
            import traceback
            traceback.print_exc()
        
        # エラーサマリーを表示
        if error_handler.error_history:
            print(error_handler.get_error_summary())
        
        sys.exit(1)


if __name__ == '__main__':
    main()
