"""
ユーティリティモジュール

共通で使用するヘルパー関数を提供
"""

import os
import logging
import re
from typing import Optional, List
from pathlib import Path


# ロギング設定
def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    ロガーをセットアップ
    
    Args:
        name: ロガー名
        level: ログレベル
    
    Returns:
        設定済みLogger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 既にハンドラが設定されている場合はスキップ
    if logger.handlers:
        return logger
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # フォーマッタ
    formatter = logging.Formatter(
        '[%(levelname)s] %(asctime)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


# ファイルI/O
def read_file(filepath: str, encoding: str = 'utf-8') -> str:
    """
    ファイルを読み込む（自動エンコーディング検出対応）
    
    Args:
        filepath: ファイルパス
        encoding: エンコーディング（'auto'の場合は自動検出）
    
    Returns:
        ファイル内容
    
    Raises:
        FileNotFoundError: ファイルが存在しない
        IOError: 読み込みエラー
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")
    
    # エンコーディングが'auto'でない場合は指定されたエンコーディングを使用
    if encoding != 'auto':
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError as e:
            # UTF-8で失敗した場合、自動検出にフォールバック
            logger = setup_logger(__name__)
            logger.warning(f"指定されたエンコーディング({encoding})での読み込みに失敗。自動検出を試みます。")
        except Exception as e:
            raise IOError(f"ファイル読み込みエラー: {filepath} - {str(e)}")
    
    # 自動エンコーディング検出
    # 日本語環境でよく使われるエンコーディングを優先順に試行
    encodings_to_try = [
        'utf-8',           # UTF-8（標準）
        'cp932',           # Windows日本語（Shift-JIS拡張）
        'shift-jis',       # Shift-JIS
        'euc-jp',          # EUC-JP
        'iso-2022-jp',     # JIS
        'utf-16',          # UTF-16
        'latin-1',         # Latin-1（バイナリセーフ）
    ]
    
    last_error = None
    for enc in encodings_to_try:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                # 成功した場合、使用したエンコーディングをログ出力
                if enc != 'utf-8':
                    logger = setup_logger(__name__)
                    logger.info(f"ファイルを {enc} として読み込みました: {filepath}")
                return content
        except UnicodeDecodeError:
            last_error = f"エンコーディング {enc} での読み込みに失敗"
            continue
        except Exception as e:
            last_error = str(e)
            continue
    
    # すべてのエンコーディングで失敗した場合
    raise IOError(
        f"ファイル読み込みエラー: {filepath}\n"
        f"試行したエンコーディング: {', '.join(encodings_to_try)}\n"
        f"最後のエラー: {last_error}"
    )


def write_file(filepath: str, content: str, encoding: str = 'utf-8') -> None:
    """
    ファイルに書き込む
    
    Args:
        filepath: ファイルパス
        content: 書き込み内容
        encoding: エンコーディング
    
    Raises:
        IOError: 書き込みエラー
    """
    try:
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"ファイル書き込みエラー: {filepath} - {str(e)}")


def ensure_directory(dirpath: str) -> None:
    """
    ディレクトリが存在することを保証（なければ作成）
    
    Args:
        dirpath: ディレクトリパス
    """
    os.makedirs(dirpath, exist_ok=True)


# 文字列処理
def sanitize_identifier(name: str) -> str:
    """
    識別子として有効な文字列に変換
    
    Args:
        name: 変換前の文字列
    
    Returns:
        有効な識別子
    """
    # 英数字とアンダースコア以外を削除
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    # 先頭が数字の場合は'_'を追加
    if sanitized and sanitized[0].isdigit():
        sanitized = '_' + sanitized
    
    return sanitized


def extract_function_name(expression: str) -> Optional[str]:
    """
    式から関数名を抽出
    
    Args:
        expression: C言語の式
    
    Returns:
        関数名（見つからない場合はNone）
    
    Examples:
        >>> extract_function_name("f4() & 0xdf")
        'f4'
        >>> extract_function_name("mx27()")
        'mx27'
    """
    # 関数呼び出しパターン
    pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    matches = re.findall(pattern, expression)
    
    return matches[0] if matches else None


def extract_all_function_names(expression: str) -> List[str]:
    """
    式からすべての関数名を抽出
    
    Args:
        expression: C言語の式
    
    Returns:
        関数名のリスト
    """
    pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    return re.findall(pattern, expression)


def remove_whitespace(code: str) -> str:
    """
    不要な空白を削除
    
    Args:
        code: コード文字列
    
    Returns:
        整形後のコード
    """
    # 連続する空白を1つに
    code = re.sub(r'[ \t]+', ' ', code)
    
    # 連続する改行を2つまでに
    code = re.sub(r'\n\n\n+', '\n\n', code)
    
    return code.strip()


def normalize_condition(condition: str) -> str:
    """
    条件式を正規化
    
    Args:
        condition: 条件式
    
    Returns:
        正規化された条件式
    """
    # 不要な括弧や空白を整理
    normalized = condition.strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


# パス操作
def get_relative_path(filepath: str, base_dir: str) -> str:
    """
    相対パスを取得
    
    Args:
        filepath: ファイルパス
        base_dir: 基準ディレクトリ
    
    Returns:
        相対パス
    """
    return os.path.relpath(filepath, base_dir)


def get_file_basename(filepath: str) -> str:
    """
    拡張子を除いたファイル名を取得
    
    Args:
        filepath: ファイルパス
    
    Returns:
        ファイル名（拡張子なし）
    """
    return os.path.splitext(os.path.basename(filepath))[0]


# バリデーション
def validate_c_file(filepath: str) -> bool:
    """
    C言語ファイルかどうかを検証
    
    Args:
        filepath: ファイルパス
    
    Returns:
        C言語ファイルならTrue
    """
    if not os.path.exists(filepath):
        return False
    
    # 拡張子チェック
    ext = os.path.splitext(filepath)[1].lower()
    return ext in ['.c', '.h']


def validate_output_directory(dirpath: str) -> bool:
    """
    出力ディレクトリが有効かどうかを検証
    
    Args:
        dirpath: ディレクトリパス
    
    Returns:
        有効ならTrue
    """
    # ディレクトリが存在しない場合は作成可能かチェック
    if not os.path.exists(dirpath):
        try:
            os.makedirs(dirpath, exist_ok=True)
            return True
        except:
            return False
    
    # 書き込み可能かチェック
    return os.access(dirpath, os.W_OK)


class ProgressReporter:
    """進捗レポーター"""
    
    def __init__(self, total_steps: int = 100, logger: Optional[logging.Logger] = None):
        """
        初期化
        
        Args:
            total_steps: 総ステップ数
            logger: ロガー
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.logger = logger or setup_logger()
    
    def step(self, message: str = "") -> None:
        """
        1ステップ進める
        
        Args:
            message: 進捗メッセージ
        """
        self.current_step += 1
        progress = (self.current_step / self.total_steps) * 100
        
        msg = f"[{progress:5.1f}%] {message}" if message else f"[{progress:5.1f}%]"
        self.logger.info(msg)
    
    def complete(self, message: str = "完了") -> None:
        """完了を通知"""
        self.logger.info(f"[100.0%] {message}")


if __name__ == "__main__":
    # ユーティリティ関数のテスト
    print("=== ユーティリティ関数のテスト ===\n")
    
    # ロガーのテスト
    logger = setup_logger("test_logger")
    logger.info("ロガーのテスト")
    
    # 識別子のサニタイズ
    print(f"sanitize_identifier('test-func'): {sanitize_identifier('test-func')}")
    print(f"sanitize_identifier('123test'): {sanitize_identifier('123test')}")
    
    # 関数名抽出
    print(f"\nextract_function_name('f4() & 0xdf'): {extract_function_name('f4() & 0xdf')}")
    print(f"extract_all_function_names('if (f4() && mx27())'): {extract_all_function_names('if (f4() && mx27())')}")
    
    # 条件式の正規化
    print(f"\nnormalize_condition('  ( a  ==  b )  '): {normalize_condition('  ( a  ==  b )  ')}")
    
    # 進捗レポーター
    print("\n進捗レポーターのテスト:")
    reporter = ProgressReporter(total_steps=5, logger=logger)
    for i in range(5):
        reporter.step(f"ステップ{i+1}")
    reporter.complete()
    
    print("\n✓ ユーティリティ関数が正常に動作しました")
