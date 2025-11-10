"""
戻り値パターン分析器

関数の戻り値パターンを分析し、期待値推論を支援する。
"""

import re
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class ReturnType(Enum):
    """戻り値の型分類"""
    CONSTANT = "CONSTANT"          # 定数値
    VARIABLE = "VARIABLE"          # 変数参照
    EXPRESSION = "EXPRESSION"      # 算術式
    FUNCTION_CALL = "FUNCTION_CALL"  # 関数呼び出し
    POINTER = "POINTER"            # ポインタ
    STRUCT_MEMBER = "STRUCT_MEMBER"  # 構造体メンバ
    ARRAY_ELEMENT = "ARRAY_ELEMENT"  # 配列要素
    CONDITIONAL = "CONDITIONAL"    # 三項演算子
    UNKNOWN = "UNKNOWN"            # 不明


@dataclass
class ReturnPattern:
    """戻り値のパターン情報"""
    type: ReturnType               # 戻り値の型
    expression: str                # 元の式
    value: Optional[Any] = None    # 評価可能な場合の値
    variables: Set[str] = field(default_factory=set)  # 使用される変数
    functions: Set[str] = field(default_factory=set)  # 呼び出される関数
    operators: Set[str] = field(default_factory=set)  # 使用される演算子
    complexity: int = 0            # 複雑度スコア
    context: str = ""              # 条件コンテキスト


@dataclass
class FunctionReturnAnalysis:
    """関数全体の戻り値分析結果"""
    patterns: List[ReturnPattern]   # すべての戻り値パターン
    default_value: Optional[Any]    # デフォルト値
    common_values: List[Any]        # よく使われる値
    value_distribution: Dict[Any, int]  # 値の分布
    type_distribution: Dict[ReturnType, int]  # 型の分布
    has_error_handling: bool        # エラーハンドリングがあるか
    estimated_return_type: str      # 推定される戻り値型


class ReturnPatternAnalyzer:
    """戻り値パターン分析器"""
    
    def __init__(self):
        self.error_values = {-1, 0, 'NULL', 'nullptr', 'false', 'FALSE'}
        self.success_values = {0, 1, 'true', 'TRUE'}
        
    def analyze(self, function_body: str) -> FunctionReturnAnalysis:
        """
        関数本体から戻り値パターンを分析
        
        Args:
            function_body: 関数本体のコード
            
        Returns:
            戻り値の分析結果
        """
        patterns = self._extract_return_patterns(function_body)
        
        # 値の分布を計算
        value_distribution = self._calculate_value_distribution(patterns)
        type_distribution = self._calculate_type_distribution(patterns)
        
        # デフォルト値を推定
        default_value = self._find_default_value(patterns, value_distribution)
        
        # よく使われる値を抽出
        common_values = self._find_common_values(value_distribution)
        
        # エラーハンドリングの検出
        has_error_handling = self._detect_error_handling(patterns)
        
        # 戻り値型の推定
        estimated_type = self._estimate_return_type(patterns, value_distribution)
        
        return FunctionReturnAnalysis(
            patterns=patterns,
            default_value=default_value,
            common_values=common_values,
            value_distribution=value_distribution,
            type_distribution=type_distribution,
            has_error_handling=has_error_handling,
            estimated_return_type=estimated_type
        )
    
    def _extract_return_patterns(self, function_body: str) -> List[ReturnPattern]:
        """関数本体からreturnパターンを抽出"""
        patterns = []
        lines = function_body.split('\n')
        
        # コンテキストトラッキング
        context_stack = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # コンテキストの更新
            if self._is_control_statement(stripped):
                context_stack.append(self._extract_condition(stripped))
            elif stripped == '}' and context_stack:
                context_stack.pop()
            
            # return文の検出（セミコロンはオプショナル）
            return_match = re.match(r'\s*return\s+([^;]+);?', line)
            if return_match:
                expression = return_match.group(1).strip()
                if expression.endswith(';'):
                    expression = expression[:-1]
                pattern = self._analyze_return_expression(
                    expression,
                    ' -> '.join(context_stack) if context_stack else 'main'
                )
                patterns.append(pattern)
        
        return patterns
    
    def _is_control_statement(self, line: str) -> bool:
        """制御文かどうかを判定"""
        control_keywords = ['if', 'else if', 'else', 'switch', 'case', 'for', 'while', 'do']
        return any(line.startswith(kw) for kw in control_keywords)
    
    def _extract_condition(self, line: str) -> str:
        """制御文から条件を抽出"""
        # if文
        if_match = re.match(r'(else\s+)?if\s*\((.*?)\)', line)
        if if_match:
            return f"if({if_match.group(2)})"
        
        # switch文
        switch_match = re.match(r'switch\s*\((.*?)\)', line)
        if switch_match:
            return f"switch({switch_match.group(1)})"
        
        # case文
        case_match = re.match(r'case\s+(.+?):', line)
        if case_match:
            return f"case {case_match.group(1)}"
        
        # else
        if line.startswith('else'):
            return "else"
        
        # ループ
        for_match = re.match(r'for\s*\((.*?)\)', line)
        if for_match:
            return "for"
        
        while_match = re.match(r'while\s*\((.*?)\)', line)
        if while_match:
            return f"while({while_match.group(1)})"
        
        return line.split()[0] if line else ""
    
    def _analyze_return_expression(self, expression: str, context: str) -> ReturnPattern:
        """return式を詳細に分析"""
        pattern = ReturnPattern(
            type=ReturnType.UNKNOWN,
            expression=expression,
            context=context
        )
        
        # 定数の判定
        is_constant, value = self._is_constant(expression)
        if is_constant:
            pattern.type = ReturnType.CONSTANT
            pattern.value = value
            pattern.complexity = 0
            return pattern
        
        # 関数呼び出しの検出
        function_calls = re.findall(r'(\w+)\s*\(', expression)
        if function_calls:
            pattern.type = ReturnType.FUNCTION_CALL
            pattern.functions = set(function_calls)
            pattern.complexity = 10 * len(function_calls)
        
        # ポインタ操作の検出
        if '->' in expression or ('*' in expression and not self._is_multiplication(expression)):
            pattern.type = ReturnType.POINTER
            pattern.complexity += 5
        
        # 構造体メンバアクセス
        if '.' in expression and not self._is_float(expression):
            pattern.type = ReturnType.STRUCT_MEMBER
            pattern.complexity += 3
        
        # 配列アクセス
        if '[' in expression and ']' in expression:
            pattern.type = ReturnType.ARRAY_ELEMENT
            pattern.complexity += 4
        
        # 三項演算子
        if '?' in expression and ':' in expression:
            pattern.type = ReturnType.CONDITIONAL
            pattern.complexity += 6
        
        # 変数の抽出
        variables = self._extract_variables(expression)
        pattern.variables = variables
        
        # 演算子の抽出
        operators = self._extract_operators(expression)
        pattern.operators = operators
        pattern.complexity += len(operators) * 2
        
        # 型の最終決定
        if pattern.type == ReturnType.UNKNOWN:
            if operators:
                pattern.type = ReturnType.EXPRESSION
            elif variables:
                pattern.type = ReturnType.VARIABLE
        
        return pattern
    
    def _is_constant(self, expression: str) -> Tuple[bool, Optional[Any]]:
        """式が定数かどうかを判定"""
        expression = expression.strip()
        
        # 整数リテラル
        if re.match(r'^-?\d+$', expression):
            return True, int(expression)
        
        # 16進数
        if re.match(r'^0[xX][0-9a-fA-F]+$', expression):
            return True, int(expression, 16)
        
        # 浮動小数点
        if re.match(r'^-?\d+\.\d+$', expression):
            return True, float(expression)
        
        # 文字リテラル
        if re.match(r"^'.'$", expression):
            return True, ord(expression[1])
        
        # よく使われる定数
        constants = {
            'NULL': 0, 'nullptr': 0,
            'true': 1, 'TRUE': 1,
            'false': 0, 'FALSE': 0,
        }
        if expression in constants:
            return True, constants[expression]
        
        return False, None
    
    def _is_multiplication(self, expression: str) -> bool:
        """*が乗算演算子かどうかを判定"""
        # 簡易的な判定: 数字や変数の後の*は乗算
        return bool(re.search(r'[\w\)]\s*\*\s*[\w\(]', expression))
    
    def _is_float(self, expression: str) -> bool:
        """.が浮動小数点の一部かどうかを判定"""
        return bool(re.search(r'\d+\.\d+', expression))
    
    def _extract_variables(self, expression: str) -> Set[str]:
        """式から変数名を抽出"""
        # 関数呼び出しを除去
        expr = re.sub(r'\w+\s*\([^)]*\)', '', expression)
        
        # 定数を除去
        expr = re.sub(r'\b\d+\b', '', expr)
        expr = re.sub(r'\b0[xX][0-9a-fA-F]+\b', '', expr)
        
        # 演算子と括弧を空白に置換
        expr = re.sub(r'[+\-*/&|^~!<>=()[\]{},;]', ' ', expr)
        
        # 変数名を抽出
        variables = set()
        for word in expr.split():
            if word and word[0].isalpha():
                # キーワードを除外
                if word not in ['return', 'if', 'else', 'NULL', 'nullptr', 'true', 'false', 'TRUE', 'FALSE']:
                    variables.add(word)
        
        return variables
    
    def _extract_operators(self, expression: str) -> Set[str]:
        """式から演算子を抽出"""
        operators = set()
        
        # 算術演算子
        for op in ['+', '-', '*', '/', '%']:
            if op in expression:
                operators.add(op)
        
        # ビット演算子
        for op in ['&', '|', '^', '~', '<<', '>>']:
            if op in expression:
                operators.add(op)
        
        # 比較演算子
        for op in ['==', '!=', '<=', '>=', '<', '>']:
            if op in expression:
                operators.add(op)
        
        # 論理演算子
        for op in ['&&', '||', '!']:
            if op in expression:
                operators.add(op)
        
        return operators
    
    def _calculate_value_distribution(self, patterns: List[ReturnPattern]) -> Dict[Any, int]:
        """値の分布を計算"""
        distribution = defaultdict(int)
        
        for pattern in patterns:
            if pattern.value is not None:
                distribution[pattern.value] += 1
        
        return dict(distribution)
    
    def _calculate_type_distribution(self, patterns: List[ReturnPattern]) -> Dict[ReturnType, int]:
        """型の分布を計算"""
        distribution = defaultdict(int)
        
        for pattern in patterns:
            distribution[pattern.type] += 1
        
        return dict(distribution)
    
    def _find_default_value(
        self,
        patterns: List[ReturnPattern],
        value_distribution: Dict[Any, int]
    ) -> Optional[Any]:
        """デフォルト値を推定"""
        
        # 最後のreturn文（多くの場合デフォルト）
        for pattern in reversed(patterns):
            if pattern.context == 'main' or 'else' in pattern.context:
                if pattern.value is not None:
                    return pattern.value
        
        # 最頻値
        if value_distribution:
            return max(value_distribution, key=value_distribution.get)
        
        # エラー値の検出
        for pattern in patterns:
            if pattern.value in self.error_values:
                return pattern.value
        
        return 0  # デフォルトは0
    
    def _find_common_values(self, value_distribution: Dict[Any, int]) -> List[Any]:
        """よく使われる値を抽出"""
        if not value_distribution:
            return []
        
        # 頻度順にソート
        sorted_values = sorted(
            value_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 上位3つまたは2回以上出現する値
        common = []
        for value, count in sorted_values[:3]:
            if count >= 2 or len(sorted_values) <= 3:
                common.append(value)
        
        return common
    
    def _detect_error_handling(self, patterns: List[ReturnPattern]) -> bool:
        """エラーハンドリングの有無を検出"""
        
        # エラー値のreturnがあるか
        for pattern in patterns:
            if pattern.value in self.error_values:
                # エラー条件のコンテキストがあるか
                if any(word in pattern.context.lower() for word in ['error', 'fail', 'null', '!', '==']):
                    return True
        
        # 複数の異なる値を返す場合
        values = {p.value for p in patterns if p.value is not None}
        if len(values) > 1 and any(v in self.error_values for v in values):
            return True
        
        return False
    
    def _estimate_return_type(
        self,
        patterns: List[ReturnPattern],
        value_distribution: Dict[Any, int]
    ) -> str:
        """戻り値の型を推定"""
        
        # すべての値が整数
        all_values = set(value_distribution.keys())
        if all_values and all(isinstance(v, int) for v in all_values):
            # bool型の判定
            if all_values.issubset({0, 1}):
                return "bool"
            # エラーコードの判定
            if any(v < 0 for v in all_values):
                return "int (error code)"
            return "int"
        
        # ポインタ型
        if any(p.type == ReturnType.POINTER for p in patterns):
            return "pointer"
        
        # 浮動小数点
        if any(isinstance(v, float) for v in all_values):
            return "float/double"
        
        # 構造体
        if any(p.type == ReturnType.STRUCT_MEMBER for p in patterns):
            return "struct/union"
        
        return "unknown"
    
    def get_confidence_for_pattern(self, pattern: ReturnPattern) -> float:
        """パターンの推論信頼度を計算"""
        
        # 定数は最高信頼度
        if pattern.type == ReturnType.CONSTANT:
            return 0.95
        
        # 単純な変数参照
        if pattern.type == ReturnType.VARIABLE and len(pattern.variables) == 1:
            return 0.75
        
        # 単純な式
        if pattern.type == ReturnType.EXPRESSION and pattern.complexity < 5:
            return 0.65
        
        # 構造体メンバ
        if pattern.type == ReturnType.STRUCT_MEMBER:
            return 0.60
        
        # 配列要素
        if pattern.type == ReturnType.ARRAY_ELEMENT:
            return 0.55
        
        # 関数呼び出し
        if pattern.type == ReturnType.FUNCTION_CALL:
            return 0.30
        
        # 三項演算子
        if pattern.type == ReturnType.CONDITIONAL:
            return 0.40
        
        # 複雑な式
        if pattern.complexity > 10:
            return 0.20
        
        return 0.25
