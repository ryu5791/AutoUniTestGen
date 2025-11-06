"""
Preprocessorモジュール

C言語ソースコードの前処理を行う
- コメント削除
- #define展開（基本）
- 不要な#include削除
"""

import re
import sys
import os
from typing import Dict, List, Tuple

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class Preprocessor:
    """C言語プリプロセッサ"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.defines: Dict[str, str] = {}
        self.include_paths: List[str] = []
    
    def preprocess(self, code: str) -> str:
        """
        前処理を実行
        
        Args:
            code: C言語ソースコード
        
        Returns:
            前処理済みコード
        """
        self.logger.info("前処理を開始")
        
        # 1. #include処理（削除または保持）
        code = self._handle_includes(code)
        
        # 2. #define処理
        code = self._process_defines(code)
        
        # 3. その他のプリプロセッサディレクティブの処理
        code = self._process_other_directives(code)
        
        # 4. コメント削除（最後に実行）
        code = self._remove_comments(code)
        
        self.logger.info("前処理が完了")
        return code
    
    def _remove_comments(self, code: str) -> str:
        """
        コメントを削除
        
        Args:
            code: ソースコード
        
        Returns:
            コメント削除後のコード
        """
        # 複数行コメント /* ... */ を削除
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # 単一行コメント // ... を削除
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        
        return code
    
    def _process_defines(self, code: str) -> str:
        """
        #define を処理
        
        Args:
            code: ソースコード
        
        Returns:
            #define処理後のコード
        """
        lines = code.split('\n')
        processed_lines = []
        
        for line in lines:
            # #define の検出
            define_match = re.match(r'^\s*#define\s+(\w+)\s+(.*?)$', line)
            
            if define_match:
                macro_name = define_match.group(1)
                macro_value = define_match.group(2).strip()
                
                # マクロを辞書に保存
                self.defines[macro_name] = macro_value
                
                # #define行は残す（pycparserが必要とする場合があるため）
                processed_lines.append(line)
            else:
                # #defineでない行はそのまま
                processed_lines.append(line)
        
        code = '\n'.join(processed_lines)
        
        # マクロ展開（基本的なもののみ）
        for macro_name, macro_value in self.defines.items():
            # 単純な置換のみ（複雑なマクロは未対応）
            pattern = r'\b' + re.escape(macro_name) + r'\b'
            code = re.sub(pattern, macro_value, code)
        
        return code
    
    def _handle_includes(self, code: str) -> str:
        """
        #include を処理
        
        Args:
            code: ソースコード
        
        Returns:
            #include処理後のコード
        """
        lines = code.split('\n')
        processed_lines = []
        
        for line in lines:
            # #include の検出
            include_match = re.match(r'^\s*#include\s+[<"](.+?)[>"]', line)
            
            if include_match:
                # すべての#includeをコメントアウト
                # pycparserは#includeディレクティブをサポートしない
                processed_lines.append(f"/* {line} */")
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _is_standard_header(self, header: str) -> bool:
        """
        標準ヘッダかどうかを判定
        
        Args:
            header: ヘッダファイル名
        
        Returns:
            標準ヘッダならTrue
        """
        standard_headers = [
            'stdio.h', 'stdlib.h', 'string.h', 'stdint.h', 'stdbool.h',
            'limits.h', 'stddef.h', 'math.h', 'time.h', 'assert.h',
            'ctype.h', 'errno.h', 'float.h', 'setjmp.h', 'signal.h',
            'stdarg.h', 'unistd.h'
        ]
        
        return header in standard_headers
    
    def _process_other_directives(self, code: str) -> str:
        """
        その他のプリプロセッサディレクティブを処理
        
        Args:
            code: ソースコード
        
        Returns:
            処理後のコード
        """
        lines = code.split('\n')
        processed_lines = []
        skip_block = False
        
        for line in lines:
            # #ifdef, #ifndef, #if の検出
            if re.match(r'^\s*#(ifdef|ifndef|if)\s+', line):
                # 条件コンパイルブロックの開始
                # 簡易的にすべて有効として扱う
                processed_lines.append(f"// {line}")
                continue
            
            # #else の検出
            if re.match(r'^\s*#else\s*$', line):
                processed_lines.append(f"// {line}")
                continue
            
            # #endif の検出
            if re.match(r'^\s*#endif\s*', line):
                processed_lines.append(f"// {line}")
                continue
            
            # #pragma の検出
            if re.match(r'^\s*#pragma\s+', line):
                processed_lines.append(f"// {line}")
                continue
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def add_define(self, name: str, value: str) -> None:
        """
        #defineを追加
        
        Args:
            name: マクロ名
            value: マクロ値
        """
        self.defines[name] = value
    
    def get_defines(self) -> Dict[str, str]:
        """
        定義されたマクロを取得
        
        Returns:
            マクロ辞書
        """
        return self.defines.copy()


if __name__ == "__main__":
    # Preprocessorのテスト
    print("=== Preprocessor のテスト ===\n")
    
    # テスト用サンプルコード
    sample_code = """
/* 複数行
   コメント */
#include <stdio.h>
#include "custom_header.h"

#define MAX_VALUE 100
#define MIN_VALUE 0

// 単一行コメント
int main() {
    int value = MAX_VALUE;  // MAX_VALUEを使用
    if (value > MIN_VALUE) {
        printf("OK\\n");
    }
    return 0;
}

#ifdef DEBUG
void debug_func() {
    // デバッグ用関数
}
#endif
"""
    
    preprocessor = Preprocessor()
    processed = preprocessor.preprocess(sample_code)
    
    print("処理後のコード:")
    print("=" * 60)
    print(processed)
    print("=" * 60)
    
    print(f"\n定義されたマクロ: {preprocessor.get_defines()}")
    print("\n✓ Preprocessorが正常に動作しました")
