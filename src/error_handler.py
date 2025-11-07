"""
エラーハンドリングモジュール

詳細なエラーメッセージ、リカバリー機能、ログレベル制御を提供します。
"""

import logging
import sys
import traceback
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass


class ErrorLevel(Enum):
    """エラーレベルの定義"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class ErrorCode(Enum):
    """エラーコードの定義"""
    # 入力エラー (1000番台)
    FILE_NOT_FOUND = 1001
    INVALID_FILE_FORMAT = 1002
    EMPTY_FILE = 1003
    PERMISSION_DENIED = 1004
    
    # 解析エラー (2000番台)
    PARSE_ERROR = 2001
    FUNCTION_NOT_FOUND = 2002
    INVALID_SYNTAX = 2003
    UNSUPPORTED_CONSTRUCT = 2004
    
    # 生成エラー (3000番台)
    GENERATION_ERROR = 3001
    TRUTH_TABLE_ERROR = 3002
    TEST_CODE_ERROR = 3003
    IO_TABLE_ERROR = 3004
    
    # 出力エラー (4000番台)
    OUTPUT_ERROR = 4001
    WRITE_ERROR = 4002
    EXCEL_ERROR = 4003
    
    # システムエラー (5000番台)
    MEMORY_ERROR = 5001
    TIMEOUT_ERROR = 5002
    UNKNOWN_ERROR = 5999


@dataclass
class ErrorContext:
    """エラーコンテキスト情報"""
    file_path: Optional[str] = None
    function_name: Optional[str] = None
    line_number: Optional[int] = None
    operation: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class GeneratorError(Exception):
    """ツール固有の例外クラス"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        context: Optional[ErrorContext] = None,
        recovery_hint: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or ErrorContext()
        self.recovery_hint = recovery_hint
        self.original_error = original_error
    
    def __str__(self) -> str:
        """詳細なエラーメッセージを生成"""
        parts = [f"[{self.error_code.name}] {self.message}"]
        
        # コンテキスト情報を追加
        if self.context.file_path:
            parts.append(f"  ファイル: {self.context.file_path}")
        if self.context.function_name:
            parts.append(f"  関数: {self.context.function_name}")
        if self.context.line_number:
            parts.append(f"  行番号: {self.context.line_number}")
        if self.context.operation:
            parts.append(f"  操作: {self.context.operation}")
        
        # リカバリーヒントを追加
        if self.recovery_hint:
            parts.append(f"\n💡 解決方法: {self.recovery_hint}")
        
        # 元の例外情報を追加
        if self.original_error:
            parts.append(f"\n原因: {type(self.original_error).__name__}: {str(self.original_error)}")
        
        return "\n".join(parts)


class ErrorHandler:
    """エラーハンドラークラス"""
    
    def __init__(self, log_level: ErrorLevel = ErrorLevel.INFO, log_file: Optional[str] = None):
        """
        初期化
        
        Args:
            log_level: ログレベル
            log_file: ログファイルパス（Noneの場合は標準エラー出力）
        """
        self.log_level = log_level
        self.log_file = log_file
        self._setup_logger()
        self.error_history = []
    
    def _setup_logger(self):
        """ロガーのセットアップ"""
        self.logger = logging.getLogger('CTestAutoGenerator')
        self.logger.setLevel(self.log_level.value)
        
        # 既存のハンドラーをクリア
        self.logger.handlers.clear()
        
        # フォーマッターの設定
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # ハンドラーの追加
        if self.log_file:
            # ファイルハンドラー
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        else:
            # コンソールハンドラー
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def set_log_level(self, level: ErrorLevel):
        """ログレベルを設定"""
        self.log_level = level
        self.logger.setLevel(level.value)
    
    def log(self, level: ErrorLevel, message: str, **kwargs):
        """ログを出力"""
        self.logger.log(level.value, message, **kwargs)
    
    def debug(self, message: str):
        """デバッグログ"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """情報ログ"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告ログ"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """エラーログ"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """致命的エラーログ"""
        self.logger.critical(message)
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        recovery_action: Optional[Callable] = None
    ) -> bool:
        """
        エラーを処理
        
        Args:
            error: 発生した例外
            context: エラーコンテキスト
            recovery_action: リカバリーアクション（関数）
        
        Returns:
            リカバリー成功時True、失敗時False
        """
        # GeneratorErrorの場合
        if isinstance(error, GeneratorError):
            self.error(str(error))
            self.error_history.append(error)
            
            # リカバリーアクションを試行
            if recovery_action:
                try:
                    self.info("リカバリーアクションを実行中...")
                    recovery_action()
                    self.info("リカバリー成功")
                    return True
                except Exception as e:
                    self.error(f"リカバリー失敗: {str(e)}")
                    return False
            return False
        
        # 一般的な例外の場合、GeneratorErrorに変換
        error_code = self._determine_error_code(error)
        generator_error = GeneratorError(
            message=str(error),
            error_code=error_code,
            context=context,
            recovery_hint=self._get_recovery_hint(error_code),
            original_error=error
        )
        
        return self.handle_error(generator_error, context, recovery_action)
    
    def _determine_error_code(self, error: Exception) -> ErrorCode:
        """例外からエラーコードを判定"""
        if isinstance(error, FileNotFoundError):
            return ErrorCode.FILE_NOT_FOUND
        elif isinstance(error, PermissionError):
            return ErrorCode.PERMISSION_DENIED
        elif isinstance(error, MemoryError):
            return ErrorCode.MEMORY_ERROR
        elif isinstance(error, TimeoutError):
            return ErrorCode.TIMEOUT_ERROR
        elif isinstance(error, (IOError, OSError)):
            return ErrorCode.OUTPUT_ERROR
        else:
            return ErrorCode.UNKNOWN_ERROR
    
    def _get_recovery_hint(self, error_code: ErrorCode) -> str:
        """エラーコードからリカバリーヒントを取得"""
        hints = {
            ErrorCode.FILE_NOT_FOUND: "ファイルパスが正しいか確認してください。",
            ErrorCode.INVALID_FILE_FORMAT: "ファイル形式がC言語ソースファイル(.c)であることを確認してください。",
            ErrorCode.EMPTY_FILE: "ファイルが空です。有効なC言語コードが含まれているか確認してください。",
            ErrorCode.PERMISSION_DENIED: "ファイルへのアクセス権限を確認してください。",
            ErrorCode.FUNCTION_NOT_FOUND: "指定された関数名が正しいか確認してください。関数が実際にファイル内に存在するか確認してください。",
            ErrorCode.PARSE_ERROR: "C言語の構文が正しいか確認してください。コンパイルエラーがないか確認してください。",
            ErrorCode.UNSUPPORTED_CONSTRUCT: "サポートされていないC言語構文が含まれています。よりシンプルな構文に書き換えてください。",
            ErrorCode.WRITE_ERROR: "出力ディレクトリへの書き込み権限を確認してください。ディスク容量が十分か確認してください。",
            ErrorCode.MEMORY_ERROR: "処理するファイルが大きすぎる可能性があります。より小さなファイルに分割してください。",
            ErrorCode.TIMEOUT_ERROR: "処理に時間がかかりすぎています。より小さなファイルまたはシンプルな関数で試してください。",
        }
        return hints.get(error_code, "詳細については、ドキュメントを参照するか、サポートにお問い合わせください。")
    
    def validate_input_file(self, file_path: str) -> bool:
        """
        入力ファイルの検証
        
        Args:
            file_path: ファイルパス
        
        Returns:
            検証成功時True
        
        Raises:
            GeneratorError: 検証失敗時
        """
        path = Path(file_path)
        
        # ファイルの存在確認
        if not path.exists():
            raise GeneratorError(
                f"ファイルが見つかりません: {file_path}",
                ErrorCode.FILE_NOT_FOUND,
                ErrorContext(file_path=file_path),
                recovery_hint="ファイルパスが正しいか確認してください。"
            )
        
        # ファイル形式の確認
        if path.suffix.lower() not in ['.c', '.h']:
            raise GeneratorError(
                f"サポートされていないファイル形式: {path.suffix}",
                ErrorCode.INVALID_FILE_FORMAT,
                ErrorContext(file_path=file_path),
                recovery_hint="C言語ソースファイル(.c)またはヘッダーファイル(.h)を指定してください。"
            )
        
        # ファイルサイズの確認
        if path.stat().st_size == 0:
            raise GeneratorError(
                f"ファイルが空です: {file_path}",
                ErrorCode.EMPTY_FILE,
                ErrorContext(file_path=file_path),
                recovery_hint="有効なC言語コードが含まれているファイルを指定してください。"
            )
        
        # 読み取り権限の確認
        if not path.is_file() or not path.stat().st_mode & 0o400:
            raise GeneratorError(
                f"ファイルの読み取り権限がありません: {file_path}",
                ErrorCode.PERMISSION_DENIED,
                ErrorContext(file_path=file_path),
                recovery_hint="ファイルの読み取り権限を確認してください。"
            )
        
        self.info(f"入力ファイル検証成功: {file_path}")
        return True
    
    def validate_output_dir(self, output_dir: str, check_existing: bool = True, 
                           force_overwrite: bool = False) -> bool:
        """
        出力ディレクトリの検証
        
        Args:
            output_dir: 出力ディレクトリパス
            check_existing: 既存ファイルをチェックするか
            force_overwrite: 強制上書きフラグ
        
        Returns:
            検証成功時True
        
        Raises:
            GeneratorError: 検証失敗時
        """
        path = Path(output_dir)
        
        # ディレクトリが存在しない場合は作成を試みる
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                self.info(f"出力ディレクトリを作成しました: {output_dir}")
            except Exception as e:
                raise GeneratorError(
                    f"出力ディレクトリの作成に失敗しました: {output_dir}",
                    ErrorCode.OUTPUT_ERROR,
                    ErrorContext(file_path=output_dir),
                    recovery_hint="親ディレクトリへの書き込み権限を確認してください。",
                    original_error=e
                )
        else:
            # ディレクトリが既に存在する場合
            if check_existing:
                # 既存ファイルをチェック
                existing_files = list(path.glob('*'))
                if existing_files:
                    if force_overwrite:
                        self.info(f"出力ディレクトリには {len(existing_files)} 個のファイルが存在しますが、上書きします")
                    else:
                        self.warning(f"⚠️  出力ディレクトリには既に {len(existing_files)} 個のファイルが存在します")
                        self.warning(f"   既存ファイルは上書きされる可能性があります")
                        self.warning(f"   上書きを防ぐには --no-overwrite オプションを使用してください")
                        self.warning(f"   強制上書きするには --overwrite オプションを使用してください")
        
        # 書き込み権限の確認
        if not path.is_dir() or not path.stat().st_mode & 0o200:
            raise GeneratorError(
                f"出力ディレクトリへの書き込み権限がありません: {output_dir}",
                ErrorCode.PERMISSION_DENIED,
                ErrorContext(file_path=output_dir),
                recovery_hint="ディレクトリの書き込み権限を確認してください。"
            )
        
        self.info(f"出力ディレクトリ検証成功: {output_dir}")
        return True
    
    def check_file_overwrite(self, file_path: str, no_overwrite: bool = False) -> bool:
        """
        ファイルの上書きをチェック
        
        Args:
            file_path: ファイルパス
            no_overwrite: 上書き禁止フラグ
        
        Returns:
            書き込み可能ならTrue
        
        Raises:
            GeneratorError: 上書き禁止で既存ファイルがある場合
        """
        path = Path(file_path)
        
        if path.exists():
            if no_overwrite:
                raise GeneratorError(
                    f"出力ファイルが既に存在します: {file_path}",
                    ErrorCode.OUTPUT_ERROR,
                    ErrorContext(file_path=file_path),
                    recovery_hint=(
                        "以下の対処方法があります:\n"
                        "1. 既存ファイルを削除または移動する\n"
                        "2. 別の出力ディレクトリを指定する (-o オプション)\n"
                        "3. --overwrite オプションで強制上書きする"
                    )
                )
            else:
                self.warning(f"⚠️  既存ファイルを上書きします: {file_path}")
        
        return True
    
    def get_error_summary(self) -> str:
        """エラー履歴のサマリーを取得"""
        if not self.error_history:
            return "エラーは発生していません。"
        
        summary = [f"\n{'='*60}"]
        summary.append(f"エラーサマリー: {len(self.error_history)}件のエラーが発生しました")
        summary.append('='*60)
        
        for i, error in enumerate(self.error_history, 1):
            summary.append(f"\n{i}. {error.error_code.name}")
            summary.append(f"   {error.message}")
            if error.context.file_path:
                summary.append(f"   ファイル: {error.context.file_path}")
        
        summary.append('='*60)
        return "\n".join(summary)


# グローバルエラーハンドラーのインスタンス
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """グローバルエラーハンドラーを取得"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def set_error_handler(handler: ErrorHandler):
    """グローバルエラーハンドラーを設定"""
    global _global_error_handler
    _global_error_handler = handler
