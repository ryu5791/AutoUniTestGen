"""
TestFunctionGeneratorモジュール

Unityテスト関数を生成

v3.3.0: ValueResolverを使用してTODOコメントを解消
v4.2.0: ローカル変数/構造体メンバー/数値リテラル対応
v4.3.1: ローカル変数へのアクセスをTODOコメント化、構造体メンバーパス抽出を修正
v4.3.3.1: AssignableVariableCheckerによる代入可能判定の一元化
v4.5: 配列変数への直接代入防止、条件式からの配列変数検出
"""

import sys
import os
import re
from typing import List, Dict, Optional, Set

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger, sanitize_identifier
from src.data_structures import TestCase, ParsedData, Condition, ConditionType
from src.test_generator.boundary_value_calculator import BoundaryValueCalculator
from src.test_generator.comment_generator import CommentGenerator
from src.test_generator.value_resolver import ValueResolver
from src.test_generator.assignable_variable_checker import AssignableVariableChecker


class TestFunctionGenerator:
    """テスト関数ジェネレータ"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.boundary_calc = BoundaryValueCalculator()
        self.comment_gen = CommentGenerator()
    
    def generate_test_function(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        テスト関数を生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            テスト関数のコード
        """
        lines = []
        
        # ヘッダコメント
        comment = self.comment_gen.generate_comment(test_case, parsed_data)
        lines.append(comment)
        
        # 関数名を生成
        func_name = self._generate_test_name(test_case, parsed_data)
        
        # 関数定義
        lines.append(f"void {func_name}(void) {{")
        
        # 変数初期化
        init_code = self._generate_variable_init(test_case, parsed_data)
        if init_code:
            lines.append(init_code)
        
        # モック設定
        mock_setup = self._generate_mock_setup(test_case, parsed_data)
        if mock_setup:
            lines.append(mock_setup)
        
        # 対象関数呼び出し
        lines.append(f"    // 対象関数を実行")
        
        # v4.1.3: パラメータを構築（戻り値の有無に関係なく）
        param_str = self._build_function_call_params(parsed_data)
        
        # 戻り値がある場合は result 変数に代入
        if parsed_data.function_info and parsed_data.function_info.return_type != 'void':
            lines.append(f"    result = {parsed_data.function_name}({param_str});")
        else:
            lines.append(f"    {parsed_data.function_name}({param_str});")
        
        lines.append("")
        
        # アサーション
        assertions = self._generate_assertions(test_case, parsed_data)
        if assertions:
            lines.append(assertions)
        
        # 呼び出し回数チェック
        call_count_check = self._generate_call_count_check(test_case, parsed_data)
        if call_count_check:
            lines.append(call_count_check)
        
        # 関数終了
        lines.append("}")
        
        return '\n'.join(lines)
    
    def _build_function_call_params(self, parsed_data: ParsedData) -> str:
        """
        対象関数呼び出し時のパラメータ文字列を構築（v4.1.3追加）
        
        Args:
            parsed_data: 解析済みデータ
        
        Returns:
            パラメータ文字列（例: "Utv1, Utv2" または ""）
        """
        if not parsed_data.function_info or not parsed_data.function_info.parameters:
            return ""
        
        params = []
        for param in parsed_data.function_info.parameters:
            param_name = param.get('name', '')
            if param_name:
                params.append(param_name)
        
        return ', '.join(params)
    
    def _generate_test_name(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        テスト名を生成
        
        ルール: test_[番号]_[判定文]_[真偽]
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            テスト関数名
        """
        # テスト番号（2桁）
        test_no = f"{test_case.no:02d}"
        
        # 判定文から識別子を生成
        # 対応する条件を検索
        matching_condition = None
        for cond in parsed_data.conditions:
            if cond.expression in test_case.condition:
                matching_condition = cond
                break
        
        if matching_condition:
            # 条件式から主要な変数や演算を抽出
            condition_part = self._extract_condition_identifier(matching_condition)
        else:
            # フォールバック
            condition_part = "condition"
        
        # 真偽パターン
        truth_part = test_case.truth.replace(' ', '') if test_case.truth else "test"
        
        # 組み合わせ
        func_name = f"test_{test_no}_{condition_part}_{truth_part}"
        
        # 識別子として有効な形に
        func_name = sanitize_identifier(func_name)
        
        # 長すぎる場合は短縮
        if len(func_name) > 60:
            func_name = func_name[:60]
        
        return func_name
    
    def _extract_condition_identifier(self, condition: Condition) -> str:
        """
        条件から識別子を抽出
        
        Args:
            condition: 条件
        
        Returns:
            識別子
        """
        expr = condition.expression
        
        # 括弧や空白を削除
        expr = expr.replace('(', '').replace(')', '').replace(' ', '_')
        
        # 演算子を置換
        replacements = {
            '==': 'eq',
            '!=': 'ne',
            '>=': 'ge',
            '<=': 'le',
            '>': 'gt',
            '<': 'lt',
            '||': 'or',
            '&&': 'and',
            '&': 'and',
            '|': 'or',
            '[': '_',
            ']': '',
        }
        
        for old, new in replacements.items():
            expr = expr.replace(old, new)
        
        # 複数のアンダースコアを1つに
        expr = re.sub(r'_+', '_', expr)
        
        # 先頭と末尾のアンダースコアを削除
        expr = expr.strip('_')
        
        # 長さ制限
        if len(expr) > 40:
            # 最初の変数名を優先
            parts = expr.split('_')
            if parts:
                expr = '_'.join(parts[:3])  # 最初の3パーツ
        
        return expr
    
    def _generate_variable_init(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        変数初期化コードを生成
        
        v4.2.0: ローカル変数、構造体メンバー、数値リテラル対応
        v4.8.6: const char*型パラメータの初期化を配列形式に変更
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コード
        """
        lines = []
        lines.append("    // 変数を初期化")
        
        # 戻り値がある場合は result 変数を初期化
        if parsed_data.function_info and parsed_data.function_info.return_type != 'void':
            return_type = parsed_data.function_info.return_type
            # ポインタ型の場合は NULL、それ以外は 0 または {0}
            if '*' in return_type:
                lines.append(f"    {return_type} result = NULL;")
            else:
                # 構造体や配列の場合は {0}、それ以外は 0
                # 型名に _t が含まれる、または大文字で始まる場合は構造体と判断
                if '_t' in return_type or (return_type and return_type[0].isupper()):
                    lines.append(f"    {return_type} result = {{0}};")
                else:
                    lines.append(f"    {return_type} result = 0;")
        
        # v4.8.6: 条件に応じた初期値を事前計算（const char*用）
        param_init_values = self._precompute_param_init_values(test_case, parsed_data)
        
        # パラメータの初期化
        if parsed_data.function_info and parsed_data.function_info.parameters:
            for param in parsed_data.function_info.parameters:
                param_name = param.get('name', '')
                param_type = param.get('type', 'int')
                
                # input_values から値を取得
                if hasattr(test_case, 'input_values') and test_case.input_values:
                    if param_name in test_case.input_values:
                        value = test_case.input_values[param_name]
                        # 型定義を追加
                        if '_t' in param_type or (param_type and param_type[0].isupper()):
                            lines.append(f"    {param_type} {param_name} = {{{value}}};")
                        else:
                            lines.append(f"    {param_type} {param_name} = {value};")
                        continue
                
                # v4.8.6: const char*型の特別処理
                if 'const' in param_type and 'char' in param_type and '*' in param_type:
                    # 事前計算された初期値があれば使用
                    if param_name in param_init_values:
                        init_value = param_init_values[param_name]
                        # 文字列リテラルの場合は配列形式で宣言
                        if init_value.startswith('"'):
                            lines.append(f"    const char {param_name}[] = {init_value};")
                        elif init_value == 'NULL':
                            # NULLの場合はポインタとして宣言（テスト目的でNULLを渡す場合）
                            lines.append(f"    const char* {param_name} = NULL;")
                        elif init_value.startswith('{') and init_value.endswith('}'):
                            # 配列初期化形式の場合はそのまま使用
                            lines.append(f"    const char {param_name}[] = {init_value};")
                        elif init_value.isdigit() or (init_value.startswith('-') and init_value[1:].isdigit()):
                            # 数値の場合は文字コードとして配列初期化
                            lines.append(f"    const char {param_name}[] = {{{init_value}, 0}};")
                        else:
                            # その他（文字列として扱う）
                            lines.append(f"    const char {param_name}[] = \"{init_value}\";")
                    else:
                        # デフォルトは空文字列
                        lines.append(f"    const char {param_name}[] = \"\";")
                    continue
                
                # デフォルト値を設定
                if '*' in param_type:
                    lines.append(f"    {param_type} {param_name} = NULL;")
                else:
                    # 構造体や配列の場合は {0}、それ以外は 0
                    if '_t' in param_type or (param_type and param_type[0].isupper()):
                        lines.append(f"    {param_type} {param_name} = {{0}};")
                    else:
                        lines.append(f"    {param_type} {param_name} = 0;")
        
        # 対応する条件を検索
        matching_condition = None
        for cond in parsed_data.conditions:
            if cond.expression in test_case.condition:
                matching_condition = cond
                break
        
        if not matching_condition:
            lines.append("")
            return '\n'.join(lines)
        
        # v4.5: 条件式を取得（配列変数検出用）
        condition_expr = matching_condition.expression
        
        # 条件タイプに応じて初期化コードを生成
        # v4.8.6: const char*型のパラメータへの代入はスキップ（既に宣言時に初期化済み）
        const_char_params = set()
        if parsed_data.function_info and parsed_data.function_info.parameters:
            for param in parsed_data.function_info.parameters:
                param_type = param.get('type', '')
                if 'const' in param_type and 'char' in param_type and '*' in param_type:
                    const_char_params.add(param.get('name', ''))
        
        if matching_condition.type == ConditionType.SIMPLE_IF:
            init = self._generate_simple_condition_init(matching_condition, test_case.truth, parsed_data)
            init = self._filter_const_char_init(init, const_char_params)
            init = self._process_init_code(init, parsed_data, lines, condition_expr)
            if init:
                self._append_init_line(init, lines)
        
        elif matching_condition.type == ConditionType.OR_CONDITION:
            init_list = self._generate_or_condition_init(matching_condition, test_case.truth, parsed_data)
            for init in init_list:
                init = self._filter_const_char_init(init, const_char_params)
                init = self._process_init_code(init, parsed_data, lines, condition_expr)
                if init:
                    self._append_init_line(init, lines)
        
        elif matching_condition.type == ConditionType.AND_CONDITION:
            init_list = self._generate_and_condition_init(matching_condition, test_case.truth, parsed_data)
            for init in init_list:
                init = self._filter_const_char_init(init, const_char_params)
                init = self._process_init_code(init, parsed_data, lines, condition_expr)
                if init:
                    self._append_init_line(init, lines)
        
        elif matching_condition.type == ConditionType.SWITCH:
            init = self._generate_switch_init(matching_condition, test_case, parsed_data)
            init = self._filter_const_char_init(init, const_char_params)
            init = self._process_init_code(init, parsed_data, lines, condition_expr)
            if init:
                self._append_init_line(init, lines)
        
        lines.append("")
        return '\n'.join(lines)
    
    def _precompute_param_init_values(self, test_case: TestCase, parsed_data: ParsedData) -> Dict[str, str]:
        """
        const char*型パラメータの初期値を事前計算（v4.8.6追加）
        
        AND条件: 両方を満たす値が必要（後の条件を優先）
        OR条件: 真の条件の値を優先
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            パラメータ名 -> 初期値のマッピング
        """
        result = {}
        
        # 対応する条件を検索
        matching_condition = None
        for cond in parsed_data.conditions:
            if cond.expression in test_case.condition:
                matching_condition = cond
                break
        
        if not matching_condition:
            return result
        
        # 条件タイプに応じて初期化値を取得
        if matching_condition.type == ConditionType.SIMPLE_IF:
            init = self._generate_simple_condition_init(matching_condition, test_case.truth, parsed_data)
            self._extract_param_value(init, result)
        
        elif matching_condition.type == ConditionType.AND_CONDITION:
            # AND条件: 全ての条件を満たす必要がある → 後の条件の値を優先
            # (両方の条件を満たす値が必要なので、より制約の強い後の条件を使用)
            init_list = self._generate_or_condition_init(matching_condition, test_case.truth, parsed_data)
            # 後の条件から順に処理（後の値が優先される）
            for init in init_list:
                self._extract_param_value_overwrite(init, result)
        
        elif matching_condition.type == ConditionType.OR_CONDITION:
            # OR条件: いずれかの条件を満たせばよい → 真の条件の値を優先
            init_list = self._generate_or_condition_init(matching_condition, test_case.truth, parsed_data)
            true_result = {}
            false_result = {}
            truth_str = test_case.truth
            for i, init in enumerate(init_list):
                if i < len(truth_str):
                    if truth_str[i] == 'T':
                        self._extract_param_value(init, true_result)
                    else:
                        self._extract_param_value(init, false_result)
            # 真の条件の値を優先
            for key, value in true_result.items():
                result[key] = value
            for key, value in false_result.items():
                if key not in result:
                    result[key] = value
        
        elif matching_condition.type == ConditionType.SWITCH:
            init = self._generate_switch_init(matching_condition, test_case, parsed_data)
            self._extract_param_value(init, result)
        
        return result
    
    def _extract_param_value_overwrite(self, init: Optional[str], result: Dict[str, str]) -> None:
        """
        初期化コードからパラメータ名と値を抽出（上書きあり版）（v4.8.6追加）
        
        Args:
            init: 初期化コード
            result: 結果を格納する辞書（既存の値は上書きされる）
        """
        if not init or init.startswith('//'):
            return
        
        # "変数[n] = 値" 形式（switch文用）
        array_match = re.match(r'(\w+)\[(\d+)\]\s*=\s*(.+?)\s*;', init)
        if array_match:
            var_name = array_match.group(1).strip()
            index = int(array_match.group(2))
            value = array_match.group(3).strip()
            if '//' in value:
                value = value.split('//')[0].strip()
            if index == 0:
                if value.isdigit():
                    result[var_name] = f'{{{value}, 0}}'
                elif value.startswith("'") and value.endswith("'"):
                    char_val = value[1:-1]
                    result[var_name] = f'"{char_val}"'
                else:
                    result[var_name] = f'{{{value}, 0}}'
            return
        
        # "変数 = 値" 形式から抽出
        match = re.match(r'(\w+)\s*=\s*(.+?)\s*;', init)
        if match:
            var_name = match.group(1).strip()
            value = match.group(2).strip()
            if '//' in value:
                value = value.split('//')[0].strip()
            result[var_name] = value  # 上書き
    
    def _extract_param_value(self, init: Optional[str], result: Dict[str, str]) -> None:
        """
        初期化コードからパラメータ名と値を抽出（v4.8.6追加）
        
        Args:
            init: 初期化コード（例: 'command = "test_string";' または 'command[0] = 999;'）
            result: 結果を格納する辞書
        """
        if not init or init.startswith('//'):
            return
        
        # "変数[n] = 値" 形式（switch文用）
        array_match = re.match(r'(\w+)\[(\d+)\]\s*=\s*(.+?)\s*;', init)
        if array_match:
            var_name = array_match.group(1).strip()
            index = int(array_match.group(2))
            value = array_match.group(3).strip()
            # コメントを除去
            if '//' in value:
                value = value.split('//')[0].strip()
            # 既に値が設定されている場合はスキップ（最初の値を優先）
            if var_name in result:
                return
            # 配列要素への代入は、その要素を持つ配列として初期化
            # 例: command[0] = 'f' -> command = "f" または command = {'f', 0}
            if index == 0:
                # 数値の場合は文字コードとして扱う
                if value.isdigit():
                    result[var_name] = f'{{{value}, 0}}'
                elif value.startswith("'") and value.endswith("'"):
                    # 文字リテラルの場合
                    char_val = value[1:-1]
                    result[var_name] = f'"{char_val}"'
                else:
                    result[var_name] = f'{{{value}, 0}}'
            return
        
        # "変数 = 値" 形式から抽出
        match = re.match(r'(\w+)\s*=\s*(.+?)\s*;', init)
        if match:
            var_name = match.group(1).strip()
            value = match.group(2).strip()
            # コメントを除去
            if '//' in value:
                value = value.split('//')[0].strip()
            # 既に値が設定されている場合はスキップ（最初の値を優先）
            if var_name in result:
                return
            result[var_name] = value
    
    def _filter_const_char_init(self, init: Optional[str], const_char_params: set) -> Optional[str]:
        """
        const char*型パラメータへの代入をフィルタ（v4.8.6追加）
        
        Args:
            init: 初期化コード
            const_char_params: const char*型パラメータ名のセット
        
        Returns:
            フィルタ後の初期化コード（const char*への代入はNone）
        """
        if not init or init.startswith('//'):
            return init
        
        # "変数 = 値" または "変数[n] = 値" 形式から変数名を抽出
        match = re.match(r'(\w+)(?:\[\d+\])?\s*=', init)
        if match:
            var_name = match.group(1).strip()
            if var_name in const_char_params:
                # const char*型パラメータへの代入はスキップ（既に宣言時に初期化済み）
                return None
        
        return init
    
    def _process_init_code(self, init: Optional[str], parsed_data: ParsedData, lines: List[str], 
                            condition_expr: str = None) -> Optional[str]:
        """
        初期化コードを処理（ローカル変数・構造体メンバー・数値リテラル対応）
        
        v4.2.0追加
        v4.3.1修正: ローカル変数へのアクセスをTODOコメント化（テスト関数外から直接初期化不可）
                   右辺の値にローカル変数が含まれる場合もTODOコメント化
        v4.3.3修正: 配列インデックス変数自体への代入を防止（問題E対応）
                   構造体メンバー名への代入を防止（問題B対応）
        v4.3.3.1: AssignableVariableCheckerを使用した一元的な判定
        v4.5: 条件式から配列変数を検出して登録
        
        Args:
            init: 生成された初期化コード
            parsed_data: 解析済みデータ
            lines: 出力行リスト（ローカル変数宣言追加用）
            condition_expr: 元の条件式（配列変数検出用）
        
        Returns:
            処理後の初期化コード（またはNone）
        """
        if not init:
            return None
        
        # コメントの場合はそのまま返す
        if init.strip().startswith('//'):
            return init
        
        # "変数 = 値" 形式から変数名を抽出
        match = re.match(r'([\w\.]+(?:\[\w+\])?(?:\.[\w]+)*)\s*=\s*(.+)', init)
        if not match:
            return init
        
        var_part = match.group(1).strip()
        value_part = match.group(2).strip()
        
        # AssignableVariableCheckerを使用して判定
        checker = AssignableVariableChecker(parsed_data)
        
        # v4.5: 条件式から配列変数を検出して登録
        if condition_expr:
            checker.detect_array_from_condition(condition_expr)
        
        # 左辺（代入先）が代入可能かチェック
        if not checker.is_assignable(var_part):
            reason = checker.get_reason(var_part)
            return f"// TODO: {reason}"
        
        # 右辺の値にローカル変数が含まれるかチェック
        value_local_var = self._check_value_for_local_variables_v2(value_part, checker)
        if value_local_var:
            return f"// TODO: {value_local_var} は対象関数内のローカル変数です。テスト値を明示的に設定してください。\n    // {init}"
        
        return init
    
    def _check_value_for_local_variables_v2(self, value_part: str, checker: AssignableVariableChecker) -> Optional[str]:
        """
        値の部分にローカル変数が含まれているかチェック（v4.3.3.1版）
        
        Args:
            value_part: 値の部分（例: "Utx204.Utm1.Utm33", "100", "GlobalVar"）
            checker: AssignableVariableCheckerインスタンス
        
        Returns:
            ローカル変数名（見つかった場合）、なければNone
        """
        # セミコロンやコメントを除去
        clean_value = value_part.split(';')[0].split('//')[0].strip()
        
        # 数値の場合はスキップ
        if clean_value.isdigit() or (clean_value.startswith('-') and len(clean_value) > 1 and clean_value[1:].isdigit()):
            return None
        if clean_value.startswith('0x') or clean_value.startswith('0X'):
            return None
        
        # v4.8.5: 文字列リテラルの場合はスキップ（"..." で囲まれた値）
        if clean_value.startswith('"') and clean_value.endswith('"'):
            return None
        
        # v4.8.5: NULLの場合はスキップ
        if clean_value == 'NULL':
            return None
        
        # v4.8.5: キャスト式の場合はスキップ（例: (const char*)0x12345678）
        if clean_value.startswith('(') and ')' in clean_value:
            return None
        
        # 構造体メンバーパスの場合、ルート変数をチェック
        if '.' in clean_value:
            root_var = clean_value.split('.')[0]
            root_var = re.sub(r'\[\w+\]', '', root_var)
            
            reason_code = checker.get_reason_code(root_var)
            if reason_code in [AssignableVariableChecker.REASON_LOCAL_VARIABLE,
                              AssignableVariableChecker.REASON_LOOP_VARIABLE,
                              AssignableVariableChecker.REASON_UNKNOWN_LOCAL]:
                return root_var
        else:
            # 単独の変数名
            clean_var = re.sub(r'\[\w+\]', '', clean_value)
            reason_code = checker.get_reason_code(clean_var)
            if reason_code in [AssignableVariableChecker.REASON_LOCAL_VARIABLE,
                              AssignableVariableChecker.REASON_LOOP_VARIABLE,
                              AssignableVariableChecker.REASON_UNKNOWN_LOCAL]:
                return clean_var
        
        return None
    
    def _check_value_for_local_variables(self, value_part: str, parsed_data: ParsedData) -> Optional[str]:
        """
        値の部分にローカル変数が含まれているかチェック
        
        v4.3.1追加
        
        Args:
            value_part: 値の部分（例: "Utx204.Utm1.Utm33", "100", "GlobalVar"）
            parsed_data: 解析済みデータ
        
        Returns:
            ローカル変数名（見つかった場合）、なければNone
        """
        # セミコロンやコメントを除去
        clean_value = value_part.split(';')[0].split('//')[0].strip()
        
        # 数値の場合はスキップ
        if clean_value.isdigit() or (clean_value.startswith('-') and clean_value[1:].isdigit()):
            return None
        if clean_value.startswith('0x') or clean_value.startswith('0X'):
            return None
        
        # 構造体メンバーパスの場合、ルート変数をチェック
        if '.' in clean_value:
            root_var = clean_value.split('.')[0]
            root_var = re.sub(r'\[\w+\]', '', root_var)
            
            if self._is_local_variable(root_var, parsed_data):
                return root_var
            if self._is_unknown_variable(root_var, parsed_data):
                return root_var
        else:
            # 単独の変数名
            clean_var = re.sub(r'\[\w+\]', '', clean_value)
            if self._is_local_variable(clean_var, parsed_data):
                return clean_var
            if self._is_unknown_variable(clean_var, parsed_data):
                return clean_var
        
        return None
    
    def _extract_array_index_variables(self, expression: str) -> List[str]:
        """
        配列アクセスのインデックス変数を抽出
        
        v4.3.1追加
        
        Args:
            expression: 式（例: "Utv12[Utv19]", "arr[i].member"）
        
        Returns:
            インデックス変数名のリスト（数値は除外）
        
        Examples:
            >>> _extract_array_index_variables("Utv12[Utv19]")
            ["Utv19"]
            >>> _extract_array_index_variables("arr[0].member")
            []
        """
        pattern = r'\[([a-zA-Z_]\w*)\]'
        matches = re.findall(pattern, expression)
        # 数値は除外
        return [m for m in matches if not m.isdigit()]
    
    def _append_init_line(self, init: str, lines: List[str]) -> None:
        """
        初期化行をリストに追加（セミコロン処理）
        
        Args:
            init: 初期化コード
            lines: 出力行リスト
        """
        # セミコロンの前のコメントを考慮してチェック
        code_part = init.split('//')[0].rstrip()
        if code_part and not code_part.endswith(';'):
            lines.append(f"    {init};")
        else:
            lines.append(f"    {init}")
    
    def _is_local_variable(self, var_name: str, parsed_data: ParsedData) -> bool:
        """
        変数がローカル変数かどうかを判定
        
        v4.2.0追加
        
        Args:
            var_name: 変数名
            parsed_data: 解析済みデータ
        
        Returns:
            ローカル変数の場合True
        """
        # local_variables属性が存在するかチェック
        if not hasattr(parsed_data, 'local_variables') or not parsed_data.local_variables:
            return False
        
        return var_name in parsed_data.local_variables
    
    def _is_unknown_variable(self, var_name: str, parsed_data: ParsedData) -> bool:
        """
        変数が未知の変数かどうかを判定（ローカル変数と推測）
        
        v4.3.1追加
        
        グローバル変数リストにもローカル変数リストにも存在しない変数は、
        対象関数内のローカル変数である可能性が高い。
        
        Args:
            var_name: 変数名
            parsed_data: 解析済みデータ
        
        Returns:
            未知の変数（ローカル変数と推測）の場合True
        """
        # 関数名やenum定数はスキップ
        if self._is_function_or_enum(var_name, parsed_data):
            return False
        
        # パラメータはスキップ
        if parsed_data.function_info and parsed_data.function_info.parameters:
            param_names = [p.get('name', '') for p in parsed_data.function_info.parameters]
            if var_name in param_names:
                return False
        
        # グローバル変数リストに存在するかチェック
        if hasattr(parsed_data, 'variables') and parsed_data.variables:
            global_var_names = [v.name for v in parsed_data.variables]
            if var_name in global_var_names:
                return False
        
        # グローバル変数名リストに存在するかチェック
        if var_name in parsed_data.global_variables:
            return False
        
        # ローカル変数リストに存在するかチェック
        if hasattr(parsed_data, 'local_variables') and parsed_data.local_variables:
            if var_name in parsed_data.local_variables:
                return False  # _is_local_variableでTrue判定されるはず
        
        # どのリストにも存在しない場合は未知（ローカル変数と推測）
        return True
    
    def _is_struct_member_name(self, var_name: str, parsed_data: ParsedData) -> bool:
        """
        識別子が構造体メンバー名かどうかを判定
        
        v4.3.3追加（問題B対応）
        
        Args:
            var_name: 識別子名
            parsed_data: 解析済みデータ
        
        Returns:
            構造体メンバー名の場合True
        """
        # 構造体定義から全てのメンバー名を収集
        if not hasattr(parsed_data, 'struct_definitions') or not parsed_data.struct_definitions:
            return False
        
        for struct_def in parsed_data.struct_definitions:
            for member in struct_def.members:
                if member.name == var_name:
                    return True
                # ネストした構造体もチェック
                if member.nested_struct:
                    for nested_member in member.nested_struct.members:
                        if nested_member.name == var_name:
                            return True
        
        return False
    
    def _is_array_index_variable(self, var_name: str, parsed_data: ParsedData) -> bool:
        """
        変数が配列インデックス変数（ループ変数）かどうかを判定
        
        v4.3.3追加（問題E対応）
        
        Args:
            var_name: 変数名
            parsed_data: 解析済みデータ
        
        Returns:
            配列インデックス変数の場合True
        """
        # ローカル変数情報を取得
        if not hasattr(parsed_data, 'local_variables') or not parsed_data.local_variables:
            return False
        
        local_var_info = parsed_data.local_variables.get(var_name)
        if local_var_info and hasattr(local_var_info, 'is_loop_variable') and local_var_info.is_loop_variable:
            return True
        
        return False
    
    def _get_local_variable_info(self, var_name: str, parsed_data: ParsedData):
        """
        ローカル変数の情報を取得
        
        v4.2.0追加
        
        Args:
            var_name: 変数名
            parsed_data: 解析済みデータ
        
        Returns:
            LocalVariableInfo または None
        """
        if not hasattr(parsed_data, 'local_variables') or not parsed_data.local_variables:
            return None
        
        return parsed_data.local_variables.get(var_name)
    
    def _generate_simple_condition_init(self, condition: Condition, truth: str, parsed_data: ParsedData) -> Optional[str]:
        """
        単純条件の初期化コードを生成
        
        Args:
            condition: 条件
            truth: 真偽
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コード
        """
        # v4.5: parsed_dataを渡してビットフィールド情報を利用
        test_value = self.boundary_calc.generate_test_value_with_parsed_data(
            condition.expression, truth, parsed_data)
        
        if test_value:
            # 関数呼び出しが含まれる場合はTODOコメントとしてそのまま返す
            if test_value.startswith("//"):
                return test_value
            
            # ビットフィールドの場合はマスク処理を追加
            test_value = self._apply_bitfield_mask(test_value, parsed_data)
            # 生成された初期化コードが関数やenum定数を使っていないか検証
            test_value = self._validate_and_fix_init_code(test_value, parsed_data)
            return test_value
        
        # 境界値計算できない場合
        variables = self.boundary_calc.extract_variables(condition.expression)
        if variables:
            var = variables[0]
            
            # 関数呼び出しかチェック（例: Utf12()）
            if self._is_function_call_pattern(var):
                # 関数呼び出しは変数として初期化できない
                func_name = var.replace('()', '').strip()
                return f"// mock_{func_name}_return_value を設定してください"
            
            # 関数かenum定数でないことを確認
            if self._is_function_or_enum(var, parsed_data):
                return f"// {var}は関数またはenum定数のため初期化できません"
            
            # v3.3.0: ValueResolverを使用してTODOを解消
            value_resolver = ValueResolver(parsed_data)
            
            # ビットフィールドかチェック
            if var in parsed_data.bitfields:
                bitfield = parsed_data.bitfields[var]
                bit_width = bitfield.bit_width
                init_val, comment = value_resolver.get_bitfield_init_value(truth, bit_width)
                return f"{var} = {init_val};  // {comment}"
            
            # 通常のブール条件
            init_val, comment = value_resolver.get_boolean_init_value(truth)
            return f"{var} = {init_val};  // {comment}"
        
        return None
    
    def _is_function_call_pattern(self, identifier: str) -> bool:
        """
        識別子が関数呼び出しパターンかどうかを判定
        
        Args:
            identifier: 識別子文字列
        
        Returns:
            関数呼び出しの場合True
        """
        return bool(re.match(r'\w+\s*\(\s*.*?\s*\)$', identifier.strip()))
    
    def _apply_bitfield_mask(self, init_code: str, parsed_data: ParsedData) -> str:
        """
        ビットフィールドの場合、マスク処理を追加
        
        Args:
            init_code: 初期化コード（例: "internal = 255"）
            parsed_data: 解析済みデータ
        
        Returns:
            マスク処理を追加した初期化コード
        """
        # 初期化コードから変数名と値を抽出
        match = re.match(r'(\w+)\s*=\s*(\d+)', init_code)
        if not match:
            return init_code
        
        var_name = match.group(1)
        value = int(match.group(2))
        
        # ビットフィールドかチェック
        if var_name not in parsed_data.bitfields:
            return init_code
        
        bitfield = parsed_data.bitfields[var_name]
        max_value = bitfield.get_max_value()
        
        # 値がビット幅を超えている場合は警告コメントを追加
        if value > max_value:
            masked_value = value & max_value
            return f"{var_name} = 0x{masked_value:X}  /* 元の値: {value}, {bitfield.bit_width}ビットでマスク */"
        
        # 値が範囲内の場合は16進数表記に変換
        if value > 9:
            return f"{var_name} = 0x{value:X}  /* {bitfield.bit_width}ビットフィールド */"
        
        return f"{var_name} = {value}  /* {bitfield.bit_width}ビットフィールド */"
    
    def _generate_or_condition_init(self, condition: Condition, truth: str, parsed_data: ParsedData) -> List[str]:
        """
        OR条件の初期化コードを生成
        
        Args:
            condition: 条件
            truth: 真偽パターン
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コードのリスト
        """
        init_list = []
        
        conditions = condition.conditions if condition.conditions else [condition.left, condition.right]
        
        # v3.3.0: ValueResolverを使用
        value_resolver = ValueResolver(parsed_data)
        
        # v4.8.5: 標準ライブラリ関数名（変数として誤検出されるのを防止）
        stdlib_funcs = {
            'strlen', 'strcmp', 'strncmp', 'strcpy', 'strncpy', 'strcat', 'strncat',
            'memcpy', 'memset', 'memcmp', 'memmove',
            'printf', 'sprintf', 'fprintf', 'scanf', 'sscanf', 'fscanf',
            'malloc', 'calloc', 'realloc', 'free',
            'atoi', 'atol', 'atof', 'strtol', 'strtoul', 'strtod',
            'abs', 'labs', 'fabs',
            'isdigit', 'isalpha', 'isalnum', 'isspace', 'isupper', 'islower',
            'toupper', 'tolower',
            'fopen', 'fclose', 'fread', 'fwrite', 'fgets', 'fputs', 'fflush',
            'sizeof', 'offsetof'
        }
        
        # 各条件に対して値を設定
        for i, cond in enumerate(conditions):
            if i < len(truth):
                truth_val = truth[i]
                test_value = self.boundary_calc.generate_test_value_with_parsed_data(cond, truth_val, parsed_data)
                
                if test_value:
                    # 関数呼び出しが含まれる場合はコメントとしてそのまま追加
                    if test_value.startswith("//"):
                        init_list.append(test_value)
                    else:
                        # 関数やenum定数の誤使用を修正
                        test_value = self._validate_and_fix_init_code(test_value, parsed_data)
                        init_list.append(test_value)
                else:
                    # デフォルト値
                    variables = self.boundary_calc.extract_variables(cond)
                    if variables:
                        # v4.8.5: 標準ライブラリ関数名を除外
                        valid_vars = [v for v in variables if v not in stdlib_funcs]
                        if not valid_vars:
                            # すべての変数が関数名の場合、条件式に含まれる関数のモック設定を提案
                            func_names = [v for v in variables if v in stdlib_funcs]
                            if func_names:
                                init_list.append(f"// {func_names[0]}() の戻り値でテスト条件が決まります")
                            continue
                        
                        var = valid_vars[0]
                        
                        # 関数呼び出しかチェック
                        if self._is_function_call_pattern(var):
                            func_name = var.replace('()', '').strip()
                            init_list.append(f"// mock_{func_name}_return_value を設定してください")
                            continue
                        
                        # 関数またはenum定数でないことを確認
                        if self._is_function_or_enum(var, parsed_data):
                            init_list.append(f"// {var}は関数またはenum定数のため初期化できません")
                        else:
                            # v3.3.0: ValueResolverを使用
                            init_val, comment = value_resolver.get_boolean_init_value(truth_val)
                            init_list.append(f"{var} = {init_val};  // {comment}")
        
        return init_list
    
    def _generate_and_condition_init(self, condition: Condition, truth: str, parsed_data: ParsedData) -> List[str]:
        """
        AND条件の初期化コードを生成
        
        Args:
            condition: 条件
            truth: 真偽パターン
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コードのリスト
        """
        # OR条件と同じロジック
        return self._generate_or_condition_init(condition, truth, parsed_data)
    
    def _generate_switch_init(self, condition: Condition, test_case: TestCase, parsed_data: ParsedData) -> Optional[str]:
        """
        switch文の初期化コードを生成
        
        Args:
            condition: 条件
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コード
        """
        switch_var = condition.expression
        
        # default caseの場合（先にチェック）
        if 'case default' in test_case.condition.lower() or test_case.condition.lower().endswith('default'):
            # caseに該当しない値を設定（999など）
            return f"{switch_var} = 999;  // default: caseに該当しない値"
        
        # 通常のcase値を抽出
        match = re.search(r'case\s+(\w+)', test_case.condition)
        if match:
            case_value = match.group(1)
            
            # case_valueが関数またはenum定数かチェック
            if self._is_function(case_value, parsed_data):
                # 関数の場合はモックの戻り値を使用
                return f"{switch_var} = mock_{case_value}_return_value"
            elif self._is_enum_constant(case_value, parsed_data):
                # enum定数の場合は別の変数に代入
                return f"{switch_var} = {case_value}"
            else:
                return f"{switch_var} = {case_value}"
        
        return None


    def _generate_mock_setup(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        モック設定コードを生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            モック設定コード
        """
        lines = []
        
        if not parsed_data.external_functions:
            return ""
        
        # 外部関数のモック戻り値を設定（デフォルト値以外のみ）
        mock_settings = []
        for func_name in parsed_data.external_functions:
            # 戻り値を決定
            return_value = self._determine_mock_return_value(
                func_name, test_case, parsed_data
            )
            # デフォルト値（0）以外の場合のみ設定コードを追加
            if return_value != "0":
                mock_settings.append(f"    mock_{func_name}_return_value = {return_value};")
        
        # 設定が必要なモックがある場合のみコメントとコードを追加
        if mock_settings:
            lines.append("    // モックを設定")
            lines.extend(mock_settings)
            lines.append("")
        
        return '\n'.join(lines)
    
    def _determine_mock_return_value(self, func_name: str, test_case: TestCase, 
                                      parsed_data: ParsedData) -> str:
        """
        モック関数の戻り値を決定
        
        ロジック:
        1. 条件式に関数が含まれているか確認
        2. 含まれている場合、真偽パターンに応じて値を決定
           - 例: func() > 10 で T の場合 → 11
           - 例: func() > 10 で F の場合 → 10
        3. 含まれていない場合 → デフォルト値（0）
        
        Args:
            func_name: モック関数名
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            決定した戻り値（文字列）
        """
        # デフォルト値
        default_value = "0"
        
        # テストケースの条件を確認
        condition_expr = test_case.condition
        truth_value = test_case.truth
        
        if not condition_expr or func_name not in condition_expr:
            return default_value
        
        # 条件式を解析して適切な値を決定
        # パターン1: func() > N または func() >= N
        match = re.search(rf'{func_name}\s*\(\)\s*(>=?)\s*(\d+)', condition_expr)
        if match:
            operator = match.group(1)
            threshold = int(match.group(2))
            
            if truth_value == 'T':
                # 真の場合: 閾値より大きい値
                if operator == '>':
                    return str(threshold + 1)
                else:  # >=
                    return str(threshold)
            else:
                # 偽の場合: 閾値以下の値
                if operator == '>':
                    return str(threshold)
                else:  # >=
                    return str(threshold - 1)
        
        # パターン2: func() < N または func() <= N
        match = re.search(rf'{func_name}\s*\(\)\s*(<=?)\s*(\d+)', condition_expr)
        if match:
            operator = match.group(1)
            threshold = int(match.group(2))
            
            if truth_value == 'T':
                # 真の場合: 閾値より小さい値
                if operator == '<':
                    return str(threshold - 1)
                else:  # <=
                    return str(threshold)
            else:
                # 偽の場合: 閾値以上の値
                if operator == '<':
                    return str(threshold)
                else:  # <=
                    return str(threshold + 1)
        
        # パターン3: func() == N
        match = re.search(rf'{func_name}\s*\(\)\s*==\s*(\d+)', condition_expr)
        if match:
            value = int(match.group(1))
            if truth_value == 'T':
                return str(value)
            else:
                return str(value + 1)
        
        # パターン4: func() != N
        match = re.search(rf'{func_name}\s*\(\)\s*!=\s*(\d+)', condition_expr)
        if match:
            value = int(match.group(1))
            if truth_value == 'T':
                return str(value + 1)
            else:
                return str(value)
        
        # パターン5: 単純な関数呼び出し（真偽値として使用）
        if re.search(rf'{func_name}\s*\(\)', condition_expr):
            if truth_value == 'T':
                return "1"  # 真
            else:
                return "0"  # 偽
        
        return default_value
    
    def _is_struct_type(self, type_name: str) -> bool:
        """
        型が構造体かどうかを判定
        
        判定基準:
        1. _t で終わる（typedef struct の命名規則）
        2. 大文字で始まる（カスタム型の命名規則）
        3. 'struct' キーワードが含まれる
        
        Args:
            type_name: 型名
        
        Returns:
            構造体の場合True
        """
        if not type_name:
            return False
        
        # ポインタ記号を除去
        clean_type = type_name.replace('*', '').strip()
        
        # _t で終わる（typedef struct の命名規則）
        if clean_type.endswith('_t'):
            return True
        
        # 大文字で始まる（カスタム型）
        if clean_type and clean_type[0].isupper():
            return True
        
        # struct キーワードが含まれる
        if 'struct' in clean_type.lower():
            return True
        
        return False
    
    def _generate_assertions(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        アサーションコードを生成 (v2.8.0で拡張)
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            アサーションコード
        """
        lines = []
        lines.append("    // 結果を確認")
        lines.append("    // 期待値を設定してください")
        
        # 戻り値のチェック（void以外の場合）
        if parsed_data.function_info and parsed_data.function_info.return_type != 'void':
            return_type = parsed_data.function_info.return_type
            
            # 構造体型かチェック
            if self._is_struct_type(return_type):
                # v2.8.0: 構造体メンバーごとのアサーション生成
                struct_assertions = self._generate_struct_assertions(return_type, "result", parsed_data)
                if struct_assertions:
                    lines.extend(struct_assertions)
                else:
                    # 構造体定義が見つからない場合は従来のTODOコメント
                    lines.append("    // 例: TEST_ASSERT_EQUAL(expected_value, result.member_name);")
            else:
                # 基本型の場合
                expected_value = self._calculate_expected_return_value(test_case, parsed_data)
                if expected_value is not None:
                    lines.append(f"    TEST_ASSERT_EQUAL({expected_value}, result);")
        
        # グローバル変数のチェック
        for var in parsed_data.global_variables[:3]:  # 最初の3つ
            if not self._is_function_or_enum(var, parsed_data):
                expected_value = self._calculate_expected_variable_value(
                    var, test_case, parsed_data
                )
                if expected_value is not None:
                    lines.append(f"    TEST_ASSERT_EQUAL({expected_value}, {var});")
        
        lines.append("")
        
        return '\n'.join(lines)
    
    def _calculate_expected_return_value(self, test_case: TestCase, 
                                          parsed_data: ParsedData) -> Optional[str]:
        """
        戻り値の期待値を計算
        
        簡易実装:
        - 真の分岐 → 1 または定数値
        - 偽の分岐 → 0 または別の定数値
        - より高度な実装は将来のPhaseで
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            期待値（文字列）またはNone
        """
        # input_values と output_values から期待値を取得
        if hasattr(test_case, 'output_values') and test_case.output_values:
            # return value は 'result' というキーで格納されていることを想定
            if 'result' in test_case.output_values:
                return str(test_case.output_values['result'])
        
        # デフォルトの簡易計算
        # 真の分岐の場合は1、偽の分岐の場合は0を返す
        if test_case.truth == 'T':
            return "1"
        else:
            return "0"
    
    def _calculate_expected_variable_value(self, var: str, test_case: TestCase,
                                            parsed_data: ParsedData) -> Optional[str]:
        """
        変数の期待値を計算
        
        Args:
            var: 変数名
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            期待値（文字列）またはNone
        """
        # output_values から期待値を取得
        if hasattr(test_case, 'output_values') and test_case.output_values:
            if var in test_case.output_values:
                return str(test_case.output_values[var])
        
        # input_valuesに変数がある場合、その値が変更されていない可能性がある
        if hasattr(test_case, 'input_values') and test_case.input_values:
            if var in test_case.input_values:
                # 入力値がそのまま出力される可能性がある場合
                return str(test_case.input_values[var])
        
        # 期待値が計算できない場合はNoneを返す
        return None
    
    def _is_function_or_enum(self, identifier: str, parsed_data: ParsedData) -> bool:
        """
        識別子が関数またはenum定数かどうかを判定
        
        Args:
            identifier: 識別子
            parsed_data: 解析済みデータ
        
        Returns:
            関数またはenum定数の場合True
        """
        # 関数名のチェック
        if identifier in parsed_data.external_functions:
            return True
        
        # 対象関数自身のチェック
        if identifier == parsed_data.function_name:
            return True
        
        # enum定数のチェック
        if identifier in parsed_data.enum_values:
            return True
        
        return False
    
    def _generate_call_count_check(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        呼び出し回数チェックコードを生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            呼び出し回数チェックコード
        """
        lines = []
        lines.append("    // 呼び出し回数を確認")
        
        for func_name in parsed_data.external_functions:
            # 条件式に含まれているか確認
            if func_name in test_case.condition:
                expected_count = 1
            else:
                expected_count = 0
            
            lines.append(f"    TEST_ASSERT_EQUAL({expected_count}, mock_{func_name}_call_count);")
        
        lines.append("")
        return '\n'.join(lines)


    def _is_function(self, name: str, parsed_data: ParsedData) -> bool:
        """
        指定された名前が関数かどうか判定
        
        Args:
            name: 識別子名
            parsed_data: 解析済みデータ
        
        Returns:
            関数の場合True
        """
        return name in parsed_data.external_functions
    
    def _is_enum_constant(self, name: str, parsed_data: ParsedData) -> bool:
        """
        指定された名前がenum定数かどうか判定
        
        Args:
            name: 識別子名
            parsed_data: 解析済みデータ
        
        Returns:
            enum定数の場合True
        """
        return name in parsed_data.enum_values
    
    def _is_function_or_enum(self, name: str, parsed_data: ParsedData) -> bool:
        """
        指定された名前が関数またはenum定数かどうか判定
        
        Args:
            name: 識別子名
            parsed_data: 解析済みデータ
        
        Returns:
            関数またはenum定数の場合True
        """
        return self._is_function(name, parsed_data) or self._is_enum_constant(name, parsed_data)
    
    def _validate_and_fix_init_code(self, init_code: str, parsed_data: ParsedData) -> str:
        """
        初期化コードを検証して問題があれば修正
        
        v4.3.3修正: 構造体メンバー名・配列インデックス変数への代入を防止
        v4.3.3.1: AssignableVariableCheckerを使用した一元的な判定
        
        Args:
            init_code: 初期化コード
            parsed_data: 解析済みデータ
        
        Returns:
            修正後の初期化コード
        """
        # "変数 = 値" の形式から変数と値を抽出
        match = re.match(r'([\w\.]+(?:\[\w+\])?(?:\.[\w]+)*)\s*=\s*(.+)', init_code)
        if not match:
            return init_code
        
        var_name = match.group(1).strip()
        value_part = match.group(2).strip()
        
        # AssignableVariableCheckerを使用して判定
        checker = AssignableVariableChecker(parsed_data)
        
        # 変数が代入可能かチェック
        if not checker.is_assignable(var_name):
            reason = checker.get_reason(var_name)
            return f"// TODO: {reason}"
        
        # 値の部分に関数が含まれている場合
        if checker.is_function(value_part):
            # 関数の場合はモックの戻り値を使用
            return f"{var_name} = mock_{value_part}_return_value;  // 修正: {value_part}は関数"
        
        # 値の部分にenum定数が含まれている場合はそのまま（正しい使い方）
        
        return init_code
    
    def _generate_struct_assertions(self, type_name: str, var_name: str, 
                                   parsed_data: ParsedData) -> List[str]:
        """
        構造体メンバーごとのアサーションを生成 (v2.8.0で追加)
        
        Args:
            type_name: 構造体の型名
            var_name: 変数名（例: "result"）
            parsed_data: 解析済みデータ
        
        Returns:
            アサーションコードのリスト
        """
        lines = []
        
        # 構造体定義を検索
        struct_def = parsed_data.get_struct_definition(type_name)
        if not struct_def:
            return lines
        
        # すべてのメンバーをフラットに取得（ネスト対応）
        members = struct_def.get_all_members_flat()
        
        for access_path, member in members:
            full_path = f"{var_name}.{access_path}"
            
            # ポインタメンバーの場合
            if member.is_pointer:
                lines.append(f"    // TODO: ポインタメンバー {full_path} を確認してください")
                continue
            
            # 配列メンバーの場合
            if member.is_array:
                lines.append(f"    // TODO: 配列メンバー {full_path} を確認してください")
                continue
            
            # ビットフィールドの場合
            if member.bit_width:
                lines.append(f"    TEST_ASSERT_EQUAL(0, {full_path});  // ビットフィールド")
            else:
                # 通常のメンバー
                lines.append(f"    TEST_ASSERT_EQUAL(0, {full_path});")
        
        return lines


if __name__ == "__main__":
    # TestFunctionGeneratorのテスト
    print("=" * 70)
    print("TestFunctionGenerator v4.1.3 のテスト（パラメータ対応）")
    print("=" * 70)
    print()
    
    from src.data_structures import TestCase, ParsedData, Condition, ConditionType, FunctionInfo
    
    # テスト用データ（パラメータなし関数）
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="test_func",
        external_functions=['f4', 'mx27'],
        global_variables=['v9', 'mx63', 'v10']
    )
    
    # 条件を追加
    parsed_data.conditions.append(
        Condition(
            line=10,
            type=ConditionType.SIMPLE_IF,
            expression="(v10 > 30)"
        )
    )
    
    parsed_data.conditions.append(
        Condition(
            line=15,
            type=ConditionType.OR_CONDITION,
            expression="((mx63 == m47) || (mx63 == m46))",
            operator='or',
            left="(mx63 == m47)",
            right="(mx63 == m46)",
            conditions=["(mx63 == m47)", "(mx63 == m46)"]
        )
    )
    
    # テストケース
    test_case1 = TestCase(
        no=1,
        truth="T",
        condition="if (v10 > 30)",
        expected="条件が真の処理を実行"
    )
    
    test_case2 = TestCase(
        no=3,
        truth="TF",
        condition="if ((mx63 == m47) || (mx63 == m46))",
        expected="左辺が真、右辺が偽"
    )
    
    # テスト関数を生成
    generator = TestFunctionGenerator()
    
    print("テスト1: 単純条件のテスト関数（パラメータなし）")
    print("=" * 70)
    print(generator.generate_test_function(test_case1, parsed_data))
    print()
    print()
    
    print("テスト2: OR条件のテスト関数（パラメータなし）")
    print("=" * 70)
    print(generator.generate_test_function(test_case2, parsed_data))
    print()
    print()
    
    # v4.1.3: パラメータあり関数のテスト
    print("=" * 70)
    print("v4.1.3: パラメータあり関数のテスト")
    print("=" * 70)
    print()
    
    # パラメータあり関数のテストデータ
    parsed_data_with_params = ParsedData(
        file_name="test.c",
        function_name="Utf1",
        external_functions=['Utf7', 'Utf8'],
        global_variables=['Utx130', 'Utx116']
    )
    
    # 関数情報を設定（パラメータあり）
    parsed_data_with_params.function_info = FunctionInfo(
        name="Utf1",
        return_type="void",  # 戻り値なし
        parameters=[
            {'type': 'uint8_t', 'name': 'Utv1'}
        ]
    )
    
    # 条件を追加
    parsed_data_with_params.conditions.append(
        Condition(
            line=110,
            type=ConditionType.SIMPLE_IF,
            expression="(Utx130.Utm1.Utm4 != 0)"
        )
    )
    
    test_case_with_params = TestCase(
        no=1,
        truth="T",
        condition="if (Utx130.Utm1.Utm4 != 0)",
        expected="条件が真の処理を実行"
    )
    
    print("テスト3: パラメータあり＆戻り値なし関数のテスト")
    print("=" * 70)
    result = generator.generate_test_function(test_case_with_params, parsed_data_with_params)
    print(result)
    
    # Utf1(Utv1) が生成されているか確認
    if "Utf1(Utv1)" in result:
        print()
        print("✅ パラメータが正しく渡されています: Utf1(Utv1)")
    elif "Utf1()" in result:
        print()
        print("❌ パラメータが渡されていません: Utf1()")
    print()
    
    # 戻り値ありの場合のテスト
    parsed_data_with_return = ParsedData(
        file_name="test.c",
        function_name="Utf2",
        external_functions=['Utf7'],
        global_variables=['Utx130']
    )
    
    parsed_data_with_return.function_info = FunctionInfo(
        name="Utf2",
        return_type="uint16_t",  # 戻り値あり
        parameters=[
            {'type': 'uint8_t', 'name': 'param1'},
            {'type': 'int', 'name': 'param2'}
        ]
    )
    
    parsed_data_with_return.conditions.append(
        Condition(
            line=110,
            type=ConditionType.SIMPLE_IF,
            expression="(Utx130 > 0)"
        )
    )
    
    test_case_with_return = TestCase(
        no=1,
        truth="T",
        condition="if (Utx130 > 0)",
        expected="条件が真"
    )
    
    print("テスト4: パラメータあり＆戻り値あり関数のテスト")
    print("=" * 70)
    result2 = generator.generate_test_function(test_case_with_return, parsed_data_with_return)
    print(result2)
    
    # result = Utf2(param1, param2) が生成されているか確認
    if "Utf2(param1, param2)" in result2:
        print()
        print("✅ パラメータが正しく渡されています: result = Utf2(param1, param2)")
    print()
    
    print("✓ TestFunctionGenerator v4.1.3 が正常に動作しました")

