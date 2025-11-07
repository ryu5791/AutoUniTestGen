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
    
    def __init__(self, defines: Dict[str, str] = None):
        """
        初期化
        
        Args:
            defines: 事前定義するマクロ辞書 {マクロ名: 値}
        """
        self.logger = setup_logger(__name__)
        self.defines: Dict[str, str] = defines.copy() if defines else {}
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
        
        if self.defines:
            self.logger.info(f"事前定義されたマクロ: {list(self.defines.keys())}")
        
        # 1. #define処理（コード内の定義を収集）
        code = self._collect_defines(code)
        
        # 2. 条件付きコンパイル処理（#ifdef, #ifndef, #if）
        code = self._process_conditional_compilation(code)
        
        # 3. マクロ展開
        code = self._expand_macros(code)
        
        # 4. #include処理（削除）
        code = self._handle_includes(code)
        
        # 5. 残りのディレクティブ処理
        code = self._process_remaining_directives(code)
        
        # 6. コメント削除（最後に実行）
        code = self._remove_comments(code)
        
        # マクロ定義のサマリーをログ出力
        if self.defines:
            self.logger.info(f"有効なマクロ定義 (合計 {len(self.defines)} 個):")
            for name, value in sorted(self.defines.items()):
                self.logger.debug(f"  {name} = {value}")
        
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
    
    def _collect_defines(self, code: str) -> str:
        """
        #define を収集（展開はしない）
        
        優先順位:
        1. 外部から定義されたマクロ（-Dオプション、プリセットなど）
        2. ソースコード内の#define
        
        Args:
            code: ソースコード
        
        Returns:
            コード（#define行をコメント化）
        """
        lines = code.split('\n')
        processed_lines = []
        source_defines = {}
        
        for line in lines:
            # #define の検出
            define_match = re.match(r'^\s*#define\s+(\w+)(?:\s+(.+?))?$', line)
            
            if define_match:
                macro_name = define_match.group(1)
                macro_value = define_match.group(2).strip() if define_match.group(2) else '1'
                
                # 外部から定義されていない場合のみ、コード内の定義を使用
                if macro_name not in self.defines:
                    self.defines[macro_name] = macro_value
                    source_defines[macro_name] = macro_value
                else:
                    # 外部定義が優先されることをログに記録
                    self.logger.debug(
                        f"マクロ '{macro_name}' はコマンドラインで定義されているため、"
                        f"ソースコードの定義（{macro_value}）は無視されます。"
                        f"使用される値: {self.defines[macro_name]}"
                    )
                
                # #define行はコメント化（pycparserエラー回避）
                processed_lines.append(f"// {line}")
            else:
                processed_lines.append(line)
        
        # ソースコード内で見つかった定義をログ出力
        if source_defines:
            self.logger.info(f"📄 ソースコード内のマクロ定義: {len(source_defines)}個")
            # 最初の10個を詳細表示
            items = list(source_defines.items())
            for name, value in items[:10]:
                self.logger.info(f"  ✓ {name} = {value}")
            if len(source_defines) > 10:
                self.logger.info(f"  ... 他 {len(source_defines) - 10}個")
        
        # 全体の統計情報
        external_count = len([k for k in self.defines if k not in source_defines])
        if external_count > 0:
            self.logger.info(f"🔧 外部定義のマクロ: {external_count}個")
        
        total_count = len(self.defines)
        self.logger.info(f"📊 使用されるマクロ定義の合計: {total_count}個")
        
        return '\n'.join(processed_lines)
    
    def _expand_macros(self, code: str) -> str:
        """
        マクロを展開
        
        Args:
            code: ソースコード
        
        Returns:
            マクロ展開後のコード
        """
        # マクロ展開（単純な置換のみ）
        for macro_name, macro_value in self.defines.items():
            # 単語境界を考慮した置換
            pattern = r'\b' + re.escape(macro_name) + r'\b'
            code = re.sub(pattern, macro_value, code)
        
        return code
    
    def _process_conditional_compilation(self, code: str) -> str:
        """
        条件付きコンパイル（#ifdef, #ifndef, #if）を処理
        
        Args:
            code: ソースコード
        
        Returns:
            処理後のコード
        """
        lines = code.split('\n')
        processed_lines = []
        
        # スタックで#if/#ifdef/#ifndef のネストを管理
        condition_stack = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # #ifdef の検出
            ifdef_match = re.match(r'^\s*#ifdef\s+(\w+)', line)
            if ifdef_match:
                macro_name = ifdef_match.group(1)
                is_defined = macro_name in self.defines
                condition_stack.append(('ifdef', is_defined))
                processed_lines.append(f"// {line}")
                i += 1
                continue
            
            # #ifndef の検出
            ifndef_match = re.match(r'^\s*#ifndef\s+(\w+)', line)
            if ifndef_match:
                macro_name = ifndef_match.group(1)
                is_not_defined = macro_name not in self.defines
                condition_stack.append(('ifndef', is_not_defined))
                processed_lines.append(f"// {line}")
                i += 1
                continue
            
            # #if の検出（簡易的な評価）
            if_match = re.match(r'^\s*#if\s+(.+)$', line)
            if if_match:
                condition = if_match.group(1).strip()
                is_true = self._evaluate_condition(condition)
                condition_stack.append(('if', is_true))
                processed_lines.append(f"// {line}")
                i += 1
                continue
            
            # #else の検出
            if re.match(r'^\s*#else\s*$', line):
                if condition_stack:
                    cond_type, cond_value = condition_stack.pop()
                    # 条件を反転
                    condition_stack.append((cond_type, not cond_value))
                processed_lines.append(f"// {line}")
                i += 1
                continue
            
            # #elif の検出
            elif_match = re.match(r'^\s*#elif\s+(.+)$', line)
            if elif_match:
                if condition_stack:
                    condition_stack.pop()
                    condition = elif_match.group(1).strip()
                    is_true = self._evaluate_condition(condition)
                    condition_stack.append(('elif', is_true))
                processed_lines.append(f"// {line}")
                i += 1
                continue
            
            # #endif の検出
            if re.match(r'^\s*#endif', line):
                if condition_stack:
                    condition_stack.pop()
                processed_lines.append(f"// {line}")
                i += 1
                continue
            
            # 通常の行の処理
            # 条件が偽の場合はコメント化
            should_include = True
            if condition_stack:
                # スタック内のすべての条件が真である必要がある
                should_include = all(cond for _, cond in condition_stack)
            
            if should_include:
                processed_lines.append(line)
            else:
                # 条件が偽の場合はコメント化
                processed_lines.append(f"// {line}")
            
            i += 1
        
        return '\n'.join(processed_lines)
    
    def _evaluate_condition(self, condition: str) -> bool:
        """
        条件式を評価（簡易版）
        
        Args:
            condition: 条件式（例: "defined(TYPE1) && defined(TYPE2)"）
        
        Returns:
            評価結果
        """
        # defined() マクロの処理
        def replace_defined(match):
            macro_name = match.group(1)
            return '1' if macro_name in self.defines else '0'
        
        condition = re.sub(r'defined\s*\(\s*(\w+)\s*\)', replace_defined, condition)
        
        # マクロ名を値に置換
        for macro_name, macro_value in self.defines.items():
            pattern = r'\b' + re.escape(macro_name) + r'\b'
            condition = re.sub(pattern, macro_value, condition)
        
        # 簡易的な評価（安全でない可能性があるため、制限的に実行）
        try:
            # 数値と論理演算子のみ許可
            if re.match(r'^[\d\s\+\-\*\/\(\)\&\|\!\=\<\>]+$', condition):
                # && を and に、|| を or に変換
                condition = condition.replace('&&', ' and ').replace('||', ' or ')
                condition = condition.replace('!', ' not ')
                result = eval(condition)
                return bool(result)
        except:
            pass
        
        # 評価できない場合は真とする（保守的）
        return True
    
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
    
    def _process_remaining_directives(self, code: str) -> str:
        """
        残りのプリプロセッサディレクティブを処理
        
        Args:
            code: ソースコード
        
        Returns:
            処理後のコード
        """
        lines = code.split('\n')
        processed_lines = []
        
        for line in lines:
            # #pragma の検出
            if re.match(r'^\s*#pragma\s+', line):
                processed_lines.append(f"// {line}")
                continue
            
            # #undef の検出
            if re.match(r'^\s*#undef\s+', line):
                processed_lines.append(f"// {line}")
                continue
            
            # #error の検出
            if re.match(r'^\s*#error\s+', line):
                processed_lines.append(f"// {line}")
                continue
            
            # #warning の検出
            if re.match(r'^\s*#warning\s+', line):
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
