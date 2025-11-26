"""
MCDCPatternGenerator v3.0

条件式をツリー構造として解析し、正確なMC/DCパターンを生成。
A || B || (C && D) のような複雑な条件に完全対応。

MC/DC (Modified Condition/Decision Coverage) の原則:
- 各条件は、他の条件を固定した状態で、結果に独立して影響を与えることを示す
- OR条件: その条件がTrueになると全体がTrueになる → 他は全てFalseの状態でそれぞれをTrueに
- AND条件: その条件がFalseになると全体がFalseになる → 他は全てTrueの状態でそれぞれをFalseに
"""

import sys
import os
import re
from typing import List, Dict, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class OperatorType(Enum):
    """演算子の種類"""
    AND = 'and'
    OR = 'or'
    LEAF = 'leaf'  # 葉ノード（単純条件）


@dataclass
class ConditionNode:
    """条件式のツリーノード"""
    operator: OperatorType
    text: str  # 元の条件テキスト
    children: List['ConditionNode'] = field(default_factory=list)
    
    def is_leaf(self) -> bool:
        return self.operator == OperatorType.LEAF
    
    def get_all_leaves(self) -> List['ConditionNode']:
        """全ての葉ノードを順序付きで取得"""
        if self.is_leaf():
            return [self]
        leaves = []
        for child in self.children:
            leaves.extend(child.get_all_leaves())
        return leaves
    
    def evaluate(self, values: Dict[int, bool], leaf_index: List[int] = None) -> bool:
        """
        与えられた値でこの条件を評価
        
        Args:
            values: 葉ノードのインデックス -> 真偽値のマッピング
            leaf_index: 現在の葉インデックス（内部使用）
        """
        if leaf_index is None:
            leaf_index = [0]
        
        if self.is_leaf():
            idx = leaf_index[0]
            leaf_index[0] += 1
            return values.get(idx, False)
        
        if self.operator == OperatorType.OR:
            for child in self.children:
                if child.evaluate(values, leaf_index):
                    return True
            return False
        
        elif self.operator == OperatorType.AND:
            for child in self.children:
                if not child.evaluate(values, leaf_index):
                    return False
            return True
        
        return False
    
    def __repr__(self):
        if self.is_leaf():
            return f"Leaf({self.text})"
        return f"{self.operator.value.upper()}({', '.join(repr(c) for c in self.children)})"


class MCDCPatternGeneratorV3:
    """MC/DCパターンジェネレータ v3.0 - ツリー構造ベース"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    def parse_condition(self, condition_text: str) -> ConditionNode:
        """
        条件式をツリー構造にパース
        
        Args:
            condition_text: 条件式のテキスト
            
        Returns:
            ConditionNode: ルートノード
        """
        text = condition_text.strip()
        text = self._remove_outer_parens(text)
        
        # トップレベルのOR分割を試みる
        or_parts = self._split_by_operator(text, '||')
        if len(or_parts) > 1:
            children = [self.parse_condition(part) for part in or_parts]
            return ConditionNode(OperatorType.OR, text, children)
        
        # トップレベルのAND分割を試みる
        and_parts = self._split_by_operator(text, '&&')
        if len(and_parts) > 1:
            children = [self.parse_condition(part) for part in and_parts]
            return ConditionNode(OperatorType.AND, text, children)
        
        # 葉ノード
        return ConditionNode(OperatorType.LEAF, text)
    
    def _split_by_operator(self, text: str, operator: str) -> List[str]:
        """
        括弧の深さを考慮して演算子で分割
        """
        parts = []
        current = ""
        depth = 0
        i = 0
        
        while i < len(text):
            if text[i] == '(':
                depth += 1
                current += text[i]
            elif text[i] == ')':
                depth -= 1
                current += text[i]
            elif depth == 0 and text[i:i+len(operator)] == operator:
                if current.strip():
                    parts.append(current.strip())
                current = ""
                i += len(operator) - 1
            else:
                current += text[i]
            i += 1
        
        if current.strip():
            parts.append(current.strip())
        
        # 各パーツの外側の括弧を削除
        return [self._remove_outer_parens(p) for p in parts]
    
    def _remove_outer_parens(self, text: str) -> str:
        """外側の括弧を削除（対応が取れている場合のみ）"""
        text = text.strip()
        while text.startswith('(') and text.endswith(')'):
            depth = 0
            valid = True
            for i, char in enumerate(text[1:-1], 1):
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth < 0:
                        valid = False
                        break
            if valid and depth == 0:
                text = text[1:-1].strip()
            else:
                break
        return text
    
    def generate_mcdc_patterns(self, condition_text: str) -> Tuple[List[str], List[str]]:
        """
        MC/DCパターンを生成
        
        Args:
            condition_text: 条件式のテキスト
            
        Returns:
            (patterns, leaf_texts): パターンのリストと葉条件のテキストリスト
        """
        root = self.parse_condition(condition_text)
        leaves = root.get_all_leaves()
        n = len(leaves)
        
        self.logger.info(f"条件式をパース: {n}個の葉条件を検出")
        self.logger.debug(f"ツリー構造: {root}")
        
        patterns_set: Set[Tuple[bool, ...]] = set()
        
        # 各葉条件について、その独立性を示すパターンペアを生成
        for leaf_idx in range(n):
            pair = self._generate_independence_pair(root, leaf_idx, n)
            for p in pair:
                patterns_set.add(tuple(p))
        
        # 結果を文字列に変換
        patterns = sorted(list(patterns_set))
        pattern_strings = [''.join('T' if v else 'F' for v in p) for p in patterns]
        leaf_texts = [leaf.text for leaf in leaves]
        
        self.logger.info(f"生成されたパターン数: {len(pattern_strings)}個")
        
        return pattern_strings, leaf_texts
    
    def _generate_independence_pair(self, 
                                    root: ConditionNode, 
                                    target_leaf_idx: int,
                                    total: int) -> List[List[bool]]:
        """
        特定の葉条件の独立性を示すパターンペアを生成
        
        MC/DCでは、各葉条件について：
        - その条件を True にした時と False にした時で
        - 全体の結果が変わる
        - 他の条件は「その条件の影響を判定可能な状態」に固定
        
        重要: AND条件内の葉の場合、他の葉をTrueにした状態で
              自分だけを T/F に変えて結果が変わることを示す
        
        Args:
            root: ルートノード
            target_leaf_idx: 対象の葉インデックス
            total: 総葉数
            
        Returns:
            [pattern_true, pattern_false] のリスト
        """
        # 対象の葉がTrueの時のパターンを生成
        pattern_true = [False] * total
        self._set_pattern_for_true_result(root, target_leaf_idx, pattern_true, 0)
        
        # 対象の葉がFalseの時のパターンを生成
        # ただし、AND条件内の葉の場合は特別な処理が必要
        pattern_false = [False] * total
        self._set_pattern_for_false_result_v2(root, target_leaf_idx, pattern_false, 0)
        
        return [pattern_true, pattern_false]
    
    def _set_pattern_for_false_result_v2(self,
                                         node: ConditionNode,
                                         target_leaf_idx: int,
                                         pattern: List[bool],
                                         current_idx: int) -> Tuple[int, bool]:
        """
        対象の葉=Falseで全体がFalseになるパターンを設定（v2）
        
        重要な変更点：
        - AND条件内の葉の場合、兄弟をTrueにする
        - これにより、対象の葉だけがFalseで結果に影響することを示せる
        """
        if node.is_leaf():
            is_target = (current_idx == target_leaf_idx)
            # 対象はFalse（デフォルト）
            return current_idx + 1, is_target
        
        # まず子を走査して、どの子が対象を含むかを調べる
        idx = current_idx
        target_child = -1
        child_ranges = []
        
        for i, child in enumerate(node.children):
            child_start = idx
            child_leaves = len(child.get_all_leaves())
            child_end = idx + child_leaves
            
            # この子が対象を含むかチェック
            has_target = (target_leaf_idx >= child_start and target_leaf_idx < child_end)
            child_ranges.append((child_start, child_end, has_target))
            if has_target:
                target_child = i
            idx = child_end
        
        if node.operator == OperatorType.OR:
            # OR: 全ての子がFalseである必要あり
            # ただし、対象を含む子がANDの場合は、AND内の他の葉をTrueに
            if target_child >= 0:
                child = node.children[target_child]
                start, _, _ = child_ranges[target_child]
                if child.operator == OperatorType.AND:
                    # AND内の対象以外をTrueに設定
                    self._ensure_subtree_true_except_target(
                        child, target_leaf_idx, pattern, start
                    )
        
        elif node.operator == OperatorType.AND:
            # AND: 対象を含む子だけFalseになれば全体がFalse
            # 他の子はTrueに設定
            for i, (start, end, has_target) in enumerate(child_ranges):
                if not has_target:
                    self._set_subtree_true(node.children[i], pattern, start)
                else:
                    # 対象を含む子：AND内なら他の葉をTrueに
                    child = node.children[i]
                    if child.operator == OperatorType.AND:
                        self._ensure_subtree_true_except_target(
                            child, target_leaf_idx, pattern, start
                        )
        
        return idx, (target_child >= 0)
    
    def _set_pattern_for_true_result(self,
                                     node: ConditionNode,
                                     target_leaf_idx: int,
                                     pattern: List[bool],
                                     current_idx: int) -> Tuple[int, bool]:
        """
        対象の葉=Trueで全体がTrueになるパターンを設定
        
        OR条件: 対象を含む子だけTrueになればOK、他はFalse
        AND条件: 全ての子がTrueである必要あり
        """
        if node.is_leaf():
            is_target = (current_idx == target_leaf_idx)
            if is_target:
                pattern[current_idx] = True  # 対象はTrue
            return current_idx + 1, is_target
        
        # まず子を走査して、どの子が対象を含むかを調べる
        idx = current_idx
        target_child = -1
        child_ranges = []
        
        for i, child in enumerate(node.children):
            child_start = idx
            child_leaves = len(child.get_all_leaves())
            child_end = idx + child_leaves
            
            # この子が対象を含むかチェック
            has_target = (target_leaf_idx >= child_start and target_leaf_idx < child_end)
            child_ranges.append((child_start, child_end, has_target))
            if has_target:
                target_child = i
            idx = child_end
        
        if node.operator == OperatorType.OR:
            # OR: 対象を含む子だけがTrueになればOK
            # 他の子はFalse（デフォルト）のまま
            if target_child >= 0:
                child = node.children[target_child]
                start, end, _ = child_ranges[target_child]
                
                # 対象の葉をTrueに設定
                pattern[target_leaf_idx] = True
                
                # 対象を含む子がANDなら、対象以外もTrueにする必要あり
                if child.operator == OperatorType.AND:
                    self._ensure_subtree_true_except_target(
                        child, target_leaf_idx, pattern, start
                    )
        
        elif node.operator == OperatorType.AND:
            # AND: 全ての子がTrueである必要あり
            # 対象を含まない子は全てTrueに設定
            for i, (start, end, has_target) in enumerate(child_ranges):
                if not has_target:
                    self._set_subtree_true(node.children[i], pattern, start)
                else:
                    # 対象を含む子：対象はTrue、ANDなら他もTrue
                    pattern[target_leaf_idx] = True
                    child = node.children[i]
                    if child.operator == OperatorType.AND:
                        self._ensure_subtree_true_except_target(
                            child, target_leaf_idx, pattern, start
                        )
                    elif child.operator == OperatorType.OR:
                        # ORの中の対象：他はFalseでOK
                        pass
        
        return idx, (target_child >= 0)
    
    def _set_pattern_for_false_result(self,
                                      node: ConditionNode,
                                      target_leaf_idx: int,
                                      pattern: List[bool],
                                      current_idx: int) -> Tuple[int, bool]:
        """
        対象の葉=Falseで全体がFalseになるパターンを設定
        
        OR条件: 全ての子がFalseである必要あり → 全てFalse
        AND条件: 1つでもFalseなら全体がFalse → 対象だけFalse、他はTrue
        """
        if node.is_leaf():
            is_target = (current_idx == target_leaf_idx)
            # 対象ならFalse（デフォルト）
            return current_idx + 1, is_target
        
        # まず子を走査して、どの子が対象を含むかを調べる
        idx = current_idx
        target_child = -1
        child_ranges = []
        
        for i, child in enumerate(node.children):
            child_start = idx
            child_leaves = len(child.get_all_leaves())
            child_end = idx + child_leaves
            
            # この子が対象を含むかチェック
            has_target = (target_leaf_idx >= child_start and target_leaf_idx < child_end)
            child_ranges.append((child_start, child_end, has_target))
            if has_target:
                target_child = i
            idx = child_end
        
        if node.operator == OperatorType.OR:
            # OR: 全ての子がFalseである必要あり
            # 全てFalseのまま（デフォルト）
            pass
        
        elif node.operator == OperatorType.AND:
            # AND: 対象を含む子だけFalseになれば全体がFalse
            # 他の子はTrueに設定
            for i, (start, end, has_target) in enumerate(child_ranges):
                if not has_target:
                    self._set_subtree_true(node.children[i], pattern, start)
        
        return idx, (target_child >= 0)
    
    def _ensure_subtree_true_except_target(self,
                                           node: ConditionNode,
                                           target_leaf_idx: int,
                                           pattern: List[bool],
                                           current_idx: int) -> int:
        """
        対象の葉以外をTrueに設定（ANDの内部で使用）
        """
        if node.is_leaf():
            if current_idx != target_leaf_idx:
                pattern[current_idx] = True
            return current_idx + 1
        
        idx = current_idx
        for child in node.children:
            idx = self._ensure_subtree_true_except_target(
                child, target_leaf_idx, pattern, idx
            )
        return idx
    
    def _set_context_for_leaf(self,
                              node: ConditionNode,
                              target_leaf_idx: int,
                              pattern: List[bool],
                              current_leaf_idx: int,
                              target_value: bool) -> Tuple[int, bool]:
        """後方互換のため残す（未使用）"""
        return current_leaf_idx, False
    
    def _set_subtree_true(self, 
                          node: ConditionNode, 
                          pattern: List[bool], 
                          start_idx: int) -> int:
        """
        サブツリー全体をTrue（評価がTrueになる最小限の設定）に
        
        OR: 1つだけTrueで十分
        AND: 全てTrue
        葉: True
        """
        if node.is_leaf():
            pattern[start_idx] = True
            return start_idx + 1
        
        idx = start_idx
        if node.operator == OperatorType.OR:
            # 最初の1つだけTrue
            for i, child in enumerate(node.children):
                if i == 0:
                    idx = self._set_subtree_true(child, pattern, idx)
                else:
                    idx += len(child.get_all_leaves())
        
        elif node.operator == OperatorType.AND:
            # 全てTrue
            for child in node.children:
                idx = self._set_subtree_true(child, pattern, idx)
        
        return idx
    
    def _generate_patterns_recursive(self, 
                                     node: ConditionNode, 
                                     start_idx: int, 
                                     total: int,
                                     patterns: Set[Tuple[bool, ...]]) -> int:
        """後方互換のため残す（未使用）"""
        return 0
    
    def _generate_or_patterns(self,
                             node: ConditionNode,
                             start_idx: int,
                             total: int,
                             child_ranges: List[Tuple[int, int]],
                             patterns: Set[Tuple[bool, ...]]) -> None:
        """
        OR条件のMC/DCパターンを生成
        
        OR条件では:
        - 全てFalseのベースケース
        - 各子条件を1つずつTrueにして全体をTrueにする（他はFalse）
        """
        n_children = len(node.children)
        
        # パターン1: 全ての子条件がFalse → 全体False
        base_false = [False] * total
        patterns.add(tuple(base_false))
        
        # パターン2-N: 各子条件を1つだけTrueにする
        for i, child in enumerate(node.children):
            pattern = [False] * total
            child_start, child_end = child_ranges[i]
            
            # この子条件をTrueにする
            self._set_child_true(pattern, child, child_start)
            
            patterns.add(tuple(pattern))
    
    def _generate_and_patterns(self,
                               node: ConditionNode,
                               start_idx: int,
                               total: int,
                               child_ranges: List[Tuple[int, int]],
                               patterns: Set[Tuple[bool, ...]]) -> None:
        """
        AND条件のMC/DCパターンを生成
        
        AND条件では:
        - 全てTrueのベースケース
        - 各子条件を1つずつFalseにして全体をFalseにする（他はTrue）
        
        注意: このノードの範囲外の値は、親の文脈によって決まる
        （親から呼ばれた時点で、このノード範囲外は適切に設定済み）
        """
        # このノードの範囲を取得
        node_start = start_idx
        node_end = child_ranges[-1][1] if child_ranges else start_idx
        
        # パターン1: 全ての子条件がTrue → 全体True
        # このノード範囲内のみTrueに設定
        base_true = [False] * total
        for child_start, child_end in child_ranges:
            for i in range(child_start, child_end):
                base_true[i] = True
        patterns.add(tuple(base_true))
        
        # パターン2-N: 各子条件を1つだけFalseにする
        for i, child in enumerate(node.children):
            pattern = [False] * total
            # まず全ての子をTrueに設定
            for j, (cs, ce) in enumerate(child_ranges):
                for idx in range(cs, ce):
                    pattern[idx] = True
            
            child_start, child_end = child_ranges[i]
            
            # この子条件をFalseにする
            self._set_child_false(pattern, child, child_start)
            
            patterns.add(tuple(pattern))
    
    def _create_all_true_pattern(self, node: ConditionNode, total: int, start_idx: int) -> List[bool]:
        """全ての葉がTrueになるパターンを作成"""
        pattern = [False] * total
        leaves = node.get_all_leaves()
        for i in range(len(leaves)):
            pattern[start_idx + i] = True
        return pattern
    
    def _set_child_true(self, pattern: List[bool], child: ConditionNode, start_idx: int) -> None:
        """
        子条件をTrueになるように設定
        - 葉: そのインデックスをTrue
        - AND: 全てTrue
        - OR: 最初の1つをTrue
        """
        if child.is_leaf():
            pattern[start_idx] = True
        elif child.operator == OperatorType.AND:
            # ANDは全てTrueが必要
            for i, leaf in enumerate(child.get_all_leaves()):
                pattern[start_idx + i] = True
        elif child.operator == OperatorType.OR:
            # ORは1つTrueで十分
            # 最初の葉をTrueにする
            pattern[start_idx] = True
    
    def _set_child_false(self, pattern: List[bool], child: ConditionNode, start_idx: int) -> None:
        """
        子条件をFalseになるように設定
        - 葉: そのインデックスをFalse
        - AND: 1つFalseで十分
        - OR: 全てFalse
        """
        if child.is_leaf():
            pattern[start_idx] = False
        elif child.operator == OperatorType.AND:
            # ANDは1つFalseで十分
            pattern[start_idx] = False
        elif child.operator == OperatorType.OR:
            # ORは全てFalseが必要
            for i, leaf in enumerate(child.get_all_leaves()):
                pattern[start_idx + i] = False
    
    # 後方互換性のためのメソッド
    def generate_mcdc_patterns_for_complex(self,
                                          top_operator: str,
                                          conditions: List[str]) -> List[str]:
        """
        複雑な条件のMC/DCパターンを生成（後方互換）
        
        Args:
            top_operator: 'and' or 'or'
            conditions: 条件のリスト
            
        Returns:
            パターンのリスト
        """
        # 条件を結合して1つの式にする
        op_str = ' || ' if top_operator == 'or' else ' && '
        combined = op_str.join(f'({c})' for c in conditions)
        
        patterns, _ = self.generate_mcdc_patterns(combined)
        return patterns
    
    def generate_or_patterns(self, n_conditions: int = 2) -> List[str]:
        """OR条件のMC/DCパターン（後方互換）"""
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
        """AND条件のMC/DCパターン（後方互換）"""
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


# エイリアス（後方互換）
MCDCPatternGenerator = MCDCPatternGeneratorV3


if __name__ == "__main__":
    print("=== MCDCPatternGenerator v3.0 のテスト ===\n")
    
    gen = MCDCPatternGeneratorV3()
    
    # テスト1: A || B || (C && D)
    print("テスト1: A || B || (C && D)")
    print("-" * 50)
    
    test_expr = "(A == 0) || (B == 3) || ((C == 1) && (D != 0))"
    patterns, leaves = gen.generate_mcdc_patterns(test_expr)
    
    print(f"葉条件: {leaves}")
    print(f"パターン数: {len(patterns)}")
    for i, p in enumerate(patterns, 1):
        print(f"  {i}. {p}")
    
    print("\n期待されるパターン (MC/DC完全版):")
    expected = [
        "FFFF",  # 全False → 結果False (基準)
        "TFFF",  # A=T → 結果True (Aの独立性)
        "FTFF",  # B=T → 結果True (Bの独立性)
        "FFTF",  # C=T, D=F → 結果False (Cの独立性 - FFTTと比較)
        "FFFT",  # C=F, D=T → 結果False (Dの独立性 - FFTTと比較)
        "FFTT",  # C=T, D=T → 結果True (C&&D = True)
    ]
    print(f"  {expected}")
    
    # 検証
    print("\n検証:")
    for exp in expected:
        status = "✓" if exp in patterns else "✗"
        print(f"  {exp}: {status}")
    
    # 余分なパターン
    extra = [p for p in patterns if p not in expected]
    if extra:
        print(f"\n余分なパターン: {extra}")
    
    # テスト2: (A && B) || C
    print("\n" + "=" * 50)
    print("テスト2: (A && B) || C")
    print("-" * 50)
    
    test_expr2 = "((A == 1) && (B == 2)) || (C == 3)"
    patterns2, leaves2 = gen.generate_mcdc_patterns(test_expr2)
    
    print(f"葉条件: {leaves2}")
    print(f"パターン数: {len(patterns2)}")
    for i, p in enumerate(patterns2, 1):
        print(f"  {i}. {p}")
    
    # テスト3: A && (B || C || D || E || F || G) && H
    print("\n" + "=" * 50)
    print("テスト3: A && (B || C || D || E || F || G) && H")
    print("-" * 50)
    
    test_expr3 = "(A == 1) && ((B == 1) || (C == 2) || (D == 3) || (E == 4) || (F == 5) || (G == 6)) && (H == 0)"
    patterns3, leaves3 = gen.generate_mcdc_patterns(test_expr3)
    
    print(f"葉条件: {len(leaves3)}個")
    print(f"パターン数: {len(patterns3)}")
    for i, p in enumerate(patterns3, 1):
        print(f"  {i}. {p}")
    
    print("\n✓ テスト完了")
