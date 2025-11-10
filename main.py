#!/usr/bin/env python3
"""
C言語単体テスト自動生成ツール - メインエントリーポイント

使用方法:
    python main.py -i sample.c -f calculate -o output
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.cli import main

if __name__ == '__main__':
    main()
