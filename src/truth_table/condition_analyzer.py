"""
ConditionAnalyzerモジュール

条件分岐を分析し、MC/DCテストに必要な情報を抽出
"""

import sys
import os
import re
from typing import Dict, List, Optional, Tuple

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import Condition, ConditionType


class ConditionAnalyzer:
    """条件分岐アナライザー"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def analyze_condition(self, condition: Condition) -> Dict:
        """
        条件分岐を分析
        
        Args:
            condition: 条件分岐
        
        Returns:
            分析結果の辞書
        """
        if condition.type == ConditionType.SIMPLE_IF:
            return self._analyze_simple_condition(condition)
        
        elif condition.type == ConditionType.OR_CONDITION:
            return self._analyze_or_condition(condition)
        
        elif condition.type == ConditionType.AND_CONDITION:
            return self._analyze_and_condition(condition)
        
        elif condition.type == ConditionType.SWITCH:
            return self._analyze_switch(condition)
        
        else:
            self.logger.warning(f"未知の条件タイプ: {condition.type}")
            return {'type': 'unknown', 'patterns': []}
    
    def _analyze_simple_condition(self, condition: Condition) -> Dict:
        """
        単純条件を分析
        
        Args:
            condition: 条件分岐
        
        Returns:
            分析結果
        """
        return {
            'type': 'simple',
            'expression': condition.expression,
            'patterns': ['T', 'F'],
            'description': '単純なif文',
            'test_values': self._suggest_test_values(condition.expression)
        }
    
    def _analyze_or_condition(self, condition: Condition) -> Dict:
        """
        OR条件を分析
        
        Args:
            condition: 条件分岐
        
        Returns:
            分析結果
        """
        # 条件の数を取得
        conditions = condition.conditions if condition.conditions else [condition.left, condition.right]
        n_conditions = len(conditions)
        
        from src.truth_table.mcdc_pattern_generator import MCDCPatternGenerator
        mcdc_gen = MCDCPatternGenerator()
        patterns = mcdc_gen.generate_or_patterns(n_conditions)
        
        # MC/DC説明を生成
        mcdc_explanation = {}
        if n_conditions == 2:
            mcdc_explanation = {
                'TF': '左辺が真、右辺が偽',
                'FT': '左辺が偽、右辺が真',
                'FF': '両方偽'
            }
        elif n_conditions >= 3:
            for i, pattern in enumerate(patterns[:-1]):  # 最後のFFF以外
                true_index = pattern.index('T')
                mcdc_explanation[pattern] = f'条件{true_index + 1}が真、他が偽'
            mcdc_explanation[patterns[-1]] = '全て偽'
        
        return {
            'type': 'or',
            'expression': condition.expression,
            'conditions': conditions,
            'n_conditions': n_conditions,
            'left': condition.left,
            'right': condition.right,
            'patterns': patterns,
            'description': f'OR条件（||）- {n_conditions}個の条件',
            'mcdc_explanation': mcdc_explanation
        }
    
    def _analyze_and_condition(self, condition: Condition) -> Dict:
        """
        AND条件を分析
        
        Args:
            condition: 条件分岐
        
        Returns:
            分析結果
        """
        # 条件の数を取得
        conditions = condition.conditions if condition.conditions else [condition.left, condition.right]
        n_conditions = len(conditions)
        
        from src.truth_table.mcdc_pattern_generator import MCDCPatternGenerator
        mcdc_gen = MCDCPatternGenerator()
        patterns = mcdc_gen.generate_and_patterns(n_conditions)
        
        # MC/DC説明を生成
        mcdc_explanation = {}
        if n_conditions == 2:
            mcdc_explanation = {
                'TF': '左辺が真、右辺が偽',
                'FT': '左辺が偽、右辺が真',
                'TT': '両方真'
            }
        elif n_conditions >= 3:
            for i, pattern in enumerate(patterns[:-1]):  # 最後のTTT以外
                false_index = pattern.index('F')
                mcdc_explanation[pattern] = f'条件{false_index + 1}が偽、他が真'
            mcdc_explanation[patterns[-1]] = '全て真'
        
        return {
            'type': 'and',
            'expression': condition.expression,
            'conditions': conditions,
            'n_conditions': n_conditions,
            'left': condition.left,
            'right': condition.right,
            'patterns': patterns,
            'description': f'AND条件（&&）- {n_conditions}個の条件',
            'mcdc_explanation': mcdc_explanation
        }
    
    def _analyze_switch(self, condition: Condition) -> Dict:
        """
        switch文を分析
        
        Args:
            condition: 条件分岐
        
        Returns:
            分析結果
        """
        cases = condition.cases or []
        
        return {
            'type': 'switch',
            'expression': condition.expression,
            'cases': cases,
            'patterns': [f'case_{c}' for c in cases],
            'description': f'switch文（{len(cases)}個のcase）',
            'case_list': cases
        }
    
    def _suggest_test_values(self, expression: str) -> Dict[str, any]:
        """
        テスト値を提案
        
        Args:
            expression: 条件式
        
        Returns:
            テスト値の提案
        """
        suggestions = {
            'T': None,
            'F': None
        }
        
        # 比較演算子を検出
        comparison = self._parse_comparison(expression)
        
        if comparison:
            operator = comparison['operator']
            value = comparison['value']
            variable = comparison['variable']
            
            # 境界値を計算
            if operator == '>':
                suggestions['T'] = f"{variable} = {value + 1}"
                suggestions['F'] = f"{variable} = {value}"
            elif operator == '>=':
                suggestions['T'] = f"{variable} = {value}"
                suggestions['F'] = f"{variable} = {value - 1}"
            elif operator == '<':
                suggestions['T'] = f"{variable} = {value - 1}"
                suggestions['F'] = f"{variable} = {value}"
            elif operator == '<=':
                suggestions['T'] = f"{variable} = {value}"
                suggestions['F'] = f"{variable} = {value + 1}"
            elif operator == '==':
                suggestions['T'] = f"{variable} = {value}"
                suggestions['F'] = f"{variable} = {value + 1}"
            elif operator == '!=':
                suggestions['T'] = f"{variable} = {value + 1}"
                suggestions['F'] = f"{variable} = {value}"
        
        return suggestions
    
    def _parse_comparison(self, expression: str) -> Optional[Dict]:
        """
        比較演算子を含む式をパース
        
        Args:
            expression: 条件式
        
        Returns:
            パース結果（変数、演算子、値）
        """
        # 比較演算子のパターン
        patterns = [
            (r'(\w+)\s*>\s*(-?\d+)', '>'),
            (r'(\w+)\s*>=\s*(-?\d+)', '>='),
            (r'(\w+)\s*<\s*(-?\d+)', '<'),
            (r'(\w+)\s*<=\s*(-?\d+)', '<='),
            (r'(\w+)\s*==\s*(-?\d+)', '=='),
            (r'(\w+)\s*!=\s*(-?\d+)', '!='),
        ]
        
        for pattern, operator in patterns:
            match = re.search(pattern, expression)
            if match:
                return {
                    'variable': match.group(1),
                    'operator': operator,
                    'value': int(match.group(2))
                }
        
        return None
    
    def is_simple_condition(self, expression: str) -> bool:
        """
        単純条件かどうかを判定
        
        Args:
            expression: 条件式
        
        Returns:
            単純条件ならTrue
        """
        # OR/ANDを含まない
        return '||' not in expression and '&&' not in expression
    
    def is_or_condition(self, expression: str) -> bool:
        """
        OR条件かどうかを判定
        
        Args:
            expression: 条件式
        
        Returns:
            OR条件ならTrue
        """
        return '||' in expression
    
    def is_and_condition(self, expression: str) -> bool:
        """
        AND条件かどうかを判定
        
        Args:
            expression: 条件式
        
        Returns:
            AND条件ならTrue
        """
        return '&&' in expression
    
    def split_binary_condition(self, expression: str, operator: str) -> Tuple[str, str]:
        """
        二項条件を分割
        
        Args:
            expression: 条件式
            operator: 演算子（'||' or '&&'）
        
        Returns:
            (左辺, 右辺)
        """
        # 括弧を考慮して分割
        parts = expression.split(operator)
        
        if len(parts) >= 2:
            left = operator.join(parts[:-1]).strip()
            right = parts[-1].strip()
            
            # 不要な括弧を削除
            left = self._remove_outer_parentheses(left)
            right = self._remove_outer_parentheses(right)
            
            return left, right
        
        return expression, ""
    
    def _remove_outer_parentheses(self, expr: str) -> str:
        """
        外側の括弧を削除
        
        Args:
            expr: 式
        
        Returns:
            括弧削除後の式
        """
        expr = expr.strip()
        
        while expr.startswith('(') and expr.endswith(')'):
            # 対応する括弧かチェック
            depth = 0
            valid = True
            
            for i, char in enumerate(expr[1:-1], 1):
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth < 0:
                        valid = False
                        break
            
            if valid and depth == 0:
                expr = expr[1:-1].strip()
            else:
                break
        
        return expr


if __name__ == "__main__":
    # ConditionAnalyzerのテスト
    print("=== ConditionAnalyzer のテスト ===\n")
    
    from src.data_structures import Condition, ConditionType
    
    analyzer = ConditionAnalyzer()
    
    # テスト1: 単純条件
    print("1. 単純条件のテスト")
    cond1 = Condition(
        line=10,
        type=ConditionType.SIMPLE_IF,
        expression="(v10 > 30)"
    )
    result1 = analyzer.analyze_condition(cond1)
    print(f"   タイプ: {result1['type']}")
    print(f"   パターン: {result1['patterns']}")
    print(f"   テスト値: {result1['test_values']}")
    print()
    
    # テスト2: OR条件
    print("2. OR条件のテスト")
    cond2 = Condition(
        line=15,
        type=ConditionType.OR_CONDITION,
        expression="((mx63 == m47) || (mx63 == m46))",
        operator='or',
        left="(mx63 == m47)",
        right="(mx63 == m46)"
    )
    result2 = analyzer.analyze_condition(cond2)
    print(f"   タイプ: {result2['type']}")
    print(f"   パターン: {result2['patterns']}")
    print(f"   説明: {result2['mcdc_explanation']}")
    print()
    
    # テスト3: AND条件
    print("3. AND条件のテスト")
    cond3 = Condition(
        line=20,
        type=ConditionType.AND_CONDITION,
        expression="((a > 0) && (b < 10))",
        operator='and',
        left="(a > 0)",
        right="(b < 10)"
    )
    result3 = analyzer.analyze_condition(cond3)
    print(f"   タイプ: {result3['type']}")
    print(f"   パターン: {result3['patterns']}")
    print(f"   説明: {result3['mcdc_explanation']}")
    print()
    
    # テスト4: switch文
    print("4. switch文のテスト")
    cond4 = Condition(
        line=30,
        type=ConditionType.SWITCH,
        expression="v9",
        cases=['0', '1', '2', 'default']
    )
    result4 = analyzer.analyze_condition(cond4)
    print(f"   タイプ: {result4['type']}")
    print(f"   パターン: {result4['patterns']}")
    print(f"   case一覧: {result4['case_list']}")
    print()
    
    print("✓ ConditionAnalyzerが正常に動作しました")
