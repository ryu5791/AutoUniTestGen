"""
I/O表生成パッケージ

テストコードから入出力変数を抽出し、I/O一覧表を生成する。
"""

from .variable_extractor import VariableExtractor
from .io_table_generator import IOTableGenerator

__all__ = [
    'VariableExtractor',
    'IOTableGenerator',
]
