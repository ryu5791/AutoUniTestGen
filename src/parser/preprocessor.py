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
    
    def __init__(self, defines: Dict[str, str] = None, include_paths: List[str] = None, enable_includes: bool = False):
        """
        初期化
        
        Args:
            defines: 事前定義するマクロ辞書 {マクロ名: 値}
            include_paths: インクルードパスのリスト
            enable_includes: ヘッダーファイルの読み込みを有効化するか
        """
        self.logger = setup_logger(__name__)
        self.defines: Dict[str, str] = defines.copy() if defines else {}
        self.include_paths: List[str] = include_paths.copy() if include_paths else []
        self.enable_includes: bool = enable_includes
        # 関数マクロを格納 {マクロ名: (パラメータリスト, 本体)}
        self.function_macros: Dict[str, Tuple[List[str], str]] = {}
        # インクルード済みファイルを追跡（循環インクルード防止）
        self.included_files: set = set()
        # ビットフィールド情報を保持 {メンバー名: (構造体名, ビット幅, 基本型)}
        self.bitfields: Dict[str, Tuple[str, int, str]] = {}
    
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
        
        # 3. ビットフィールドをコメント化（pycparser互換性のため）
        code = self._remove_bitfields(code)
        
        # 4. 関数マクロ展開
        code = self._expand_function_macros(code)
        
        # 5. 通常マクロ展開
        code = self._expand_macros(code)
        
        # 6. #include処理（削除）
        code = self._handle_includes(code)
        
        # 7. 残りのディレクティブ処理
        code = self._process_remaining_directives(code)
        
        # 8. コメント削除（最後に実行）
        code = self._remove_comments(code)
        
        # マクロ定義のサマリーをログ出力
        if self.defines:
            self.logger.info(f"有効なマクロ定義 (合計 {len(self.defines)} 個):")
            for name, value in sorted(self.defines.items()):
                self.logger.debug(f"  {name} = {value}")
        
        if self.function_macros:
            self.logger.info(f"有効な関数マクロ定義 (合計 {len(self.function_macros)} 個):")
            for name, (params, _) in sorted(self.function_macros.items()):
                self.logger.debug(f"  {name}({', '.join(params)})")
        
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
    
    def _remove_bitfields(self, code: str) -> str:
        """
        ビットフィールド指定をコメント化し、情報を抽出
        
        pycparserはビットフィールドの構文を完全にはサポートしていないため、
        ビット幅指定（: N）をコメント化する。ただし、ビットフィールド情報は
        別途保持し、テスト生成時に活用する。
        
        また、無名ビットフィールド（例: uint16_t : 13;）に自動的に名前を付ける。
        
        例:
            uint16_t internal : 8;  -> uint16_t internal /* : 8 */;
            uint8_t ram : 1;        -> uint8_t ram /* : 1 */;
            uint16_t : 13;          -> uint16_t reserved_0 /* : 13 */;
        
        Args:
            code: ソースコード
        
        Returns:
            ビットフィールド削除後のコード
        """
        # 名前付きビットフィールドパターン: 型 変数名 : ビット幅 ;
        named_pattern = r'((?:uint\d+_t|int\d+_t|unsigned\s+\w+|signed\s+\w+|\w+))\s+(\w+)\s*:\s*(\d+)\s*;'
        
        # 無名ビットフィールドパターン: 型 : ビット幅 ;
        unnamed_pattern = r'((?:uint\d+_t|int\d+_t|unsigned\s+\w+|signed\s+\w+|\w+))\s*:\s*(\d+)\s*;'
        
        modified_lines = []
        current_struct = None
        struct_stack = []
        unnamed_counter = 0
        
        for line in code.split('\n'):
            # 構造体/共用体の開始を検出
            struct_match = re.match(r'\s*(typedef\s+)?(struct|union)\s+(\w+)?\s*\{', line)
            if struct_match:
                struct_name = struct_match.group(3) if struct_match.group(3) else f"anonymous_{len(struct_stack)}"
                struct_stack.append(struct_name)
                current_struct = struct_name
                modified_lines.append(line)
                continue
            
            # 構造体/共用体の終了を検出
            if current_struct and '}' in line:
                if struct_stack:
                    struct_stack.pop()
                current_struct = struct_stack[-1] if struct_stack else None
                modified_lines.append(line)
                continue
            
            # 名前付きビットフィールドを検出
            named_match = re.search(named_pattern, line)
            if named_match and current_struct:
                base_type = named_match.group(1).strip()
                member_name = named_match.group(2)
                bit_width = int(named_match.group(3))
                
                # ビットフィールド情報を保存
                self.bitfields[member_name] = (current_struct, bit_width, base_type)
                
                # ビット幅をコメント化
                modified_line = re.sub(
                    r'(\w+)\s*:\s*(\d+)\s*;',
                    r'\1 /* : \2 */;',
                    line
                )
                modified_lines.append(modified_line)
                
                self.logger.debug(f"ビットフィールド検出: {current_struct}.{member_name} : {bit_width} ({base_type})")
            
            # 無名ビットフィールドを検出（名前付きにマッチしなかった場合のみ）
            elif current_struct and re.search(unnamed_pattern, line):
                unnamed_match = re.search(unnamed_pattern, line)
                base_type = unnamed_match.group(1).strip()
                bit_width = int(unnamed_match.group(2))
                
                # 自動的に名前を生成
                reserved_name = f"reserved_{unnamed_counter}"
                unnamed_counter += 1
                
                # ビットフィールド情報を保存
                self.bitfields[reserved_name] = (current_struct, bit_width, base_type)
                
                # 無名ビットフィールドに名前を付けてビット幅をコメント化
                modified_line = re.sub(
                    r'(' + re.escape(base_type) + r')\s*:\s*(\d+)\s*;',
                    r'\1 ' + reserved_name + r' /* : \2 */;',
                    line
                )
                modified_lines.append(modified_line)
                
                self.logger.debug(f"無名ビットフィールド検出: {current_struct}.{reserved_name} : {bit_width} ({base_type}) ← 自動命名")
            
            else:
                modified_lines.append(line)
        
        modified_code = '\n'.join(modified_lines)
        
        # 変更があった場合はログ出力
        if self.bitfields:
            self.logger.info(f"ビットフィールド情報を {len(self.bitfields)} 個抽出しました")
            for member, (struct, width, btype) in self.bitfields.items():
                if member.startswith('reserved_'):
                    self.logger.debug(f"  {struct}.{member}: {width}ビット ({btype}) [自動命名]")
                else:
                    self.logger.debug(f"  {struct}.{member}: {width}ビット ({btype})")
        
        return modified_code
    
    def get_bitfields(self) -> Dict[str, Tuple[str, int, str]]:
        """
        抽出されたビットフィールド情報を取得
        
        Returns:
            {メンバー名: (構造体名, ビット幅, 基本型)}
        """
        return self.bitfields.copy()
    
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
        source_function_macros = {}
        
        for line in lines:
            # 関数マクロの検出: #define MACRO(params) body
            func_macro_match = re.match(
                r'^\s*#define\s+(\w+)\s*\(([^)]*)\)\s+(.+)$', 
                line
            )
            
            if func_macro_match:
                macro_name = func_macro_match.group(1)
                params_str = func_macro_match.group(2).strip()
                macro_body = func_macro_match.group(3).strip()
                
                # パラメータをリストに分割
                params = [p.strip() for p in params_str.split(',') if p.strip()]
                
                # 外部から定義されていない場合のみ、コード内の定義を使用
                if macro_name not in self.function_macros:
                    self.function_macros[macro_name] = (params, macro_body)
                    source_function_macros[macro_name] = (params, macro_body)
                    self.logger.debug(
                        f"関数マクロ検出: {macro_name}({', '.join(params)}) = {macro_body}"
                    )
                
                # #define行はコメント化
                processed_lines.append(f"// {line}")
                continue
            
            # 通常のマクロの検出: #define MACRO value
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
        
        if source_function_macros:
            self.logger.info(f"🔧 ソースコード内の関数マクロ定義: {len(source_function_macros)}個")
            for name, (params, body) in list(source_function_macros.items())[:10]:
                self.logger.info(f"  ✓ {name}({', '.join(params)}) = {body}")
            if len(source_function_macros) > 10:
                self.logger.info(f"  ... 他 {len(source_function_macros) - 10}個")
        
        # 全体の統計情報
        external_count = len([k for k in self.defines if k not in source_defines])
        if external_count > 0:
            self.logger.info(f"🔧 外部定義のマクロ: {external_count}個")
        
        total_count = len(self.defines)
        total_func_count = len(self.function_macros)
        self.logger.info(f"📊 使用されるマクロ定義の合計: {total_count}個 (通常) + {total_func_count}個 (関数)")
        
        return '\n'.join(processed_lines)
    
    
    def _expand_function_macros(self, code: str) -> str:
        """
        関数マクロを展開
        
        Args:
            code: ソースコード
        
        Returns:
            関数マクロ展開後のコード
        """
        if not self.function_macros:
            return code
        
        # 複数回展開（ネストしたマクロに対応）
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            code_before = code
            
            for macro_name, (params, body) in self.function_macros.items():
                # 関数マクロの呼び出しを検出して展開
                code = self._expand_single_function_macro(code, macro_name, params, body)
            
            # 変化がなければ終了
            if code == code_before:
                break
        
        if iteration >= max_iterations:
            self.logger.warning(
                "関数マクロ展開が最大反復回数に達しました。"
                "循環参照がある可能性があります。"
            )
        
        return code
    
    def _expand_single_function_macro(self, code: str, macro_name: str, 
                                       params: List[str], body: str) -> str:
        """
        単一の関数マクロを展開
        
        Args:
            code: ソースコード
            macro_name: マクロ名
            params: パラメータリスト
            body: マクロ本体
        
        Returns:
            展開後のコード
        """
        result = []
        i = 0
        
        while i < len(code):
            # マクロ名を検索
            pattern = r'\b' + re.escape(macro_name) + r'\s*\('
            match = re.match(pattern, code[i:])
            
            if match:
                # マクロ呼び出しの開始位置
                start = i
                i += len(match.group(0))
                
                # 括弧内の引数を抽出（ネストした括弧を考慮）
                args_str, end_pos = self._extract_balanced_parentheses(code, i)
                
                if args_str is not None:
                    # 引数をパース
                    args = self._parse_macro_arguments(args_str)
                    
                    # 引数の数が一致するか確認
                    if len(args) == len(params):
                        # マクロを展開
                        expanded = body
                        for param, arg in zip(params, args):
                            # パラメータ名を引数で置換（単語境界を考慮）
                            param_pattern = r'\b' + re.escape(param) + r'\b'
                            expanded = re.sub(param_pattern, arg, expanded)
                        
                        self.logger.debug(
                            f"関数マクロ展開: {macro_name}({', '.join(args)}) → {expanded}"
                        )
                        
                        # 展開結果を追加
                        result.append(expanded)
                        i = end_pos + 1  # 閉じ括弧の次へ
                    else:
                        # 引数数不一致 - 展開しない
                        self.logger.warning(
                            f"関数マクロ {macro_name} の引数数が一致しません: "
                            f"期待={len(params)}, 実際={len(args)}"
                        )
                        result.append(code[start:end_pos + 1])
                        i = end_pos + 1
                else:
                    # 括弧が閉じていない - 展開しない
                    result.append(code[start:i])
            else:
                # マクロではない - そのまま追加
                result.append(code[i])
                i += 1
        
        return ''.join(result)
    
    def _extract_balanced_parentheses(self, code: str, start: int) -> Tuple[str, int]:
        """
        括弧のバランスを考慮して括弧内の内容を抽出
        
        Args:
            code: ソースコード
            start: 開始位置（開き括弧の次の位置）
        
        Returns:
            (括弧内の内容, 閉じ括弧の位置) または (None, -1)
        """
        depth = 1
        i = start
        content_start = start
        
        while i < len(code) and depth > 0:
            char = code[i]
            
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    # 対応する閉じ括弧を見つけた
                    return code[content_start:i], i
            
            i += 1
        
        # 括弧が閉じていない
        return None, -1
    
    def _build_function_macro_pattern(self, macro_name: str) -> str:
        """
        関数マクロ呼び出しの正規表現パターンを構築
        
        Args:
            macro_name: マクロ名
        
        Returns:
            正規表現パターン
        """
        # MACRO(...)の形式を検出
        # より柔軟なパターンでネストした括弧も考慮
        return r'\b' + re.escape(macro_name) + r'\s*\('
    
    def _parse_macro_arguments(self, args_str: str) -> List[str]:
        """
        マクロ引数文字列をパースして引数リストに分割
        
        Args:
            args_str: 引数文字列（例: "a, b, c"）
        
        Returns:
            引数リスト
        """
        args = []
        current_arg = []
        paren_depth = 0
        
        for char in args_str:
            if char == '(':
                paren_depth += 1
                current_arg.append(char)
            elif char == ')':
                paren_depth -= 1
                current_arg.append(char)
            elif char == ',' and paren_depth == 0:
                # トップレベルのカンマで分割
                args.append(''.join(current_arg).strip())
                current_arg = []
            else:
                current_arg.append(char)
        
        # 最後の引数を追加
        if current_arg or args_str.strip():
            args.append(''.join(current_arg).strip())
        
        return args
    
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
        if not self.enable_includes:
            # インクルード機能が無効の場合は従来通りコメント化
            lines = code.split('\n')
            processed_lines = []
            
            for line in lines:
                include_match = re.match(r'^\s*#include\s+[<"](.+?)[>"]', line)
                if include_match:
                    processed_lines.append(f"/* {line} */")
                else:
                    processed_lines.append(line)
            
            return '\n'.join(processed_lines)
        
        # インクルード機能が有効の場合はヘッダーファイルを読み込む
        lines = code.split('\n')
        processed_lines = []
        
        for line in lines:
            include_match = re.match(r'^\s*#include\s+([<"])(.+?)[>"]', line)
            
            if include_match:
                quote_type = include_match.group(1)
                header_file = include_match.group(2)
                
                # 標準ヘッダはコメント化（システムヘッダは読み込まない）
                if quote_type == '<' or self._is_standard_header(header_file):
                    processed_lines.append(f"/* {line} */")
                    self.logger.debug(f"標準ヘッダをスキップ: {header_file}")
                else:
                    # ユーザー定義ヘッダを読み込み
                    header_content = self._read_header_file(header_file)
                    
                    if header_content is not None:
                        # #includeを読み込んだ内容で置換
                        processed_lines.append(f"/* {line} - 展開開始 */")
                        processed_lines.append(header_content)
                        processed_lines.append(f"/* {line} - 展開終了 */")
                        self.logger.info(f"✓ ヘッダーファイルを読み込み: {header_file}")
                    else:
                        # ファイルが見つからない場合はコメント化
                        processed_lines.append(f"/* {line} - ファイルが見つかりません */")
                        self.logger.warning(f"ヘッダーファイルが見つかりません: {header_file}")
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _read_header_file(self, header_file: str) -> str:
        """
        ヘッダーファイルを読み込む
        
        Args:
            header_file: ヘッダーファイル名
        
        Returns:
            ヘッダーファイルの内容、見つからない場合はNone
        """
        import os
        
        # 循環インクルードのチェック
        if header_file in self.included_files:
            self.logger.warning(f"循環インクルードを検出: {header_file}")
            return f"/* 循環インクルード: {header_file} */"
        
        # ヘッダーファイルを検索
        search_paths = self.include_paths.copy()
        
        # カレントディレクトリも検索対象に追加
        if '.' not in search_paths:
            search_paths.insert(0, '.')
        
        for search_path in search_paths:
            file_path = os.path.join(search_path, header_file)
            
            if os.path.exists(file_path):
                try:
                    # エンコーディング自動検出で読み込み
                    from ..utils import read_file
                    
                    # インクルード済みとしてマーク
                    self.included_files.add(header_file)
                    
                    content = read_file(file_path, encoding='auto')
                    
                    # ヘッダーファイルの内容も前処理（再帰的に処理）
                    # ただし、#includeは処理しない（循環を避ける）
                    processed_content = self._preprocess_header_content(content)
                    
                    return processed_content
                    
                except Exception as e:
                    self.logger.error(f"ヘッダーファイルの読み込みエラー: {file_path} - {e}")
                    return None
        
        # ファイルが見つからない
        return None
    
    def _preprocess_header_content(self, content: str) -> str:
        """
        ヘッダーファイルの内容を前処理
        
        Args:
            content: ヘッダーファイルの内容
        
        Returns:
            前処理済みの内容
        """
        # コメント削除
        content = self._remove_comments(content)
        
        # #defineを収集（ヘッダー内のマクロも利用可能に）
        content = self._collect_defines(content)
        
        # 条件付きコンパイルを処理
        content = self._process_conditional_compilation(content)
        
        # #includeは無効化（ネストしたインクルードは処理しない）
        lines = content.split('\n')
        processed_lines = []
        for line in lines:
            if re.match(r'^\s*#include\s+', line):
                processed_lines.append(f"/* {line} - ネストしたインクルード */")
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
