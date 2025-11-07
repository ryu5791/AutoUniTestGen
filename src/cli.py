#!/usr/bin/env python3
"""
C言語単体テスト自動生成ツール - CLIインターフェース

コマンドライン引数を処理してテスト生成を実行
"""

import argparse
import sys
from pathlib import Path

from .c_test_auto_generator import CTestAutoGenerator
from .config import ConfigManager


VERSION = "1.0.0"


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

  # バージョン表示
  %(prog)s --version
        """
    )
    
    # 必須引数
    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        metavar='FILE',
        help='入力するC言語ソースファイルパス (必須)'
    )
    
    parser.add_argument(
        '-f', '--function',
        type=str,
        required=True,
        metavar='FUNC',
        help='テスト対象関数名 (必須)'
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
        '-c', '--config',
        type=str,
        metavar='FILE',
        help='設定ファイルパス (JSON形式)'
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
    
    return parser


def validate_args(args: argparse.Namespace) -> bool:
    """
    引数を検証
    
    Args:
        args: パース済み引数
    
    Returns:
        bool: 検証成功したかどうか
    """
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
    
    # 設定ファイル作成モード
    if args.create_config:
        success = ConfigManager.create_default_config(args.create_config)
        sys.exit(0 if success else 1)
    
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
    
    # 生成器初期化
    generator = CTestAutoGenerator(config=config.to_dict())
    
    try:
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
        
        sys.exit(0 if result.success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
