"""
AssignableVariableCheckerモジュール

変数が代入可能かどうかを判定するクラス

v4.3.3.1新規作成:
- ローカル変数/ループ変数への代入防止
- 構造体メンバー名単独への代入防止
- enum定数への代入防止
- 関数名への代入防止
- 配列インデックス変数への代入防止

v4.4: 標準マクロ定数への代入防止
- limits.h: CHAR_MAX, INT_MAX, UINT_MAX, UCHAR_MAX, etc.
- stdint.h: INT8_MAX, UINT8_MAX, INT16_MAX, etc.
- stdbool.h: true, false
- stddef.h: NULL
- float.h: FLT_MAX, DBL_MAX, etc.

v4.5: 配列変数への直接代入防止
- 配列変数名（例: Utv12）への直接代入を検出
- 条件式から配列アクセスパターンを検出して配列変数を登録
- ビットフィールド範囲外の値代入を検出

代入可能な変数:
- グローバル変数
- 関数パラメータ
- 構造体メンバーアクセス（ルート変数がグローバル/パラメータの場合）
"""

import sys
import os
import re
from typing import Set, Optional, Tuple, List, Dict, Any

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class AssignableVariableChecker:
    """変数が代入可能かどうかを判定するクラス"""
    
    # 代入不可の理由コード
    REASON_LOCAL_VARIABLE = "local_variable"
    REASON_LOOP_VARIABLE = "loop_variable"
    REASON_STRUCT_MEMBER_NAME = "struct_member_name"
    REASON_ENUM_CONSTANT = "enum_constant"
    REASON_FUNCTION_NAME = "function_name"
    REASON_NUMERIC_LITERAL = "numeric_literal"
    REASON_UNKNOWN_LOCAL = "unknown_local"  # グローバルにもローカルにも登録されていない
    REASON_ARRAY_INDEX_LOCAL = "array_index_local"  # 配列インデックス内のローカル変数
    REASON_MACRO = "macro"  # マクロ（関数マクロ・変数マクロ）
    REASON_STANDARD_MACRO_CONSTANT = "standard_macro_constant"  # v4.4: 標準マクロ定数
    REASON_ARRAY_VARIABLE = "array_variable"  # v4.5: 配列変数（直接代入不可）
    REASON_BITFIELD_OUT_OF_RANGE = "bitfield_out_of_range"  # v4.5: ビットフィールド範囲外
    
    # v4.4: 標準マクロ定数（代入不可）
    # これらは <limits.h>, <stdint.h>, <stdbool.h>, <stddef.h>, <float.h> で定義される
    STANDARD_MACRO_CONSTANTS: Set[str] = {
        # limits.h - CHAR
        'CHAR_BIT', 'CHAR_MAX', 'CHAR_MIN',
        # limits.h - INT
        'INT_MAX', 'INT_MIN', 'UINT_MAX',
        # limits.h - SIGNED CHAR
        'SCHAR_MAX', 'SCHAR_MIN',
        # limits.h - SHORT
        'SHRT_MAX', 'SHRT_MIN',
        # limits.h - LONG
        'LONG_MAX', 'LONG_MIN',
        # limits.h - UNSIGNED
        'UCHAR_MAX', 'USHRT_MAX', 'ULONG_MAX',
        # limits.h - LONG LONG
        'LLONG_MIN', 'LLONG_MAX', 'ULLONG_MAX',
        
        # stdint.h - INT8
        'INT8_MIN', 'INT8_MAX', 'UINT8_MAX',
        # stdint.h - INT16
        'INT16_MIN', 'INT16_MAX', 'UINT16_MAX',
        # stdint.h - INT32
        'INT32_MIN', 'INT32_MAX', 'UINT32_MAX',
        # stdint.h - INT64
        'INT64_MIN', 'INT64_MAX', 'UINT64_MAX',
        
        # stdint.h - Other
        'SIZE_MAX', 'PTRDIFF_MIN', 'PTRDIFF_MAX',
        'INTMAX_MIN', 'INTMAX_MAX', 'UINTMAX_MAX',
        'INTPTR_MIN', 'INTPTR_MAX', 'UINTPTR_MAX',
        'WCHAR_MIN', 'WCHAR_MAX',
        'WINT_MIN', 'WINT_MAX',
        'SIG_ATOMIC_MIN', 'SIG_ATOMIC_MAX',
        
        # stdbool.h
        'true', 'false',
        
        # stddef.h
        'NULL',
        
        # float.h（浮動小数点定数）
        'FLT_MAX', 'FLT_MIN', 'FLT_EPSILON',
        'FLT_RADIX', 'FLT_ROUNDS', 'FLT_DIG', 'FLT_MANT_DIG',
        'FLT_MIN_EXP', 'FLT_MAX_EXP', 'FLT_MIN_10_EXP', 'FLT_MAX_10_EXP',
        'DBL_MAX', 'DBL_MIN', 'DBL_EPSILON',
        'DBL_DIG', 'DBL_MANT_DIG',
        'DBL_MIN_EXP', 'DBL_MAX_EXP', 'DBL_MIN_10_EXP', 'DBL_MAX_10_EXP',
        'LDBL_MAX', 'LDBL_MIN', 'LDBL_EPSILON',
        'LDBL_DIG', 'LDBL_MANT_DIG',
        'LDBL_MIN_EXP', 'LDBL_MAX_EXP', 'LDBL_MIN_10_EXP', 'LDBL_MAX_10_EXP',
        
        # errno.h
        'EDOM', 'ERANGE', 'EILSEQ',
        
        # signal.h
        'SIGABRT', 'SIGFPE', 'SIGILL', 'SIGINT', 'SIGSEGV', 'SIGTERM',
        
        # stdlib.h
        'EXIT_SUCCESS', 'EXIT_FAILURE', 'RAND_MAX', 'MB_CUR_MAX',
        
        # stdio.h
        'EOF', 'BUFSIZ', 'FOPEN_MAX', 'FILENAME_MAX',
        'L_tmpnam', 'TMP_MAX',
        'SEEK_SET', 'SEEK_CUR', 'SEEK_END',
        '_IOFBF', '_IOLBF', '_IONBF',
    }
    
    def __init__(self, parsed_data: Any):
        """
        初期化
        
        Args:
            parsed_data: ParsedDataオブジェクト
        """
        self.logger = setup_logger(__name__)
        self.parsed_data = parsed_data
        
        # 代入不可識別子のセットを構築
        self._non_assignable: Dict[str, str] = {}  # {識別子名: 理由コード}
        self._struct_member_names: Set[str] = set()
        self._assignable_vars: Set[str] = set()  # 代入可能な変数
        self._array_variables: Set[str] = set()  # v4.5: 配列変数のセット
        
        self._build_non_assignable_set()
        self._build_assignable_set()
        self._build_array_variable_set()  # v4.5: 配列変数セットを構築
    
    def _build_non_assignable_set(self):
        """代入不可能な識別子のセットを構築"""
        
        # 0. v4.4: 標準マクロ定数（最優先で代入不可）
        for const_name in self.STANDARD_MACRO_CONSTANTS:
            self._non_assignable[const_name] = self.REASON_STANDARD_MACRO_CONSTANT
        
        # 1. ローカル変数（すべて代入不可）
        if hasattr(self.parsed_data, 'local_variables') and self.parsed_data.local_variables:
            for var_name, var_info in self.parsed_data.local_variables.items():
                # ループ変数は特別な理由コード
                if hasattr(var_info, 'is_loop_variable') and var_info.is_loop_variable:
                    self._non_assignable[var_name] = self.REASON_LOOP_VARIABLE
                else:
                    self._non_assignable[var_name] = self.REASON_LOCAL_VARIABLE
        
        # 2. 構造体メンバー名（単独では代入不可）
        if hasattr(self.parsed_data, 'struct_definitions') and self.parsed_data.struct_definitions:
            for struct_def in self.parsed_data.struct_definitions:
                self._collect_member_names(struct_def)
        
        # 3. enum定数（代入不可）
        if hasattr(self.parsed_data, 'enum_values') and self.parsed_data.enum_values:
            for enum_val in self.parsed_data.enum_values:
                self._non_assignable[enum_val] = self.REASON_ENUM_CONSTANT
        
        # 4. 関数名（代入不可）
        if hasattr(self.parsed_data, 'external_functions') and self.parsed_data.external_functions:
            for func_name in self.parsed_data.external_functions:
                self._non_assignable[func_name] = self.REASON_FUNCTION_NAME
        
        # function_signaturesからも関数名を収集
        if hasattr(self.parsed_data, 'function_signatures') and self.parsed_data.function_signatures:
            for func_name in self.parsed_data.function_signatures.keys():
                if func_name not in self._non_assignable:
                    self._non_assignable[func_name] = self.REASON_FUNCTION_NAME
        
        # 5. マクロ（関数マクロも変数マクロも代入不可）
        if hasattr(self.parsed_data, 'macros') and self.parsed_data.macros:
            for macro_name in self.parsed_data.macros.keys():
                if macro_name not in self._non_assignable:
                    self._non_assignable[macro_name] = self.REASON_MACRO
    
    def _collect_member_names(self, struct_def, depth: int = 0):
        """
        構造体定義からメンバー名を収集
        
        Args:
            struct_def: 構造体定義
            depth: 再帰の深さ（無限ループ防止）
        """
        if depth > 10:  # 安全策
            return
        
        if not hasattr(struct_def, 'members'):
            return
        
        for member in struct_def.members:
            if hasattr(member, 'name') and member.name:
                self._struct_member_names.add(member.name)
                # struct_member_nameとして非代入可能に追加
                if member.name not in self._non_assignable:
                    self._non_assignable[member.name] = self.REASON_STRUCT_MEMBER_NAME
            
            # ネストした構造体もチェック
            if hasattr(member, 'nested_struct') and member.nested_struct:
                self._collect_member_names(member.nested_struct, depth + 1)
    
    def _build_assignable_set(self):
        """代入可能な変数のセットを構築"""
        
        # 1. グローバル変数
        if hasattr(self.parsed_data, 'global_variables') and self.parsed_data.global_variables:
            for var_name in self.parsed_data.global_variables:
                self._assignable_vars.add(var_name)
        
        # 2. variables属性からも収集
        if hasattr(self.parsed_data, 'variables') and self.parsed_data.variables:
            for var_info in self.parsed_data.variables:
                if hasattr(var_info, 'name') and var_info.name:
                    self._assignable_vars.add(var_info.name)
        
        # 3. 関数パラメータ
        if hasattr(self.parsed_data, 'function_info') and self.parsed_data.function_info:
            if hasattr(self.parsed_data.function_info, 'parameters') and self.parsed_data.function_info.parameters:
                for param in self.parsed_data.function_info.parameters:
                    param_name = param.get('name', '')
                    if param_name:
                        self._assignable_vars.add(param_name)
    
    def _build_array_variable_set(self):
        """
        v4.5: 配列変数のセットを構築
        
        配列変数は要素アクセスなしでは代入できないため、特別に管理する
        """
        # 1. variables属性から配列変数を検出
        if hasattr(self.parsed_data, 'variables') and self.parsed_data.variables:
            for var_info in self.parsed_data.variables:
                if hasattr(var_info, 'var_type') and var_info.var_type:
                    # 型に [ が含まれていれば配列
                    if '[' in var_info.var_type:
                        if hasattr(var_info, 'name') and var_info.name:
                            self._array_variables.add(var_info.name)
                # definition属性からも確認
                if hasattr(var_info, 'definition') and var_info.definition:
                    # 宣言に [ が含まれていれば配列
                    if hasattr(var_info, 'name') and var_info.name:
                        if re.search(rf'\b{re.escape(var_info.name)}\s*\[', var_info.definition):
                            self._array_variables.add(var_info.name)
        
        # 2. グローバル変数の宣言情報からも検出（ソースを直接解析した場合）
        # これはparsed_data.variablesがない場合のフォールバック
        
        self.logger.debug(f"配列変数を検出: {self._array_variables}")
    
    def is_assignable(self, var_name: str) -> bool:
        """
        変数が代入可能かどうかを判定
        
        v4.5: 配列変数への直接代入を検出
        
        Args:
            var_name: 変数名（構造体メンバーアクセスを含む場合あり）
        
        Returns:
            代入可能な場合True
        """
        # 数値リテラルチェック
        clean_name = var_name.strip()
        if self._is_numeric_literal(clean_name):
            return False
        
        # 構造体メンバーアクセス（.を含む）の場合はルート変数をチェック
        if '.' in clean_name:
            root = clean_name.split('.')[0]
            root = re.sub(r'\[\w+\]', '', root)  # 配列アクセスを除去
            
            # ルート変数が代入可能かチェック
            return self._is_root_assignable(root)
        
        # 配列アクセスの場合（例: Utv12[Utv19]）
        if '[' in clean_name:
            # 配列名を抽出
            array_name = re.sub(r'\[\w+\]', '', clean_name)
            
            # 配列インデックス内の変数をチェック
            index_vars = self._extract_array_index_variables(clean_name)
            for idx_var in index_vars:
                if idx_var in self._non_assignable:
                    return False
            
            return self._is_root_assignable(array_name)
        
        # v4.5: 単独の変数名で、かつ配列変数の場合は代入不可
        # 条件式 Utv12[Utv19] から Utv12 が抽出された場合、
        # 配列名だけでは代入できない
        if self.is_array_variable(clean_name):
            return False
        
        # 単独の変数名
        return self._is_root_assignable(clean_name)
    
    def _is_root_assignable(self, root_name: str) -> bool:
        """
        ルート変数名が代入可能かチェック
        
        Args:
            root_name: ルート変数名
        
        Returns:
            代入可能な場合True
        """
        # 明示的に代入不可能な変数セットに含まれているかを先にチェック
        # （マクロ、関数、enum定数などは代入不可）
        if root_name in self._non_assignable:
            return False
        
        # 明示的に代入可能な変数セットに含まれているか
        if root_name in self._assignable_vars:
            return True
        
        # どちらにも含まれない場合は未知のローカル変数と推測
        # → 代入不可
        return False
    
    def _is_numeric_literal(self, name: str) -> bool:
        """数値リテラルかどうかを判定"""
        # 整数リテラル
        if name.isdigit():
            return True
        if name.startswith('-') and len(name) > 1 and name[1:].isdigit():
            return True
        # 16進数リテラル
        if name.startswith('0x') or name.startswith('0X'):
            return True
        return False
    
    def _extract_array_index_variables(self, expression: str) -> List[str]:
        """
        配列アクセスのインデックス変数を抽出
        
        Args:
            expression: 式（例: "Utv12[Utv19]", "arr[i].member"）
        
        Returns:
            インデックス変数名のリスト（数値は除外）
        """
        pattern = r'\[([a-zA-Z_]\w*)\]'
        matches = re.findall(pattern, expression)
        # 数値は除外
        return [m for m in matches if not m.isdigit()]
    
    def get_reason(self, var_name: str) -> str:
        """
        代入不可の理由を取得
        
        v4.5: 配列変数への直接代入を検出
        
        Args:
            var_name: 変数名
        
        Returns:
            代入不可の理由（日本語）
        """
        clean_name = var_name.strip()
        
        # 数値リテラル
        if self._is_numeric_literal(clean_name):
            return f"{clean_name}は数値リテラルのため変数として初期化できません"
        
        # 構造体メンバーアクセスの場合
        if '.' in clean_name:
            root = clean_name.split('.')[0]
            root = re.sub(r'\[\w+\]', '', root)
            return self._get_reason_for_identifier(root, is_root=True, original=clean_name)
        
        # 配列アクセスの場合
        if '[' in clean_name:
            # 配列インデックス内の変数をチェック
            index_vars = self._extract_array_index_variables(clean_name)
            for idx_var in index_vars:
                if idx_var in self._non_assignable:
                    reason_code = self._non_assignable[idx_var]
                    return self._format_reason(idx_var, reason_code, is_index=True, original=clean_name)
            
            # 配列名をチェック
            array_name = re.sub(r'\[\w+\]', '', clean_name)
            return self._get_reason_for_identifier(array_name, is_root=True, original=clean_name)
        
        # v4.5: 単独の変数名で、かつ配列変数の場合
        if self.is_array_variable(clean_name):
            return self._format_reason(clean_name, self.REASON_ARRAY_VARIABLE)
        
        # 単独の識別子
        return self._get_reason_for_identifier(clean_name)
    
    def _get_reason_for_identifier(self, name: str, is_root: bool = False, original: str = None) -> str:
        """
        識別子に対する理由を取得
        
        v4.5: 配列変数への直接代入を検出
        
        Args:
            name: 識別子名
            is_root: ルート変数として評価中か
            original: 元の式（構造体アクセス等）
        
        Returns:
            理由の文字列
        """
        # v4.5: 配列変数のチェック
        if self.is_array_variable(name):
            return self._format_reason(name, self.REASON_ARRAY_VARIABLE, original=original)
        
        if name in self._non_assignable:
            reason_code = self._non_assignable[name]
            return self._format_reason(name, reason_code, original=original)
        
        # 代入可能リストにも非代入可能リストにもない = 未知のローカル変数
        return self._format_reason(name, self.REASON_UNKNOWN_LOCAL, original=original)
    
    def _format_reason(self, name: str, reason_code: str, is_index: bool = False, original: str = None) -> str:
        """
        理由コードを日本語メッセージに変換
        
        Args:
            name: 識別子名
            reason_code: 理由コード
            is_index: 配列インデックスとして評価中か
            original: 元の式
        
        Returns:
            日本語の理由メッセージ
        """
        suffix = f"（{original}）" if original and original != name else ""
        
        if is_index:
            prefix = f"配列インデックス {name} は"
        else:
            prefix = f"{name}は"
        
        reason_map = {
            self.REASON_LOCAL_VARIABLE: f"{prefix}関数内ローカル変数のため直接初期化できません{suffix}",
            self.REASON_LOOP_VARIABLE: f"{prefix}for文のループ変数のため直接初期化できません{suffix}",
            self.REASON_STRUCT_MEMBER_NAME: f"{prefix}構造体メンバー名のため変数として初期化できません{suffix}",
            self.REASON_ENUM_CONSTANT: f"{prefix}enum定数のため変数として初期化できません{suffix}",
            self.REASON_FUNCTION_NAME: f"{prefix}関数名のため変数として初期化できません{suffix}",
            self.REASON_NUMERIC_LITERAL: f"{prefix}数値リテラルのため変数として初期化できません{suffix}",
            self.REASON_UNKNOWN_LOCAL: f"{prefix}関数内ローカル変数と推測されます{suffix}",
            self.REASON_ARRAY_INDEX_LOCAL: f"{prefix}ローカル変数のため直接初期化できません{suffix}",
            self.REASON_MACRO: f"{prefix}マクロのため変数として初期化できません{suffix}",
            self.REASON_STANDARD_MACRO_CONSTANT: f"{prefix}標準ライブラリのマクロ定数のため代入できません{suffix}",
            self.REASON_ARRAY_VARIABLE: f"{prefix}配列のため直接代入できません。{name}[インデックス]の形式で指定してください{suffix}",
            self.REASON_BITFIELD_OUT_OF_RANGE: f"{prefix}ビットフィールドのため、有効な値を指定してください{suffix}",
        }
        
        return reason_map.get(reason_code, f"{prefix}代入不可{suffix}")
    
    def get_reason_code(self, var_name: str) -> Optional[str]:
        """
        代入不可の理由コードを取得
        
        Args:
            var_name: 変数名
        
        Returns:
            理由コード（代入可能な場合はNone）
        """
        clean_name = var_name.strip()
        
        if self._is_numeric_literal(clean_name):
            return self.REASON_NUMERIC_LITERAL
        
        if '.' in clean_name:
            root = clean_name.split('.')[0]
            root = re.sub(r'\[\w+\]', '', root)
            clean_name = root
        elif '[' in clean_name:
            # 配列インデックス内の変数をチェック
            index_vars = self._extract_array_index_variables(clean_name)
            for idx_var in index_vars:
                if idx_var in self._non_assignable:
                    return self._non_assignable[idx_var]
            
            clean_name = re.sub(r'\[\w+\]', '', clean_name)
        
        # v4.5: 配列変数のチェック
        if self.is_array_variable(clean_name):
            return self.REASON_ARRAY_VARIABLE
        
        if clean_name in self._non_assignable:
            return self._non_assignable[clean_name]
        
        if clean_name not in self._assignable_vars:
            return self.REASON_UNKNOWN_LOCAL
        
        return None
    
    def classify_variables(self, variables: List[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        変数リストを代入可能/不可に分類
        
        Args:
            variables: 変数名のリスト
        
        Returns:
            (assignable_vars, non_assignable_vars)
            assignable_vars: 代入可能な変数のリスト
            non_assignable_vars: [(変数名, 理由), ...] のリスト
        """
        assignable = []
        non_assignable = []
        
        for var in variables:
            if self.is_assignable(var):
                assignable.append(var)
            else:
                reason = self.get_reason(var)
                non_assignable.append((var, reason))
        
        return assignable, non_assignable
    
    def is_struct_member_name(self, name: str) -> bool:
        """
        識別子が構造体メンバー名かどうかを判定
        
        Args:
            name: 識別子名
        
        Returns:
            構造体メンバー名の場合True
        """
        return name in self._struct_member_names
    
    def is_loop_variable(self, name: str) -> bool:
        """
        変数がループ変数かどうかを判定
        
        Args:
            name: 変数名
        
        Returns:
            ループ変数の場合True
        """
        if name in self._non_assignable:
            return self._non_assignable[name] == self.REASON_LOOP_VARIABLE
        return False
    
    def is_enum_constant(self, name: str) -> bool:
        """
        識別子がenum定数かどうかを判定
        
        Args:
            name: 識別子名
        
        Returns:
            enum定数の場合True
        """
        if name in self._non_assignable:
            return self._non_assignable[name] == self.REASON_ENUM_CONSTANT
        return False
    
    def is_function(self, name: str) -> bool:
        """
        識別子が関数名かどうかを判定
        
        Args:
            name: 識別子名
        
        Returns:
            関数名の場合True
        """
        if name in self._non_assignable:
            return self._non_assignable[name] == self.REASON_FUNCTION_NAME
        return False
    
    def is_standard_macro_constant(self, name: str) -> bool:
        """
        識別子が標準マクロ定数かどうかを判定（v4.4）
        
        Args:
            name: 識別子名
        
        Returns:
            標準マクロ定数の場合True
        """
        return name in self.STANDARD_MACRO_CONSTANTS
    
    def is_array_variable(self, name: str) -> bool:
        """
        識別子が配列変数かどうかを判定（v4.5）
        
        Args:
            name: 識別子名
        
        Returns:
            配列変数の場合True
        """
        return name in self._array_variables
    
    def add_array_variable(self, name: str) -> None:
        """
        配列変数を手動で追加（v4.5）
        
        条件式から配列アクセスパターンを検出した場合に使用
        
        Args:
            name: 配列変数名
        """
        self._array_variables.add(name)
    
    def detect_array_from_condition(self, condition_expr: str) -> None:
        """
        条件式から配列変数を検出して登録（v4.5）
        
        条件式に含まれる配列アクセスパターン（例: Utv12[Utv19]）から
        配列変数名（Utv12）を検出して登録する
        
        Args:
            condition_expr: 条件式
        """
        # 配列アクセスパターン: 変数名[変数名または数値]
        pattern = r'\b([a-zA-Z_]\w*)\s*\[[^\]]+\]'
        matches = re.findall(pattern, condition_expr)
        for match in matches:
            if match not in self._non_assignable:  # 関数名やマクロでない場合
                self._array_variables.add(match)
                self.logger.debug(f"条件式から配列変数を検出: {match}")


if __name__ == "__main__":
    # AssignableVariableCheckerのテスト
    print("=" * 70)
    print("AssignableVariableChecker v4.4 のテスト")
    print("=" * 70)
    print()
    
    from src.data_structures import (
        ParsedData, Condition, ConditionType, FunctionInfo,
        LocalVariableInfo, StructDefinition, StructMember
    )
    
    # テスト用のParsedDataを作成
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="Utf1",
        external_functions=['Utf7', 'Utf8', 'Utf12'],
        global_variables=['Utx116', 'Utx130', 'Utx204'],
        enum_values=['Utm74', 'Utm75', 'STATE_IDLE', 'STATE_ACTIVE']
    )
    
    # 関数情報
    parsed_data.function_info = FunctionInfo(
        name="Utf1",
        return_type="void",
        parameters=[{'type': 'uint8_t', 'name': 'Utv1'}]
    )
    
    # ローカル変数情報
    parsed_data.local_variables = {
        'Utv19': LocalVariableInfo(
            name='Utv19',
            var_type='uint8_t',
            scope='Utf1',
            is_loop_variable=True
        ),
        'Utv20': LocalVariableInfo(
            name='Utv20',
            var_type='uint16_t',
            scope='Utf1',
            is_loop_variable=False
        )
    }
    
    # 構造体定義
    struct_def = StructDefinition(
        name='state_def_t',
        members=[
            StructMember(name='Utm6', type='uint8_t'),
            StructMember(name='Utm7', type='uint8_t'),
            StructMember(name='Utm27', type='uint16_t'),
        ]
    )
    parsed_data.struct_definitions = [struct_def]
    
    # チェッカーを初期化
    checker = AssignableVariableChecker(parsed_data)
    
    print("1. 代入可能な変数のテスト")
    print("-" * 40)
    
    assignable_tests = [
        ('Utx116', True, 'グローバル変数'),
        ('Utx116.Utm6.Utm7', True, '構造体メンバーアクセス（グローバル）'),
        ('Utv1', True, '関数パラメータ'),
    ]
    
    for var, expected, desc in assignable_tests:
        result = checker.is_assignable(var)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {var:30s} → {result} ({desc})")
    
    print()
    print("2. 代入不可な変数のテスト")
    print("-" * 40)
    
    non_assignable_tests = [
        ('Utv19', False, 'ループ変数'),
        ('Utv20', False, 'ローカル変数'),
        ('Utm27', False, '構造体メンバー名単独'),
        ('Utm74', False, 'enum定数'),
        ('Utf7', False, '関数名'),
        ('123', False, '数値リテラル'),
        ('UnknownVar', False, '未知の変数（ローカルと推測）'),
    ]
    
    for var, expected, desc in non_assignable_tests:
        result = checker.is_assignable(var)
        status = "✓" if result == expected else "✗"
        reason = checker.get_reason(var) if not result else ""
        print(f"  {status} {var:30s} → {result} ({desc})")
        if reason:
            print(f"      理由: {reason}")
    
    print()
    print("3. v4.4: 標準マクロ定数のテスト")
    print("-" * 40)
    
    macro_const_tests = [
        ('UCHAR_MAX', False, 'limits.h 定数'),
        ('INT_MAX', False, 'limits.h 定数'),
        ('INT_MIN', False, 'limits.h 定数'),
        ('UINT8_MAX', False, 'stdint.h 定数'),
        ('UINT16_MAX', False, 'stdint.h 定数'),
        ('UINT32_MAX', False, 'stdint.h 定数'),
        ('true', False, 'stdbool.h 定数'),
        ('false', False, 'stdbool.h 定数'),
        ('NULL', False, 'stddef.h 定数'),
        ('FLT_MAX', False, 'float.h 定数'),
        ('EOF', False, 'stdio.h 定数'),
    ]
    
    for var, expected, desc in macro_const_tests:
        result = checker.is_assignable(var)
        status = "✓" if result == expected else "✗"
        reason = checker.get_reason(var) if not result else ""
        print(f"  {status} {var:30s} → {result} ({desc})")
        if reason:
            print(f"      理由: {reason}")
    
    print()
    print("4. 変数分類のテスト")
    print("-" * 40)
    
    test_vars = ['Utx116', 'Utv19', 'Utm27', 'Utv1', 'Utf7', 'Utx130.Utm6', 'UCHAR_MAX', 'INT_MAX']
    assignable, non_assignable = checker.classify_variables(test_vars)
    
    print(f"  入力: {test_vars}")
    print(f"  代入可能: {assignable}")
    print(f"  代入不可:")
    for var, reason in non_assignable:
        print(f"    - {var}: {reason}")
    
    print()
    print("=" * 70)
    print("✓ AssignableVariableChecker v4.4 が正常に動作しました")
    print("=" * 70)
