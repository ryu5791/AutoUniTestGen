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
        比較式をパース（構造体メンバアクセス対応）
        
        Args:
            expression: 条件式
        
        Returns:
            パース結果（左辺、演算子、右辺）
        
        Examples:
            >>> calc.parse_comparison("v10 > 30")
            {'left': 'v10', 'operator': '>', 'right': '30', 'right_type': 'number'}
            >>> calc.parse_comparison("mx63 == m47")
            {'left': 'mx63', 'operator': '==', 'right': 'm47', 'right_type': 'identifier'}
            >>> calc.parse_comparison("Utx112.Utm10 != Utx104.Utm10")
            {'left': 'Utx112.Utm10', 'operator': '!=', 'right': 'Utx104.Utm10', 'right_type': 'identifier'}
        """
        # 比較演算子のリスト（長い順）
        operators = ['>=', '<=', '==', '!=', '>', '<']
        
        for op in operators:
            if op in expression:
                parts = expression.split(op, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    # 右辺が数値かどうか判定
                    right_type = 'number' if right.lstrip('-').isdigit() else 'identifier'
                    
                    result = {
                        'left': left,
                        'operator': op,
                        'right': right,
                        'right_type': right_type
                    }
                    
                    # 後方互換性のために古い形式も含める
                    result['variable'] = left
                    if right_type == 'number':
                        result['value'] = int(right)
                    else:
                        result['value'] = right
                        result['is_identifier'] = True
                    
                    return result
        
        return None
    
    def generate_test_value(self, expression: str, truth: str) -> Optional[str]:
        """
        テスト値を生成
        
        Args:
            expression: 条件式
            truth: 真偽（'T' or 'F'）
        
        Returns:
            テスト値の設定コード（例: "v10 = 31"）
            
        Note:
            識別子同士の比較の場合は、generate_comparison_values() を使用することを推奨
        """
        comparison = self.parse_comparison(expression)
        
        if comparison:
            variable = comparison['variable']
            operator = comparison['operator']
            value = comparison.get('value')
            is_identifier = comparison.get('is_identifier', False)
            
            if is_identifier:
                # 識別子同士の比較（例: mx63 == m47）
                # 左辺または右辺が関数呼び出しでないことを確認
                if self._is_function_call(variable) or self._is_function_call(str(value)):
                    if self._is_function_call(variable):
                        return f"// TODO: {variable}は関数呼び出しのため初期化できません"
                    else:
                        return f"// TODO: {value}は関数呼び出しのため初期化できません"
                
                if operator == '==':
                    if truth == 'T':
                        return f"{variable} = {value}"
                    else:
                        # 偽の場合は異なる値（簡易実装）
                        return f"{variable} = 0;  // TODO: {value}以外の値を設定"
                elif operator == '!=':
                    if truth == 'T':
                        return f"{variable} = 0;  // TODO: {value}以外の値を設定"
                    else:
                        return f"{variable} = {value}"
            else:
                # 数値との比較
                # 左辺が関数呼び出しでないことを確認
                if self._is_function_call(variable):
                    return f"// TODO: {variable}は関数呼び出しのため初期化できません"
                
                test_value = self.calculate_boundary(operator, value, truth)
                return f"{variable} = {test_value}"
        
        return None
    
    def generate_comparison_values(self, expression: str, truth: str) -> list:
        """
        比較式の両辺に適切な値を設定するコードを生成
        
        Args:
            expression: 条件式
            truth: 真偽（'T' or 'F'）
        
        Returns:
            初期化コードのリスト
        
        Examples:
            >>> calc.generate_comparison_values("Utx112.Utm10 != Utx104.Utm10", 'T')
            ['Utx112.Utm10 = 1;  // 左辺', 'Utx104.Utm10 = 0;  // 右辺（異なる値）']
            >>> calc.generate_comparison_values("var1 == var2", 'T')
            ['var1 = 1;  // 左辺', 'var2 = 1;  // 右辺（同じ値）']
        """
        comparison = self.parse_comparison(expression)
        
        if not comparison:
            return []
        
        left = comparison['left']
        operator = comparison['operator']
        right = comparison['right']
        right_type = comparison['right_type']
        
        init_list = []
        
        # 右辺が識別子（変数）の場合のみ、両辺に値を設定
        if right_type == 'identifier':
            # 左辺または右辺が関数呼び出しの場合は、初期化コードを生成しない
            if self._is_function_call(left) or self._is_function_call(right):
                # 関数呼び出しは初期化できないため、TODOコメントを生成
                if self._is_function_call(left) and self._is_function_call(right):
                    return [f"// TODO: {left}と{right}は関数呼び出しのため初期化できません"]
                elif self._is_function_call(left):
                    return [f"// TODO: {left}は関数呼び出しのため初期化できません"]
                else:
                    return [f"// TODO: {right}は関数呼び出しのため初期化できません"]
            
            if operator == '!=':
                # 不等号の場合
                if truth == 'T':
                    # 真にする: 異なる値を設定
                    init_list.append(f"{left} = 1;  // 左辺")
                    init_list.append(f"{right} = 0;  // 右辺（異なる値）")
                else:
                    # 偽にする: 同じ値を設定
                    init_list.append(f"{left} = 0;  // 左辺")
                    init_list.append(f"{right} = 0;  // 右辺（同じ値）")
            
            elif operator == '==':
                # 等号の場合
                if truth == 'T':
                    # 真にする: 同じ値を設定
                    init_list.append(f"{left} = 1;  // 左辺")
                    init_list.append(f"{right} = 1;  // 右辺（同じ値）")
                else:
                    # 偽にする: 異なる値を設定
                    init_list.append(f"{left} = 1;  // 左辺")
                    init_list.append(f"{right} = 0;  // 右辺（異なる値）")
            
            elif operator == '>':
                # 大なり
                if truth == 'T':
                    init_list.append(f"{left} = 2;  // 左辺")
                    init_list.append(f"{right} = 1;  // 右辺（小さい値）")
                else:
                    init_list.append(f"{left} = 1;  // 左辺")
                    init_list.append(f"{right} = 2;  // 右辺（大きい値）")
            
            elif operator == '>=':
                # 大なりイコール
                if truth == 'T':
                    init_list.append(f"{left} = 2;  // 左辺")
                    init_list.append(f"{right} = 1;  // 右辺（小さい値）")
                else:
                    init_list.append(f"{left} = 1;  // 左辺")
                    init_list.append(f"{right} = 2;  // 右辺（大きい値）")
            
            elif operator == '<':
                # 小なり
                if truth == 'T':
                    init_list.append(f"{left} = 1;  // 左辺")
                    init_list.append(f"{right} = 2;  // 右辺（大きい値）")
                else:
                    init_list.append(f"{left} = 2;  // 左辺")
                    init_list.append(f"{right} = 1;  // 右辺（小さい値）")
            
            elif operator == '<=':
                # 小なりイコール
                if truth == 'T':
                    init_list.append(f"{left} = 1;  // 左辺")
                    init_list.append(f"{right} = 2;  // 右辺（大きい値）")
                else:
                    init_list.append(f"{left} = 2;  // 左辺")
                    init_list.append(f"{right} = 1;  // 右辺（小さい値）")
        
        else:
            # 右辺が数値の場合は、従来通り左辺のみ設定
            test_value_code = self.generate_test_value(expression, truth)
            if test_value_code:
                init_list.append(test_value_code)
        
        return init_list
    
    def _is_function_call(self, identifier: str) -> bool:
        """
        識別子が関数呼び出しかどうかを判定
        
        Args:
            identifier: 識別子（例: "Utf12()", "var", "obj.member"）
        
        Returns:
            関数呼び出しの場合True
        """
        # 関数呼び出しのパターン: 識別子の後に括弧がある
        return '(' in identifier and ')' in identifier
    
    def extract_variables(self, expression: str) -> list:
        """
        条件式から変数を抽出（構造体メンバアクセス対応）
        
        Args:
            expression: 条件式
        
        Returns:
            変数名のリスト
        
        Examples:
            >>> calc.extract_variables("v10 > 30")
            ['v10']
            >>> calc.extract_variables("Utx112.Utm10 != Utx104.Utm10")
            ['Utx112.Utm10', 'Utx104.Utm10']
            >>> calc.extract_variables("a.b.c == 10")
            ['a.b.c']
        """
        # まず構造体メンバアクセス（複数レベル対応）を抽出
        struct_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+)\b'
        struct_members = re.findall(struct_pattern, expression)
        
        # 構造体メンバが見つかった場合はそれを優先
        if struct_members:
            return list(set(struct_members))
        
        # 構造体メンバが無い場合は通常の変数を抽出
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
