"""
期待値推論エンジン (v2.3)

条件分岐やコードパターンから期待値を自動推論する
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import pycparser
from pycparser import c_ast


@dataclass
class InferredExpectation:
    """推論された期待値"""
    variable: str
    value: Any
    assertion_type: str  # TEST_ASSERT_EQUAL, TEST_ASSERT_TRUE, etc.
    confidence: float  # 0.0 ~ 1.0
    reason: str  # 推論理由


class ExpectationInferenceEngine:
    """期待値推論エンジン"""
    
    def __init__(self):
        self.inferred_expectations = []
        self.variable_types = {}  # 変数の型情報
        self.global_variables = set()  # グローバル変数
        self.function_returns = {}  # 関数の戻り値情報
    
    def analyze_function(self, function_ast: c_ast.FuncDef, parsed_data: dict) -> List[InferredExpectation]:
        """関数全体を解析して期待値を推論"""
        self.global_variables = set(parsed_data.get('global_variables', []))
        self._extract_variable_types(function_ast)
        self._analyze_function_body(function_ast)
        return self.inferred_expectations
    
    def infer_from_condition(self, condition: str, truth_value: bool, 
                           line_number: int = 0) -> List[InferredExpectation]:
        """条件式から期待値を推論"""
        expectations = []
        
        # パターン1: 単純な等価比較 (x == value)
        eq_match = re.match(r'(\w+)\s*==\s*(.+)', condition.strip())
        if eq_match:
            var, value = eq_match.groups()
            if truth_value:
                # 条件が真の場合、変数は指定値と等しい
                expectations.append(InferredExpectation(
                    variable=var,
                    value=self._parse_value(value),
                    assertion_type='TEST_ASSERT_EQUAL',
                    confidence=0.9,
                    reason=f"条件 '{condition}' が真"
                ))
            else:
                # 条件が偽の場合、変数は指定値と異なる
                expectations.append(InferredExpectation(
                    variable=var,
                    value=self._parse_value(value),
                    assertion_type='TEST_ASSERT_NOT_EQUAL',
                    confidence=0.8,
                    reason=f"条件 '{condition}' が偽"
                ))
        
        # パターン2: 不等価比較 (x != value)
        neq_match = re.match(r'(\w+)\s*!=\s*(.+)', condition.strip())
        if neq_match:
            var, value = neq_match.groups()
            if truth_value:
                expectations.append(InferredExpectation(
                    variable=var,
                    value=self._parse_value(value),
                    assertion_type='TEST_ASSERT_NOT_EQUAL',
                    confidence=0.9,
                    reason=f"条件 '{condition}' が真"
                ))
            else:
                expectations.append(InferredExpectation(
                    variable=var,
                    value=self._parse_value(value),
                    assertion_type='TEST_ASSERT_EQUAL',
                    confidence=0.8,
                    reason=f"条件 '{condition}' が偽"
                ))
        
        # パターン3: 大小比較 (x > value, x < value, etc.)
        comp_patterns = [
            (r'(\w+)\s*>\s*(.+)', 'greater', lambda v: int(v) + 1),
            (r'(\w+)\s*>=\s*(.+)', 'greater_equal', lambda v: int(v)),
            (r'(\w+)\s*<\s*(.+)', 'less', lambda v: int(v) - 1),
            (r'(\w+)\s*<=\s*(.+)', 'less_equal', lambda v: int(v))
        ]
        
        for pattern, comp_type, value_func in comp_patterns:
            match = re.match(pattern, condition.strip())
            if match:
                var, value = match.groups()
                try:
                    if truth_value:
                        # 条件を満たす最小/最大値を設定
                        inferred_value = value_func(value)
                        expectations.append(InferredExpectation(
                            variable=var,
                            value=inferred_value,
                            assertion_type='TEST_ASSERT_EQUAL',
                            confidence=0.7,
                            reason=f"条件 '{condition}' を満たす境界値"
                        ))
                except (ValueError, TypeError):
                    # 数値でない場合はスキップ
                    pass
        
        # パターン4: NULL/ポインタチェック
        null_patterns = [
            (r'(\w+)\s*==\s*NULL', True, 'TEST_ASSERT_NULL'),
            (r'(\w+)\s*!=\s*NULL', True, 'TEST_ASSERT_NOT_NULL'),
            (r'!\s*(\w+)', True, 'TEST_ASSERT_NULL'),
            (r'(\w+)', True, 'TEST_ASSERT_NOT_NULL')  # if (ptr) の形
        ]
        
        for pattern, expected_truth, assertion in null_patterns:
            match = re.match(pattern, condition.strip())
            if match and truth_value == expected_truth:
                var = match.group(1)
                if self._is_likely_pointer(var):
                    expectations.append(InferredExpectation(
                        variable=var,
                        value=None,
                        assertion_type=assertion,
                        confidence=0.8,
                        reason=f"ポインタチェック '{condition}'"
                    ))
        
        # パターン5: ビット演算 (x & MASK)
        bit_match = re.match(r'\((\w+)\s*&\s*([^)]+)\)\s*!=\s*0', condition.strip())
        if bit_match:
            var, mask = bit_match.groups()
            if truth_value:
                expectations.append(InferredExpectation(
                    variable=f"({var} & {mask})",
                    value="!= 0",
                    assertion_type='TEST_ASSERT_TRUE',
                    confidence=0.7,
                    reason=f"ビットマスクチェック '{condition}' が真"
                ))
        
        return expectations
    
    def infer_from_assignment(self, ast_node: c_ast.Assignment) -> Optional[InferredExpectation]:
        """代入文から期待値を推論"""
        if isinstance(ast_node.lvalue, c_ast.ID):
            var_name = ast_node.lvalue.name
            
            # グローバル変数への代入を検出
            if var_name in self.global_variables:
                value = self._extract_value_from_ast(ast_node.rvalue)
                if value is not None:
                    return InferredExpectation(
                        variable=var_name,
                        value=value,
                        assertion_type='TEST_ASSERT_EQUAL',
                        confidence=0.85,
                        reason=f"グローバル変数 '{var_name}' への代入"
                    )
        
        return None
    
    def infer_from_return(self, return_node: c_ast.Return, 
                         function_name: str = None) -> Optional[InferredExpectation]:
        """return文から期待値を推論"""
        if return_node.expr:
            value = self._extract_value_from_ast(return_node.expr)
            if value is not None:
                return InferredExpectation(
                    variable='_return_value',
                    value=value,
                    assertion_type='TEST_ASSERT_EQUAL',
                    confidence=0.9,
                    reason=f"関数の戻り値"
                )
        return None
    
    def infer_from_switch(self, switch_node: c_ast.Switch, 
                         case_value: Any) -> List[InferredExpectation]:
        """switch文から期待値を推論"""
        expectations = []
        
        if isinstance(switch_node.cond, c_ast.ID):
            var_name = switch_node.cond.name
            
            if case_value != 'default':
                expectations.append(InferredExpectation(
                    variable=var_name,
                    value=case_value,
                    assertion_type='TEST_ASSERT_EQUAL',
                    confidence=0.95,
                    reason=f"switch文のcase {case_value}"
                ))
            else:
                # defaultの場合は、他のcase値以外の値を設定
                other_cases = self._extract_case_values(switch_node)
                # 使われていない値を見つける
                unused_value = self._find_unused_value(other_cases)
                expectations.append(InferredExpectation(
                    variable=var_name,
                    value=unused_value,
                    assertion_type='TEST_ASSERT_EQUAL',
                    confidence=0.7,
                    reason=f"switch文のdefault (case値以外)"
                ))
        
        return expectations
    
    def generate_smart_assertion(self, expectation: InferredExpectation, 
                                 context: dict = None) -> str:
        """スマートなアサーションを生成"""
        if expectation.confidence < 0.5:
            # 信頼度が低い場合はTODOコメントを生成
            return self._generate_todo_with_hint(expectation, context)
        
        # アサーションタイプに応じた生成
        if expectation.assertion_type == 'TEST_ASSERT_EQUAL':
            if expectation.variable == '_return_value':
                return f"TEST_ASSERT_EQUAL({expectation.value}, result);"
            else:
                return f"TEST_ASSERT_EQUAL({expectation.value}, {expectation.variable});"
        
        elif expectation.assertion_type == 'TEST_ASSERT_NOT_EQUAL':
            return f"TEST_ASSERT_NOT_EQUAL({expectation.value}, {expectation.variable});"
        
        elif expectation.assertion_type == 'TEST_ASSERT_NULL':
            return f"TEST_ASSERT_NULL({expectation.variable});"
        
        elif expectation.assertion_type == 'TEST_ASSERT_NOT_NULL':
            return f"TEST_ASSERT_NOT_NULL({expectation.variable});"
        
        elif expectation.assertion_type == 'TEST_ASSERT_TRUE':
            return f"TEST_ASSERT_TRUE({expectation.variable});"
        
        elif expectation.assertion_type == 'TEST_ASSERT_FALSE':
            return f"TEST_ASSERT_FALSE({expectation.variable});"
        
        else:
            return self._generate_todo_with_hint(expectation, context)
    
    def _parse_value(self, value_str: str) -> Any:
        """文字列から値を解析"""
        value_str = value_str.strip()
        
        # 数値
        try:
            if '0x' in value_str or '0X' in value_str:
                return int(value_str, 16)
            return int(value_str)
        except ValueError:
            pass
        
        # 浮動小数点
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # 文字列リテラル
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str
        
        # その他（変数名、マクロ等）
        return value_str
    
    def _is_likely_pointer(self, var_name: str) -> bool:
        """変数名がポインタの可能性が高いか判定"""
        pointer_patterns = ['ptr', 'p_', 'lp', 'h_', 'handle', 'buf', 'buffer']
        var_lower = var_name.lower()
        return any(pattern in var_lower for pattern in pointer_patterns)
    
    def _extract_variable_types(self, function_ast: c_ast.FuncDef):
        """関数から変数の型情報を抽出"""
        # TODO: 実装
        pass
    
    def _analyze_function_body(self, function_ast: c_ast.FuncDef):
        """関数本体を解析"""
        # TODO: 実装
        pass
    
    def _extract_value_from_ast(self, ast_node) -> Any:
        """ASTノードから値を抽出"""
        if isinstance(ast_node, c_ast.Constant):
            return self._parse_value(ast_node.value)
        elif isinstance(ast_node, c_ast.ID):
            return ast_node.name
        elif isinstance(ast_node, c_ast.UnaryOp):
            if ast_node.op == '-':
                sub_value = self._extract_value_from_ast(ast_node.expr)
                if isinstance(sub_value, (int, float)):
                    return -sub_value
        return None
    
    def _extract_case_values(self, switch_node: c_ast.Switch) -> List[Any]:
        """switch文からcase値を抽出"""
        case_values = []
        # TODO: switch文のASTを解析してcase値を抽出
        return case_values
    
    def _find_unused_value(self, used_values: List[Any]) -> Any:
        """使用されていない値を見つける"""
        # 整数値の場合
        if all(isinstance(v, int) for v in used_values):
            max_val = max(used_values) if used_values else 0
            return max_val + 999  # 十分大きい値
        
        # その他の場合
        return 999
    
    def _generate_todo_with_hint(self, expectation: InferredExpectation, 
                                 context: dict = None) -> str:
        """より具体的なヒント付きTODOコメントを生成"""
        hint = f"// TODO: {expectation.variable} の期待値を設定 "
        
        if expectation.reason:
            hint += f"({expectation.reason})"
        
        if expectation.assertion_type == 'TEST_ASSERT_EQUAL':
            hint += f"\n    // 推奨: TEST_ASSERT_EQUAL(expected, {expectation.variable});"
        elif expectation.assertion_type == 'TEST_ASSERT_NULL':
            hint += f"\n    // 推奨: TEST_ASSERT_NULL({expectation.variable});"
        elif expectation.assertion_type == 'TEST_ASSERT_NOT_NULL':
            hint += f"\n    // 推奨: TEST_ASSERT_NOT_NULL({expectation.variable});"
        
        return hint


class SmartTODOGenerator:
    """スマートなTODOコメント生成器"""
    
    @staticmethod
    def generate_from_condition(condition: str, truth_value: bool) -> str:
        """条件に基づいた具体的なTODOを生成"""
        todo_lines = []
        
        # 基本的なTODOメッセージ
        todo_lines.append("// TODO: 以下の期待値を設定してください")
        
        # 条件の説明
        truth_str = "真" if truth_value else "偽"
        todo_lines.append(f"//   条件 '{condition}' が{truth_str}の場合")
        
        # 具体的なヒント
        if '==' in condition:
            var = condition.split('==')[0].strip()
            value = condition.split('==')[1].strip()
            if truth_value:
                todo_lines.append(f"//   推奨: TEST_ASSERT_EQUAL({value}, {var});")
            else:
                todo_lines.append(f"//   推奨: TEST_ASSERT_NOT_EQUAL({value}, {var});")
        
        elif '>' in condition or '<' in condition:
            todo_lines.append("//   推奨: 境界値をテストしてください")
        
        elif 'NULL' in condition:
            todo_lines.append("//   推奨: ポインタの有効性をチェック")
        
        else:
            todo_lines.append("//   推奨: 適切なアサーションを選択")
        
        return '\n'.join(todo_lines)
