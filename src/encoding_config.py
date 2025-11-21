"""
出力エンコーディング設定モジュール

設定ファイルから出力エンコーディングを読み込み、全体で使用できるようにする
"""

import configparser
from pathlib import Path
from typing import Optional

# グローバル変数（デフォルト値）
OUTPUT_ENCODING = "shift_jis"


def load_encoding_config(config_path: str = "config.ini") -> str:
    """
    設定ファイルから出力エンコーディングを読み込む
    
    Args:
        config_path: 設定ファイルのパス
    
    Returns:
        str: 出力エンコーディング
    """
    global OUTPUT_ENCODING
    
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
