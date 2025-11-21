"""
TestFunctionGeneratorモジュール

Unityテスト関数を生成
"""

import sys
import os
import re
from typing import List, Dict, Optional

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger, sanitize_identifier
from src.data_structures import TestCase, ParsedData, Condition, ConditionType
from src.test_generator.boundary_value_calculator import BoundaryValueCalculator
from src.test_generator.comment_generator import CommentGenerator


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
        
        # 戻り値がある場合は result 変数に代入
        if parsed_data.function_info and parsed_data.function_info.return_type != 'void':
            # パラメータを構築
            params = []
            if parsed_data.function_info.parameters:
                for param in parsed_data.function_info.parameters:
                    params.append(param.get('name', ''))
            param_str = ', '.join(params) if params else ''
            lines.append(f"    result = {parsed_data.function_name}({param_str});")
        else:
            lines.append(f"    {parsed_data.function_name}();")
        
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
        
        # 条件タイプに応じて初期化コードを生成
        if matching_condition.type == ConditionType.SIMPLE_IF:
            init = self._generate_simple_condition_init(matching_condition, test_case.truth, parsed_data)
            if init:
                # セミコロンの前のコメントを考慮してチェック
                # "変数 = 値;  // コメント" の形式を想定
                code_part = init.split('//')[0].rstrip()
                if not code_part.endswith(';'):
                    lines.append(f"    {init};")
                else:
                    lines.append(f"    {init}")
        
        elif matching_condition.type == ConditionType.OR_CONDITION:
            init_list = self._generate_or_condition_init(matching_condition, test_case.truth, parsed_data)
            for init in init_list:
                # セミコロンの前のコメントを考慮してチェック
                code_part = init.split('//')[0].rstrip()
                if not code_part.endswith(';'):
                    lines.append(f"    {init};")
                else:
                    lines.append(f"    {init}")
        
        elif matching_condition.type == ConditionType.AND_CONDITION:
            init_list = self._generate_and_condition_init(matching_condition, test_case.truth, parsed_data)
            for init in init_list:
                # セミコロンの前のコメントを考慮してチェック
                code_part = init.split('//')[0].rstrip()
                if not code_part.endswith(';'):
                    lines.append(f"    {init};")
                else:
                    lines.append(f"    {init}")
        
        elif matching_condition.type == ConditionType.SWITCH:
            init = self._generate_switch_init(matching_condition, test_case, parsed_data)
            if init:
                # セミコロンの前のコメントを考慮してチェック
                code_part = init.split('//')[0].rstrip()
                if not code_part.endswith(';'):
                    lines.append(f"    {init};")
                else:
                    lines.append(f"    {init}")
        
        lines.append("")
        return '\n'.join(lines)
    
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
        # 境界値を計算
        test_value = self.boundary_calc.generate_test_value(condition.expression, truth)
        
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
                return f"// TODO: mock_{func_name}_return_value を設定してください"
            
            # 関数かenum定数でないことを確認
            if self._is_function_or_enum(var, parsed_data):
                return f"// TODO: {var}は関数またはenum定数のため初期化できません"
            
            # ビットフィールドかチェック
            if var in parsed_data.bitfields:
                bitfield = parsed_data.bitfields[var]
                max_val = bitfield.get_max_value()
                if truth == 'T':
                    return f"{var} = 1;  // TODO: 真になる値を設定 (最大値: 0x{max_val:X})"
                else:
                    return f"{var} = 0;  // TODO: 偽になる値を設定 (最大値: 0x{max_val:X})"
            
            if truth == 'T':
                return f"{var} = 1;  // TODO: 真になる値を設定"
            else:
                return f"{var} = 0;  // TODO: 偽になる値を設定"
        
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
        
        # 各条件に対して値を設定
        for i, cond in enumerate(conditions):
            if i < len(truth):
                truth_val = truth[i]
                test_value = self.boundary_calc.generate_test_value(cond, truth_val)
                
                if test_value:
                    # 関数呼び出しが含まれる場合はTODOコメントとしてそのまま追加
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
                        var = variables[0]
                        
                        # 関数呼び出しかチェック
                        if self._is_function_call_pattern(var):
                            func_name = var.replace('()', '').strip()
                            init_list.append(f"// TODO: mock_{func_name}_return_value を設定してください")
                            continue
                        
                        # 関数またはenum定数でないことを確認
                        if self._is_function_or_enum(var, parsed_data):
                            init_list.append(f"// TODO: {var}は関数またはenum定数のため初期化できません")
                        else:
                            val = '1' if truth_val == 'T' else '0'
                            init_list.append(f"{var} = {val};  // TODO: 適切な値を設定")
        
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
        lines.append("    // TODO: 期待値を設定してください")
        
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
        
        Args:
            init_code: 初期化コード
            parsed_data: 解析済みデータ
        
        Returns:
            修正後の初期化コード
        """
        # "変数 = 値" の形式から変数と値を抽出
        match = re.match(r'(\w+)\s*=\s*(.+)', init_code)
        if not match:
            return init_code
        
        var_name = match.group(1)
        value_part = match.group(2).strip()
        
        # 値の部分に関数が含まれている場合
        if self._is_function(value_part, parsed_data):
            # 関数の場合はモックの戻り値を使用
            return f"{var_name} = mock_{value_part}_return_value;  // 修正: {value_part}は関数"
        
        # 値の部分にenum定数が含まれている場合はそのまま（正しい使い方）
        
        # 変数自体が関数の場合（エラー）
        if self._is_function(var_name, parsed_data):
            return f"// ERROR: {var_name}は関数のため変数として初期化できません。モック設定を使用してください。"
        
        # 変数自体がenum定数の場合（エラー）
        if self._is_enum_constant(var_name, parsed_data):
            # enum定数は代入できないので、適切な変数を見つける
            # グローバル変数の中から適切なものを探す
            for gvar in parsed_data.global_variables:
                if not self._is_function_or_enum(gvar, parsed_data):
                    return f"{gvar} = {value_part};  // 修正: {var_name}はenum定数のため{gvar}に代入"
            return f"// ERROR: {var_name}はenum定数のため変数として初期化できません"
        
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
    print("TestFunctionGenerator のテスト")
    print("=" * 70)
    print()
    
    from src.data_structures import TestCase, ParsedData, Condition, ConditionType
    
    # テスト用データ
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
    
    print("テスト1: 単純条件のテスト関数")
    print("=" * 70)
    print(generator.generate_test_function(test_case1, parsed_data))
    print()
    print()
    
    print("テスト2: OR条件のテスト関数")
    print("=" * 70)
    print(generator.generate_test_function(test_case2, parsed_data))
    print()
    
    print("✓ TestFunctionGeneratorが正常に動作しました")

