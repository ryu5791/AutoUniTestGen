#!/usr/bin/env python3
"""
C言語単体テスト自動生成ツール - メインエントリーポイント

使用方法:
    python main.py -i sample.c -f calculate -o output
"""

import sys
import os
from pathlib import Path

# 現在のディレクトリとsrcディレクトリを確実にパスに追加
current_dir = Path(__file__).parent.resolve()
src_dir = current_dir / 'src'

# 両方のパスを追加（Windowsでも確実に動作するように）
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 環境変数PYTHONPATHにも追加（Windows対応）
os.environ['PYTHONPATH'] = str(current_dir) + os.pathsep + str(src_dir) + os.pathsep + os.environ.get('PYTHONPATH', '')

from src.cli import main

if __name__ == '__main__':
    main()
