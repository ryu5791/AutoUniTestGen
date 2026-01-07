"""
出力エンコーディング設定モジュール

設定ファイルから出力エンコーディングを読み込み、全体で使用できるようにする
"""

import configparser
import sys
import os
from pathlib import Path
from typing import Optional

# グローバル変数（デフォルト値）
OUTPUT_ENCODING = "shift_jis"


def _get_config_path(config_name: str = "config.ini") -> str:
    """
    v4.8.1: PyInstaller対応の設定ファイルパス解決
    
    Args:
        config_name: 設定ファイル名
    
    Returns:
        設定ファイルのフルパス
    """
    if hasattr(sys, '_MEIPASS'):
        # exe実行時
        return os.path.join(sys._MEIPASS, config_name)
    else:
        # 通常実行時: カレントディレクトリを優先
        if Path(config_name).exists():
            return config_name
        # src/encoding_config.py -> ../config.ini
        return str(Path(__file__).resolve().parent.parent / config_name)


def load_encoding_config(config_path: str = None) -> str:
    """
    設定ファイルから出力エンコーディングを読み込む
    
    Args:
        config_path: 設定ファイルのパス（Noneの場合は自動解決）
    
    Returns:
        str: 出力エンコーディング
    """
    global OUTPUT_ENCODING
    
    if config_path is None:
        config_path = _get_config_path()
    
    if Path(config_path).exists():
        parser = configparser.ConfigParser()
        parser.read(config_path, encoding='utf-8')
        
        if parser.has_section('output') and parser.has_option('output', 'output_encoding'):
            OUTPUT_ENCODING = parser.get('output', 'output_encoding')
            print(f"📝 出力エンコーディング: {OUTPUT_ENCODING}")
    
    return OUTPUT_ENCODING


def get_output_encoding() -> str:
    """
    現在の出力エンコーディングを取得
    
    Returns:
        str: 出力エンコーディング
    """
    return OUTPUT_ENCODING


def set_output_encoding(encoding: str) -> None:
    """
    出力エンコーディングを設定
    
    Args:
        encoding: エンコーディング名
    """
    global OUTPUT_ENCODING
    OUTPUT_ENCODING = encoding


# モジュール読み込み時に自動的に設定を読み込む
load_encoding_config()
