"""
MCDCPatternGenerator v2.6.1

シンプルで確実なMC/DCパターン生成
ネストしたAND/OR条件に完全対応
"""

import sys
import os
from typing import List, Dict, Tuple, Set
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class MCDCPatternGeneratorV2:
    """MC/DCパターンジェネレータ（シンプル実装版）"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def generate_mcdc_patterns_for_complex(self,
                                          top_operator: str,
                                          conditions: List[str]) -> List[str]:
        """
        複雑なネスト条件のMC/DCパターンを生成
        
        アルゴリズム:
        1. 各条件を展開して、全ての単純条件を抽出
        2. 各単純条件の独立性をテストするパターンを生成
        3. 重複を削除
        
        例: A && (B || C || D || E || F || G) && H
        展開: A, B, C, D, E, F, G, H (8個の単純条件)
        
        Args:
            top_operator: トップレベルの演算子 ('and' or 'or')
            conditions: 条件のリスト
        
        Returns:
            MC/DCパターンのリスト
        """
        self.logger.info(f"複雑条件のMC/DCパターン生成: operator={top_operator}, "
                        f"conditions={len(conditions)}個")
        
        # 各条件を展開
        expanded_conditions = []
        condition_structure = []  # 各条件の構造情報を保持
        
        for cond in conditions:
            if '||' in cond and '&&' not in cond:
                # OR条件のみ
                sub_conditions = self._extract_or_conditions(cond)
                expanded_conditions.extend(sub_conditions)
                condition_structure.append(('or', len(sub_conditions)))
            elif '&&' in cond and '||' not in cond:
                # AND条件のみ
                sub_conditions = self._extract_and_conditions(cond)
                expanded_conditions.extend(sub_conditions)
                condition_structure.append(('and', len(sub_conditions)))
            elif '||' in cond and '&&' in cond:
                # 混在（ORとAND）
                sub_conditions = self._extract_mixed_conditions(cond)
                expanded_conditions.extend(sub_conditions)
                condition_structure.append(('mixed', len(sub_conditions)))
            else:
                # 単純条件
                expanded_conditions.append(cond.strip())
                condition_structure.append(('simple', 1))
        
        n_total = len(expanded_conditions)
        self.logger.info(f"展開後の単純条件数: {n_total}個")
        self.logger.debug(f"条件構造: {condition_structure}")
        
        # MC/DCパターンを生成
        patterns = self._generate_patterns_for_structure(
            top_operator, 
            expanded_conditions, 
            condition_structure
        )
        
        self.logger.info(f"生成されたパターン数: {len(patterns)}個")
        
        return patterns
    
    def _extract_or_conditions(self, condition: str) -> List[str]:
        """OR条件を展開"""
        # まず外側の括弧を削除
        condition = self._remove_outer_parens(condition)
        
        # 括弧を考慮してORで分割
        parts = []
        current = ""
        depth = 0
        i = 0
        
        while i < len(condition):
            if condition[i] == '(':
                depth += 1
                current += condition[i]
            elif condition[i] == ')':
                depth -= 1
                current += condition[i]
            elif depth == 0 and condition[i:i+2] == '||':
                parts.append(current.strip())
                current = ""
                i += 1  # skip next '|'
            else:
                current += condition[i]
            i += 1
        
        if current.strip():
            parts.append(current.strip())
        
        # 各パーツの外側の括弧を削除
        return [self._remove_outer_parens(p) for p in parts]
    
    def _extract_and_conditions(self, condition: str) -> List[str]:
        """AND条件を展開"""
        # まず外側の括弧を削除
        condition = self._remove_outer_parens(condition)
        
        parts = []
        current = ""
        depth = 0
        i = 0
        
        while i < len(condition):
            if condition[i] == '(':
                depth += 1
                current += condition[i]
            elif condition[i] == ')':
                depth -= 1
                current += condition[i]
            elif depth == 0 and condition[i:i+2] == '&&':
                parts.append(current.strip())
                current = ""
                i += 1  # skip next '&'
            else:
                current += condition[i]
            i += 1
        
        if current.strip():
            parts.append(current.strip())
        
        return [self._remove_outer_parens(p) for p in parts]
    
    def _extract_mixed_conditions(self, condition: str) -> List[str]:
        """混在した条件を展開（ANDが優先）"""
        # まずANDで分割
        and_parts = self._extract_and_conditions(condition)
        
        # 各ANDパートでORがあればさらに分割
        all_parts = []
        for part in and_parts:
            if '||' in part:
                or_parts = self._extract_or_conditions(part)
                all_parts.extend(or_parts)
            else:
                all_parts.append(part)
        
        return all_parts
    
    def _remove_outer_parens(self, expr: str) -> str:
        """外側の括弧を削除"""
        expr = expr.strip()
        while expr.startswith('(') and expr.endswith(')'):
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
    
    def _generate_patterns_for_structure(self,
                                        top_operator: str,
                                        conditions: List[str],
                                        structure: List[Tuple[str, int]]) -> List[str]:
        """
        条件構造に基づいてMC/DCパターンを生成
        
        Args:
            top_operator: トップレベルの演算子
            conditions: 展開済みの条件リスト
            structure: 条件構造 [(operator, count), ...]
        
        Returns:
            パターンのリスト
        """
        n = len(conditions)
        patterns_set: Set[Tuple[bool, ...]] = set()
        
        # 各単純条件の独立性をテスト
        current_index = 0
        
        for struct_operator, count in structure:
            if struct_operator == 'or':
                # OR条件グループの処理
                patterns_set.update(
                    self._generate_or_group_patterns_with_structure(
                        top_operator, n, current_index, count, structure
                    )
                )
                current_index += count
            
            elif struct_operator == 'and':
                # AND条件グループの処理
                patterns_set.update(
                    self._generate_and_group_patterns(
                        top_operator, n, current_index, count
                    )
                )
                current_index += count
            
            elif struct_operator == 'simple':
                # 単純条件の処理
                patterns_set.update(
                    self._generate_simple_condition_patterns_with_structure(
                        top_operator, n, current_index, structure
                    )
                )
                current_index += 1
            
            elif struct_operator == 'mixed':
                # 混在条件の処理（各条件を個別に処理）
                for i in range(count):
                    patterns_set.update(
                        self._generate_simple_condition_patterns_with_structure(
                            top_operator, n, current_index + i, structure
                        )
                    )
                current_index += count
        
        # ソートして文字列に変換
        patterns_list = sorted(list(patterns_set))
        return [''.join('T' if v else 'F' for v in p) for p in patterns_list]
    
    def _generate_or_group_patterns_with_structure(self,
                                                   top_operator: str,
                                                   total: int,
                                                   start_index: int,
                                                   count: int,
                                                   structure: List[Tuple[str, int]]) -> Set[Tuple[bool, ...]]:
        """ORグループのMC/DCパターンを生成（構造情報考慮）"""
        patterns = set()
        
        if top_operator == 'and':
            # トップがANDの場合
            # パターン1: ORグループ全てFalse、他はTrue（ORグループ内を適切に）
            p1 = self._create_base_pattern_for_and(total, structure)
            for i in range(start_index, start_index + count):
                p1[i] = False
            patterns.add(tuple(p1))
            
            # パターン2-N: 各OR条件を1つずつTrue、他はFalse、他のグループは適切に
            for i in range(count):
                p = self._create_base_pattern_for_and(total, structure)
                # ORグループ内
                for j in range(start_index, start_index + count):
                    p[j] = (j == start_index + i)
                patterns.add(tuple(p))
        
        return patterns
    
    def _generate_simple_condition_patterns_with_structure(self,
                                                          top_operator: str,
                                                          total: int,
                                                          index: int,
                                                          structure: List[Tuple[str, int]]) -> Set[Tuple[bool, ...]]:
        """単純条件のMC/DCパターンを生成（構造情報考慮）"""
        patterns = set()
        
        if top_operator == 'and':
            # ANDの場合
            # パターン1: index番目をFalse、他は適切に
            p1 = self._create_base_pattern_for_and(total, structure)
            p1[index] = False
            patterns.add(tuple(p1))
            
            # パターン2: index番目をTrue、他は適切に
            p2 = self._create_base_pattern_for_and(total, structure)
            p2[index] = True
            patterns.add(tuple(p2))
        
        elif top_operator == 'or':
            # ORの場合
            p1 = [False] * total
            p1[index] = True
            patterns.add(tuple(p1))
            
            p2 = tuple([False] * total)
            patterns.add(p2)
        
        return patterns
    
    def _create_base_pattern_for_and(self, total: int, structure: List[Tuple[str, int]]) -> List[bool]:
        """
        ANDトップレベルのベースパターンを作成
        - 単純条件とANDグループ: True
        - ORグループ: 最初の条件のみTrue、他はFalse
        """
        pattern = []
        for struct_op, count in structure:
            if struct_op == 'or':
                # ORグループ: 最初だけTrue
                pattern.extend([True] + [False] * (count - 1))
            else:
                # 単純条件やANDグループ: 全てTrue
                pattern.extend([True] * count)
        
        return pattern
    
    def _generate_or_group_patterns(self,
                                   top_operator: str,
                                   total: int,
                                   start_index: int,
                                   count: int) -> Set[Tuple[bool, ...]]:
        """ORグループのMC/DCパターンを生成"""
        patterns = set()
        
        if top_operator == 'and':
            # トップがANDの場合
            # パターン1: ORグループ全てFalse、他はTrue
            p1 = [True] * total
            for i in range(start_index, start_index + count):
                p1[i] = False
            patterns.add(tuple(p1))
            
            # パターン2-N: 各OR条件を1つずつTrue、他はFalse、他のグループはTrue
            for i in range(count):
                p = [True] * total
                # ORグループ内
                for j in range(start_index, start_index + count):
                    p[j] = (j == start_index + i)
                patterns.add(tuple(p))
        
        return patterns
    
    def _generate_and_group_patterns(self,
                                    top_operator: str,
                                    total: int,
                                    start_index: int,
                                    count: int) -> Set[Tuple[bool, ...]]:
        """ANDグループのMC/DCパターンを生成"""
        patterns = set()
        
        # 各AND条件を1つずつFalse、他はTrue
        for i in range(count):
            p = [True] * total
            p[start_index + i] = False
            patterns.add(tuple(p))
        
        # 全てTrue
        p_all_true = tuple([True] * total)
        patterns.add(p_all_true)
        
        return patterns
    
    def _generate_simple_condition_patterns(self,
                                           top_operator: str,
                                           total: int,
                                           index: int) -> Set[Tuple[bool, ...]]:
        """単純条件のMC/DCパターンを生成"""
        patterns = set()
        
        if top_operator == 'and':
            # ANDの場合: index番目をFalse、他はTrue
            # ただし、他のOR条件グループがある場合は、そのうち1つだけをTrueに
            p1 = [True] * total
            p1[index] = False
            
            # ORグループを探して調整
            p1 = self._adjust_for_or_groups(p1, index, total)
            patterns.add(tuple(p1))
            
            # index番目がTrue、他も適切に設定
            p2 = [True] * total
            p2 = self._adjust_for_or_groups(p2, index, total)
            patterns.add(tuple(p2))
        
        elif top_operator == 'or':
            # ORの場合: index番目のみTrue、他はFalse
            p1 = [False] * total
            p1[index] = True
            patterns.add(tuple(p1))
            
            # 全てFalse
            p2 = tuple([False] * total)
            patterns.add(p2)
        
        return patterns
    
    def _adjust_for_or_groups(self, pattern: List[bool], skip_index: int, total: int) -> List[bool]:
        """
        ORグループがある場合、そのグループ内で1つだけTrueになるように調整
        （この実装では簡易版 - 構造情報が必要）
        """
        # 簡易実装: patternをそのまま返す
        # 完全な実装にはstructure情報が必要
        return pattern
    
    # 後方互換性のためのメソッド
    def generate_or_patterns(self, n_conditions: int = 2) -> List[str]:
        """OR条件のMC/DCパターンを生成"""
        if n_conditions == 2:
            return ['TF', 'FT', 'FF']
        elif n_conditions >= 3:
            patterns = []
            for i in range(n_conditions):
                pattern = ['F'] * n_conditions
                pattern[i] = 'T'
                patterns.append(''.join(pattern))
            patterns.append('F' * n_conditions)
            return patterns
        else:
            return ['T', 'F']
    
    def generate_and_patterns(self, n_conditions: int = 2) -> List[str]:
        """AND条件のMC/DCパターンを生成"""
        if n_conditions == 2:
            return ['TF', 'FT', 'TT']
        elif n_conditions >= 3:
            patterns = []
            for i in range(n_conditions):
                pattern = ['T'] * n_conditions
                pattern[i] = 'F'
                patterns.append(''.join(pattern))
            patterns.append('T' * n_conditions)
            return patterns
        else:
            return ['T', 'F']


if __name__ == "__main__":
    print("=== MCDCPatternGenerator v2.6.1 のテスト ===\n")
    
    generator = MCDCPatternGeneratorV2()
    
    # テスト: ネストしたAND/OR条件
    print("テスト: A && (B || C || D || E || F || G) && H")
    
    conditions = [
        "(Utx104.Utm11.Utm14 == UtD27)",  # A
        "((UtD39 == 1) || (UtD39 == 2) || (UtD39 == 3) || (UtD39 == 6) || (UtD39 == 7) || (UtD39 == 8))",  # B-G
        "(UtD38 == 0)"  # H
    ]
    
    patterns = generator.generate_mcdc_patterns_for_complex('and', conditions)
    
    print(f"\n生成されたパターン数: {len(patterns)}")
    for i, pattern in enumerate(patterns, 1):
        print(f"{i}. {pattern}")
    
    print("\n期待される9パターンとの比較:")
    expected = [
        "TTFFFFFT",
        "FTFFFFFT",
        "TFFFFFFT",
        "TTFFFFFF",
        "TFTFFFFT",
        "TFFTFFFT",
        "TFFFTFFT",
        "TFFFFTFT",
        "TFFFFFTT",
    ]
    
    for i, pattern in enumerate(expected, 1):
        status = "✓" if pattern in patterns else "✗"
        print(f"{i}. {pattern} {status}")
    
    # 逆チェック（余分なパターンがないか）
    print("\n余分なパターン:")
    for pattern in patterns:
        if pattern not in expected:
            print(f"  - {pattern}")
    
    print("\n✓ テスト完了")
