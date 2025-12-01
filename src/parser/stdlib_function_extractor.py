"""
標準ライブラリ関数抽出モジュール（v4.0.1）

#includeで指定されたヘッダファイルから関数宣言を抽出し、
標準ライブラリ関数のリストを構築する。
"""

import os
import re
from typing import Set, List, Dict, Optional
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class StdlibFunctionExtractor:
    """標準ライブラリ関数抽出クラス"""
    
    # 標準ライブラリヘッダのリスト（これらのヘッダに含まれる関数はモック対象外）
    STDLIB_HEADERS = {
        'stdio.h', 'stdlib.h', 'string.h', 'math.h', 'ctype.h',
        'stdint.h', 'stdbool.h', 'stddef.h', 'limits.h', 'float.h',
        'time.h', 'errno.h', 'assert.h', 'signal.h', 'setjmp.h',
        'stdarg.h', 'locale.h', 'iso646.h', 'wchar.h', 'wctype.h',
        'complex.h', 'fenv.h', 'inttypes.h', 'stdalign.h', 'stdnoreturn.h',
        'tgmath.h', 'uchar.h', 'stdatomic.h', 'threads.h',
    }
    
    # フォールバック用：よく使われる標準ライブラリ関数
    FALLBACK_STDLIB_FUNCTIONS = {
        # stdlib.h
        'abs', 'labs', 'llabs', 'div', 'ldiv', 'lldiv',
        'atoi', 'atol', 'atoll', 'atof',
        'strtol', 'strtoll', 'strtoul', 'strtoull', 'strtod', 'strtof', 'strtold',
        'rand', 'srand',
        'malloc', 'calloc', 'realloc', 'free', 'aligned_alloc',
        'abort', 'exit', '_Exit', 'atexit', 'at_quick_exit', 'quick_exit',
        'getenv', 'system',
        'bsearch', 'qsort',
        'mblen', 'mbtowc', 'wctomb', 'mbstowcs', 'wcstombs',
        
        # string.h
        'memcpy', 'memmove', 'memset', 'memcmp', 'memchr',
        'strcpy', 'strncpy', 'strcat', 'strncat',
        'strcmp', 'strncmp', 'strcoll', 'strxfrm',
        'strchr', 'strrchr', 'strspn', 'strcspn', 'strpbrk', 'strstr', 'strtok',
        'strlen', 'strerror',
        
        # stdio.h
        'fopen', 'freopen', 'fclose', 'fflush',
        'setbuf', 'setvbuf',
        'fread', 'fwrite',
        'fgetc', 'getc', 'fgets', 'fputc', 'putc', 'fputs',
        'getchar', 'gets', 'putchar', 'puts',
        'ungetc',
        'scanf', 'fscanf', 'sscanf', 'vscanf', 'vfscanf', 'vsscanf',
        'printf', 'fprintf', 'sprintf', 'snprintf',
        'vprintf', 'vfprintf', 'vsprintf', 'vsnprintf',
        'fseek', 'ftell', 'rewind', 'fgetpos', 'fsetpos',
        'clearerr', 'feof', 'ferror', 'perror',
        'remove', 'rename', 'tmpfile', 'tmpnam',
        
        # math.h
        'fabs', 'fabsf', 'fabsl',
        'fmod', 'fmodf', 'fmodl', 'remainder', 'remainderf', 'remainderl',
        'fma', 'fmaf', 'fmal',
        'fmax', 'fmaxf', 'fmaxl', 'fmin', 'fminf', 'fminl', 'fdim', 'fdimf', 'fdiml',
        'exp', 'expf', 'expl', 'exp2', 'exp2f', 'exp2l', 'expm1', 'expm1f', 'expm1l',
        'log', 'logf', 'logl', 'log10', 'log10f', 'log10l', 'log2', 'log2f', 'log2l',
        'log1p', 'log1pf', 'log1pl',
        'pow', 'powf', 'powl', 'sqrt', 'sqrtf', 'sqrtl', 'cbrt', 'cbrtf', 'cbrtl',
        'hypot', 'hypotf', 'hypotl',
        'sin', 'sinf', 'sinl', 'cos', 'cosf', 'cosl', 'tan', 'tanf', 'tanl',
        'asin', 'asinf', 'asinl', 'acos', 'acosf', 'acosl', 'atan', 'atanf', 'atanl',
        'atan2', 'atan2f', 'atan2l',
        'sinh', 'sinhf', 'sinhl', 'cosh', 'coshf', 'coshl', 'tanh', 'tanhf', 'tanhl',
        'asinh', 'asinhf', 'asinhl', 'acosh', 'acoshf', 'acoshl', 'atanh', 'atanhf', 'atanhl',
        'ceil', 'ceilf', 'ceill', 'floor', 'floorf', 'floorl',
        'trunc', 'truncf', 'truncl', 'round', 'roundf', 'roundl',
        'lround', 'lroundf', 'lroundl', 'llround', 'llroundf', 'llroundl',
        'nearbyint', 'nearbyintf', 'nearbyintl', 'rint', 'rintf', 'rintl',
        'lrint', 'lrintf', 'lrintl', 'llrint', 'llrintf', 'llrintl',
        'frexp', 'frexpf', 'frexpl', 'ldexp', 'ldexpf', 'ldexpl',
        'modf', 'modff', 'modfl', 'scalbn', 'scalbnf', 'scalbnl',
        'ilogb', 'ilogbf', 'ilogbl', 'logb', 'logbf', 'logbl',
        'copysign', 'copysignf', 'copysignl',
        'nan', 'nanf', 'nanl',
        'nextafter', 'nextafterf', 'nextafterl', 'nexttoward', 'nexttowardf', 'nexttowardl',
        'isnan', 'isinf', 'isfinite', 'isnormal', 'signbit',
        'fpclassify',
        'erf', 'erff', 'erfl', 'erfc', 'erfcf', 'erfcl',
        'lgamma', 'lgammaf', 'lgammal', 'tgamma', 'tgammaf', 'tgammal',
        
        # ctype.h
        'isalnum', 'isalpha', 'isblank', 'iscntrl', 'isdigit', 'isgraph',
        'islower', 'isprint', 'ispunct', 'isspace', 'isupper', 'isxdigit',
        'tolower', 'toupper',
        
        # time.h
        'clock', 'time', 'difftime', 'mktime',
        'asctime', 'ctime', 'gmtime', 'localtime', 'strftime',
        
        # assert.h
        'assert',
        
        # setjmp.h
        'setjmp', 'longjmp',
        
        # signal.h
        'signal', 'raise',
    }
    
    # システムのインクルードパス候補
    SYSTEM_INCLUDE_PATHS = [
        '/usr/include',
        '/usr/local/include',
        '/usr/include/x86_64-linux-gnu',
        '/usr/lib/gcc/x86_64-linux-gnu/*/include',
        'C:/MinGW/include',
        'C:/Program Files/Microsoft Visual Studio/*/VC/include',
    ]
    
    def __init__(self, additional_include_paths: List[str] = None):
        """
        初期化
        
        Args:
            additional_include_paths: 追加のインクルードパス
        """
        self.logger = setup_logger(__name__)
        self.include_paths = list(additional_include_paths or [])
        
        # システムインクルードパスを追加
        for path in self.SYSTEM_INCLUDE_PATHS:
            if '*' in path:
                # ワイルドカード展開
                import glob
                expanded = glob.glob(path)
                self.include_paths.extend(expanded)
            elif os.path.isdir(path):
                self.include_paths.append(path)
        
        # キャッシュ
        self._header_functions_cache: Dict[str, Set[str]] = {}
        self._stdlib_functions: Optional[Set[str]] = None
    
    def extract_includes_from_source(self, source_code: str) -> List[str]:
        """
        ソースコードから#includeディレクティブを抽出
        
        Args:
            source_code: ソースコード
        
        Returns:
            インクルードされているヘッダファイル名のリスト
        """
        includes = []
        
        # #include <header.h> または #include "header.h" にマッチ
        pattern = r'#\s*include\s*[<"]([^>"]+)[>"]'
        
        for match in re.finditer(pattern, source_code):
            header = match.group(1)
            includes.append(header)
        
        return includes
    
    def find_header_file(self, header_name: str) -> Optional[str]:
        """
        ヘッダファイルのフルパスを検索
        
        Args:
            header_name: ヘッダファイル名
        
        Returns:
            見つかった場合はフルパス、なければNone
        """
        for include_path in self.include_paths:
            full_path = os.path.join(include_path, header_name)
            if os.path.isfile(full_path):
                return full_path
        return None
    
    def extract_functions_from_header(self, header_path: str) -> Set[str]:
        """
        ヘッダファイルから関数宣言を抽出
        
        Args:
            header_path: ヘッダファイルのパス
        
        Returns:
            関数名のセット
        """
        # キャッシュチェック
        if header_path in self._header_functions_cache:
            return self._header_functions_cache[header_path]
        
        functions = set()
        
        try:
            with open(header_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # プリプロセッサディレクティブとコメントを除去
            content = self._remove_comments(content)
            
            # 関数宣言パターン
            # 戻り値型 関数名(パラメータ);
            # extern 戻り値型 関数名(パラメータ);
            pattern = r'''
                (?:extern\s+)?                      # extern（オプション）
                (?:static\s+)?                      # static（オプション）
                (?:inline\s+)?                      # inline（オプション）
                (?:__\w+\s+)*                       # __attribute__等（オプション）
                [\w\s\*]+?                          # 戻り値型
                \s+(\w+)                            # 関数名（キャプチャ）
                \s*\([^)]*\)                        # パラメータ
                \s*(?:__\w+\s*\([^)]*\))*           # __attribute__等（オプション）
                \s*;                                # セミコロン
            '''
            
            for match in re.finditer(pattern, content, re.VERBOSE | re.MULTILINE):
                func_name = match.group(1)
                # キーワードや型名を除外
                if not self._is_keyword_or_type(func_name):
                    functions.add(func_name)
            
            self.logger.debug(f"ヘッダ {header_path} から {len(functions)} 個の関数を抽出")
            
        except Exception as e:
            self.logger.warning(f"ヘッダファイル読み込みエラー: {header_path}: {e}")
        
        # キャッシュに保存
        self._header_functions_cache[header_path] = functions
        return functions
    
    def _remove_comments(self, code: str) -> str:
        """コメントを除去"""
        # /* */ コメント
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # // コメント
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        return code
    
    def _is_keyword_or_type(self, name: str) -> bool:
        """キーワードまたは型名かどうかをチェック"""
        keywords = {
            'if', 'else', 'while', 'for', 'do', 'switch', 'case', 'default',
            'break', 'continue', 'return', 'goto',
            'struct', 'union', 'enum', 'typedef',
            'int', 'char', 'short', 'long', 'float', 'double', 'void',
            'signed', 'unsigned', 'const', 'volatile', 'static', 'extern',
            'register', 'auto', 'inline', 'restrict',
            'sizeof', 'typeof',
        }
        return name in keywords
    
    def get_stdlib_functions_from_source(self, source_code: str) -> Set[str]:
        """
        ソースコードの#includeを解析し、標準ライブラリ関数のリストを取得
        
        Args:
            source_code: ソースコード
        
        Returns:
            標準ライブラリ関数名のセット
        """
        stdlib_functions = set()
        
        # ソースコードからインクルードを抽出
        includes = self.extract_includes_from_source(source_code)
        self.logger.info(f"検出された#include: {len(includes)}個")
        
        for header in includes:
            # 標準ライブラリヘッダかチェック
            header_basename = os.path.basename(header)
            if header_basename in self.STDLIB_HEADERS:
                self.logger.debug(f"標準ライブラリヘッダ検出: {header}")
                
                # ヘッダファイルを検索
                header_path = self.find_header_file(header)
                if header_path:
                    # ヘッダから関数を抽出
                    functions = self.extract_functions_from_header(header_path)
                    stdlib_functions.update(functions)
                    self.logger.info(f"  {header}: {len(functions)}個の関数を抽出")
                else:
                    self.logger.debug(f"  {header}: ヘッダファイルが見つかりません（フォールバック使用）")
        
        # フォールバック関数を追加
        stdlib_functions.update(self.FALLBACK_STDLIB_FUNCTIONS)
        
        return stdlib_functions
    
    def is_stdlib_function(self, func_name: str, source_code: str = None) -> bool:
        """
        関数が標準ライブラリ関数かどうかを判定
        
        Args:
            func_name: 関数名
            source_code: ソースコード（Noneの場合はフォールバックリストのみ使用）
        
        Returns:
            標準ライブラリ関数の場合True
        """
        # フォールバックリストでまずチェック
        if func_name in self.FALLBACK_STDLIB_FUNCTIONS:
            return True
        
        # ソースコードがある場合はインクルードを解析
        if source_code:
            if self._stdlib_functions is None:
                self._stdlib_functions = self.get_stdlib_functions_from_source(source_code)
            return func_name in self._stdlib_functions
        
        return False
    
    def filter_external_functions(self, external_functions: List[str], 
                                   source_code: str = None) -> List[str]:
        """
        外部関数リストから標準ライブラリ関数を除外
        
        Args:
            external_functions: 外部関数リスト
            source_code: ソースコード
        
        Returns:
            フィルタリングされた外部関数リスト
        """
        filtered = []
        excluded = []
        
        for func_name in external_functions:
            if self.is_stdlib_function(func_name, source_code):
                excluded.append(func_name)
            else:
                filtered.append(func_name)
        
        if excluded:
            self.logger.info(f"標準ライブラリ関数を除外: {excluded}")
        
        return filtered


# テスト用
if __name__ == "__main__":
    print("=" * 70)
    print("StdlibFunctionExtractor テスト")
    print("=" * 70)
    
    extractor = StdlibFunctionExtractor()
    
    # テスト用ソースコード
    test_source = '''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "my_header.h"

int main(void) {
    int x = abs(-5);
    double y = sqrt(2.0);
    char *s = malloc(100);
    memset(s, 0, 100);
    printf("Hello\\n");
    my_custom_function();
    return 0;
}
'''
    
    # インクルードを抽出
    includes = extractor.extract_includes_from_source(test_source)
    print(f"\n検出された#include: {includes}")
    
    # 標準ライブラリ関数を取得
    stdlib_funcs = extractor.get_stdlib_functions_from_source(test_source)
    print(f"\n標準ライブラリ関数数: {len(stdlib_funcs)}")
    print(f"サンプル: {list(stdlib_funcs)[:20]}...")
    
    # フィルタリングテスト
    external_funcs = ['abs', 'sqrt', 'malloc', 'memset', 'printf', 'my_custom_function', 'Utf8']
    filtered = extractor.filter_external_functions(external_funcs, test_source)
    print(f"\n元の外部関数: {external_funcs}")
    print(f"フィルタ後: {filtered}")
    
    print("\n✓ テスト完了")
