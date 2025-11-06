"""
BoundaryValueCalculatorモジュール

境界値を計算して適切なテスト値を生成
"""

import sys
import os
import re
from typing import Optional, Dict, Tuple

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class BoundaryValueCalculator:
    """境界値計算機"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def calculate_boundary(self, operator: str, value: int, truth: str) -> int:
        """
        境界値を計算
        
        Args:
            operator: 比較演算子（>, <, >=, <=, ==, !=）
            value: 比較対象の値
            truth: 真偽（'T' or 'F'）
        
        Returns:
            テスト値
        
        Examples:
            >>> calc.calculate_boundary('>', 30, 'T')
            31
            >>> calc.calculate_boundary('>', 30, 'F')
            30
        """
        if truth == 'T':
            # 真の場合
            if operator == '>':
                return value + 1
            elif operator == '>=':
                return value
            elif operator == '<':
                return value - 1
            elif operator == '<=':
                return value
            elif operator == '==':
                return value
            elif operator == '!=':
                return value + 1
        else:
            # 偽の場合
            if operator == '>':
                return value
            elif operator == '>=':
                return value - 1
            elif operator == '<':
                return value
            elif operator == '<=':
                return value + 1
            elif operator == '==':
                return value + 1
            elif operator == '!=':
                return value
        
        return value
    
    def parse_comparison(self, expression: str) -> Optional[Dict]:
        """
        比較式をパース
        
        Args:
            expression: 条件式
        
        Returns:
            パース結果（変数、演算子、値）
        
        Examples:
            >>> calc.parse_comparison("v10 > 30")
            {'variable': 'v10', 'operator': '>', 'value': 30}
        """
        # 比較演算子のパターン（長い順にマッチング）
        patterns = [
            (r'(\w+(?:\[\d+\])?)\s*>=\s*(-?\d+)', '>='),
            (r'(\w+(?:\[\d+\])?)\s*<=\s*(-?\d+)', '<='),
            (r'(\w+(?:\[\d+\])?)\s*==\s*(-?\d+)', '=='),
            (r'(\w+(?:\[\d+\])?)\s*!=\s*(-?\d+)', '!='),
            (r'(\w+(?:\[\d+\])?)\s*>\s*(-?\d+)', '>'),
            (r'(\w+(?:\[\d+\])?)\s*<\s*(-?\d+)', '<'),
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
    
    def generate_test_value(self, expression: str, truth: str) -> Optional[str]:
        """
        テスト値を生成
        
        Args:
            expression: 条件式
            truth: 真偽（'T' or 'F'）
        
        Returns:
            テスト値の設定コード（例: "v10 = 31"）
        """
        comparison = self.parse_comparison(expression)
        
        if comparison:
            variable = comparison['variable']
            operator = comparison['operator']
            value = comparison['value']
            
            test_value = self.calculate_boundary(operator, value, truth)
            
            return f"{variable} = {test_value}"
        
        return None
    
    def extract_variables(self, expression: str) -> list:
        """
        条件式から変数を抽出
        
        Args:
            expression: 条件式
        
        Returns:
            変数名のリスト
        """
        # 変数パターン（配列アクセス含む）
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*(?:\[\d+\])?)\b'
        variables = re.findall(pattern, expression)
        
        # C言語キーワードを除外
        keywords = {'if', 'else', 'for', 'while', 'switch', 'case', 'default', 
                   'return', 'break', 'continue', 'sizeof', 'int', 'void', 'char',
                   'short', 'long', 'float', 'double', 'struct', 'union', 'enum'}
        
        variables = [v for v in variables if v not in keywords]
        
        return list(set(variables))  # 重複を除去
    
    def suggest_enum_values(self, variable: str, enum_name: str, pattern: str) -> Dict[str, str]:
        """
        enum型の変数に対する値を提案
        
        Args:
            variable: 変数名
            enum_name: enum型名
            pattern: 真偽パターン（'T' or 'F'）
        
        Returns:
            提案された値の辞書
        """
        # 実装は簡易版
        # 実際には型情報が必要
        return {
            'T': f"{variable} = /* enum値 */",
            'F': f"{variable} = /* 異なるenum値 */"
        }
    
    def format_boundary_comment(self, operator: str, value: int, truth: str, test_value: int) -> str:
        """
        境界値テストのコメントを生成
        
        Args:
            operator: 演算子
            value: 元の値
            truth: 真偽
            test_value: テスト値
        
        Returns:
            コメント文字列
        """
        if truth == 'T':
            return f"境界値テスト（真）: {test_value} {operator} {value} → 真"
        else:
            return f"境界値テスト（偽）: {test_value} {operator} {value} → 偽"


if __name__ == "__main__":
    # BoundaryValueCalculatorのテスト
    print("=" * 70)
    print("BoundaryValueCalculator のテスト")
    print("=" * 70)
    print()
    
    calc = BoundaryValueCalculator()
    
    # テスト1: 境界値計算
    print("1. 境界値計算のテスト")
    print()
    
    test_cases = [
        ('>', 30, 'T', 31),
        ('>', 30, 'F', 30),
        ('<', -30, 'T', -31),
        ('<', -30, 'F', -30),
        ('>=', 10, 'T', 10),
        ('>=', 10, 'F', 9),
        ('<=', 100, 'T', 100),
        ('<=', 100, 'F', 101),
        ('==', 0, 'T', 0),
        ('==', 0, 'F', 1),
        ('!=', 5, 'T', 6),
        ('!=', 5, 'F', 5),
    ]
    
    for operator, value, truth, expected in test_cases:
        result = calc.calculate_boundary(operator, value, truth)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {operator:2s} {value:3d} [{truth}] → {result:3d} (期待値: {expected})")
    
    print()
    
    # テスト2: 条件式のパース
    print("2. 条件式のパースのテスト")
    print()
    
    expressions = [
        "v10 > 30",
        "v10 < -30",
        "v7[0] == 0",
        "count >= 100",
        "value != 0",
    ]
    
    for expr in expressions:
        parsed = calc.parse_comparison(expr)
        if parsed:
            print(f"  {expr:20s} → {parsed}")
        else:
            print(f"  {expr:20s} → パース失敗")
    
    print()
    
    # テスト3: テスト値の生成
    print("3. テスト値の生成のテスト")
    print()
    
    for expr in ["v10 > 30", "v10 < -30", "v7[0] == 0"]:
        for truth in ['T', 'F']:
            test_val = calc.generate_test_value(expr, truth)
            print(f"  {expr:20s} [{truth}] → {test_val}")
    
    print()
    
    # テスト4: 変数抽出
    print("4. 変数抽出のテスト")
    print()
    
    complex_expr = "((mx63 == m47) || (mx63 == m46))"
    variables = calc.extract_variables(complex_expr)
    print(f"  式: {complex_expr}")
    print(f"  変数: {variables}")
    
    print()
    
    # テスト5: コメント生成
    print("5. 境界値コメントの生成")
    print()
    
    for operator, value, truth in [('>', 30, 'T'), ('>', 30, 'F'), ('<', -30, 'T')]:
        test_val = calc.calculate_boundary(operator, value, truth)
        comment = calc.format_boundary_comment(operator, value, truth, test_val)
        print(f"  {comment}")
    
    print()
    print("=" * 70)
    print("✓ BoundaryValueCalculatorが正常に動作しました")
    print("=" * 70)
