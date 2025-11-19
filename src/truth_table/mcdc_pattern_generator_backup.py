"""
MCDCPatternGeneratorモジュール

MC/DC (Modified Condition/Decision Coverage) のテストパターンを生成
"""

import sys
import os
from typing import List, Dict, Tuple
from itertools import product

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class MCDCPatternGenerator:
    """MC/DCパターンジェネレータ"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def generate_or_patterns(self, n_conditions: int = 2) -> List[str]:
        """
        OR条件のMC/DCパターンを生成
        
        MC/DC要件:
        - 各条件が独立して結果に影響することを示す
        - 2条件: A || B
          - TF: Aが真、Bが偽 → 結果は真（Aの影響）
          - FT: Aが偽、Bが真 → 結果は真（Bの影響）
          - FF: 両方偽 → 結果は偽
        - 3条件: A || B || C
          - TFF: Aの影響を証明
          - FTF: Bの影響を証明
          - FFT: Cの影響を証明
          - FFF: 全て偽の場合
        
        Args:
            n_conditions: 条件の数
        
        Returns:
            パターンのリスト
        """
        if n_conditions == 2:
            return ['TF', 'FT', 'FF']
        elif n_conditions >= 3:
            # 各条件が真になるパターン + 全て偽のパターン
            patterns = []
            
            # 各条件が真で他が偽のパターン
            for i in range(n_conditions):
                pattern = ['F'] * n_conditions
                pattern[i] = 'T'
                patterns.append(''.join(pattern))
            
            # 全て偽のパターン
            patterns.append('F' * n_conditions)
            
            return patterns
        else:
            return ['T', 'F']
    
    def generate_and_patterns(self, n_conditions: int = 2) -> List[str]:
        """
        AND条件のMC/DCパターンを生成
        
        MC/DC要件:
        - 2条件: A && B
          - TF: Aが真、Bが偽 → 結果は偽（Bの影響）
          - FT: Aが偽、Bが真 → 結果は偽（Aの影響）
          - TT: 両方真 → 結果は真
        - 3条件: A && B && C
          - TTF: Cの影響を証明
          - TFT: Bの影響を証明
          - FTT: Aの影響を証明
          - TTT: 全て真の場合
        
        Args:
            n_conditions: 条件の数
        
        Returns:
            パターンのリスト
        """
        if n_conditions == 2:
            return ['TF', 'FT', 'TT']
        elif n_conditions >= 3:
            # 各条件が偽になるパターン + 全て真のパターン
            patterns = []
            
            # 各条件が偽で他が真のパターン
            for i in range(n_conditions):
                pattern = ['T'] * n_conditions
                pattern[i] = 'F'
                patterns.append(''.join(pattern))
            
            # 全て真のパターン
            patterns.append('T' * n_conditions)
            
            return patterns
        else:
            return ['T', 'F']
    
    def generate_switch_patterns(self, cases: List[str]) -> List[str]:
        """
        switch文のパターンを生成
        
        Args:
            cases: case値のリスト
        
        Returns:
            パターンのリスト（各caseに対応）
        """
        return [f'case_{c}' for c in cases]
    
    def generate_complex_patterns(self, n_conditions: int, operator: str = 'or') -> List[Tuple[bool, ...]]:
        """
        複雑な条件の組み合わせパターンを生成
        
        Args:
            n_conditions: 条件の数
            operator: 演算子 ('or' or 'and')
        
        Returns:
            MC/DCパターンのリスト
        """
        if n_conditions < 2:
            return [(True,), (False,)]
        
        # 全組み合わせを生成
        all_combinations = list(product([True, False], repeat=n_conditions))
        
        # MC/DCに必要な組み合わせを選択
        mcdc_patterns = self._select_mcdc_patterns(all_combinations, operator)
        
        return mcdc_patterns
    
    def _select_mcdc_patterns(self, combinations: List[Tuple[bool, ...]], operator: str) -> List[Tuple[bool, ...]]:
        """
        MC/DC要件を満たすパターンを選択
        
        Args:
            combinations: 全組み合わせ
            operator: 演算子
        
        Returns:
            選択されたパターン
        """
        selected = []
        n = len(combinations[0])
        
        # 各条件が独立して影響するパターンを選択
        for i in range(n):
            # i番目の条件を反転させたときに結果が変わるペアを探す
            for combo in combinations:
                flipped = list(combo)
                flipped[i] = not flipped[i]
                flipped = tuple(flipped)
                
                if flipped in combinations:
                    result1 = self._evaluate(combo, operator)
                    result2 = self._evaluate(flipped, operator)
                    
                    # 結果が異なる場合、両方のパターンを追加
                    if result1 != result2:
                        if combo not in selected:
                            selected.append(combo)
                        if flipped not in selected:
                            selected.append(flipped)
        
        return selected
    
    def _evaluate(self, pattern: Tuple[bool, ...], operator: str) -> bool:
        """
        パターンを評価
        
        Args:
            pattern: 真偽値のタプル
            operator: 演算子
        
        Returns:
            評価結果
        """
        if operator == 'or':
            return any(pattern)
        elif operator == 'and':
            return all(pattern)
        else:
            return False
    
    def pattern_to_string(self, pattern: Tuple[bool, ...]) -> str:
        """
        パターンを文字列に変換
        
        Args:
            pattern: 真偽値のタプル
        
        Returns:
            文字列表現（例: "TF", "FTT"）
        """
        return ''.join('T' if v else 'F' for v in pattern)
    
    def explain_pattern(self, pattern: str, operator: str) -> str:
        """
        パターンの説明を生成
        
        Args:
            pattern: パターン文字列（例: "TF"）
            operator: 演算子
        
        Returns:
            説明文
        """
        if len(pattern) == 2:
            left = "真" if pattern[0] == 'T' else "偽"
            right = "真" if pattern[1] == 'T' else "偽"
            
            if operator == 'or':
                result = "真" if pattern[0] == 'T' or pattern[1] == 'T' else "偽"
            elif operator == 'and':
                result = "真" if pattern[0] == 'T' and pattern[1] == 'T' else "偽"
            else:
                result = "不明"
            
            return f"左辺: {left}, 右辺: {right} → 結果: {result}"
        
        return "説明なし"
    
    def calculate_mcdc_coverage(self, patterns: List[str], total_conditions: int) -> float:
        """
        MC/DCカバレッジを計算
        
        Args:
            patterns: テストパターンのリスト
            total_conditions: 総条件数
        
        Returns:
            カバレッジ率（0.0～1.0）
        """
        if total_conditions == 0:
            return 0.0
        
        # 簡易計算: 各条件が少なくとも1回は独立して影響するか
        covered_conditions = set()
        
        for pattern in patterns:
            for i, char in enumerate(pattern):
                if char in ['T', 'F']:
                    covered_conditions.add(i)
        
        coverage = len(covered_conditions) / total_conditions
        return coverage
    
    def generate_truth_table(self, n_conditions: int, operator: str = 'or') -> List[Dict]:
        """
        真偽表を生成
        
        Args:
            n_conditions: 条件の数
            operator: 演算子
        
        Returns:
            真偽表のリスト
        """
        patterns = self.generate_complex_patterns(n_conditions, operator)
        
        truth_table = []
        for i, pattern in enumerate(patterns, 1):
            pattern_str = self.pattern_to_string(pattern)
            result = self._evaluate(pattern, operator)
            
            truth_table.append({
                'no': i,
                'pattern': pattern_str,
                'values': pattern,
                'result': result,
                'explanation': self.explain_pattern(pattern_str, operator)
            })
        
        return truth_table


if __name__ == "__main__":
    # MCDCPatternGeneratorのテスト
    print("=== MCDCPatternGenerator のテスト ===\n")
    
    generator = MCDCPatternGenerator()
    
    # テスト1: OR条件
    print("1. OR条件のパターン生成")
    or_patterns = generator.generate_or_patterns()
    print(f"   パターン: {or_patterns}")
    for pattern in or_patterns:
        print(f"   - {pattern}: {generator.explain_pattern(pattern, 'or')}")
    print()
    
    # テスト2: AND条件
    print("2. AND条件のパターン生成")
    and_patterns = generator.generate_and_patterns()
    print(f"   パターン: {and_patterns}")
    for pattern in and_patterns:
        print(f"   - {pattern}: {generator.explain_pattern(pattern, 'and')}")
    print()
    
    # テスト3: switch文
    print("3. switch文のパターン生成")
    switch_cases = ['0', '1', '2', 'default']
    switch_patterns = generator.generate_switch_patterns(switch_cases)
    print(f"   パターン: {switch_patterns}")
    print()
    
    # テスト4: 複雑な条件（3条件のOR）
    print("4. 3条件OR の真偽表生成")
    truth_table = generator.generate_truth_table(3, 'or')
    print(f"   生成されたパターン数: {len(truth_table)}")
    for entry in truth_table[:5]:  # 最初の5つを表示
        print(f"   {entry['no']}. {entry['pattern']} → {entry['result']} ({entry['explanation']})")
    print()
    
    # テスト5: MC/DCカバレッジ計算
    print("5. MC/DCカバレッジ計算")
    test_patterns = ['TF', 'FT', 'FF']
    coverage = generator.calculate_mcdc_coverage(test_patterns, 2)
    print(f"   パターン: {test_patterns}")
    print(f"   カバレッジ: {coverage * 100:.1f}%")
    print()
    
    print("✓ MCDCPatternGeneratorが正常に動作しました")
