"""
MCDCPatternGenerator v4.0 (AutoUniTestGen v4.6.0)

条件式をツリー構造として解析し、最小MC/DCパターンを生成。
A || B || (C && D) のような複雑な条件に完全対応。

v4.0の変更点:
- Masking MC/DCの考え方を導入してパターン数を最小化
- パターン共有を最大化するアルゴリズム（貪欲法）
- 最小セット選択で n条件 → n+1パターン を達成

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
from itertools import combinations

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
    
    def evaluate_with_list(self, values: List[bool]) -> bool:
        """リスト形式の値で評価"""
        return self.evaluate({i: v for i, v in enumerate(values)})
    
    def __repr__(self):
        if self.is_leaf():
            return f"Leaf({self.text})"
        return f"{self.operator.value.upper()}({', '.join(repr(c) for c in self.children)})"


class MCDCPatternGeneratorV4:
    """MC/DCパターンジェネレータ v4.0 - 最小パターン生成"""
    
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
        最小MC/DCパターンを生成
        
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
        
        # Step 1: 各葉条件の全ての有効な独立性ペア候補を生成
        all_independence_pairs = []
        for leaf_idx in range(n):
            pairs = self._find_all_independence_pairs(root, leaf_idx, n)
            all_independence_pairs.append(pairs)
            self.logger.debug(f"条件{leaf_idx}の独立性ペア候補: {len(pairs)}組")
        
        # Step 2: 貪欲法で最小パターンセットを選択
        selected_patterns = self._select_minimal_patterns_greedy(
            all_independence_pairs, n
        )
        
        # 結果を文字列に変換
        pattern_strings = [''.join('T' if v else 'F' for v in p) 
                          for p in sorted(selected_patterns)]
        leaf_texts = [leaf.text for leaf in leaves]
        
        self.logger.info(f"生成されたパターン数: {len(pattern_strings)}個 (最小化済み)")
        
        return pattern_strings, leaf_texts
    
    def _find_all_independence_pairs(self, 
                                     root: ConditionNode,
                                     target_leaf_idx: int,
                                     total: int) -> List[Tuple[Tuple[bool, ...], Tuple[bool, ...]]]:
        """
        特定の葉条件の全ての有効な独立性ペアを探索
        
        MC/DCの独立性要件:
        - 対象の条件だけが変わる（T→FまたはF→T）
        - 他の全ての条件は固定
        - 全体の結果が変わる
        
        Returns:
            独立性ペアのリスト: [(pattern_true, pattern_false), ...]
            pattern_true: 対象条件=True のパターン
            pattern_false: 対象条件=False のパターン（他は同じ）
        """
        valid_pairs = []
        
        # 全パターンを探索（対象条件=Trueのパターンのみ）
        for i in range(2 ** total):
            pattern = [(i >> j) & 1 == 1 for j in range(total)]
            
            # target_leaf_idx がTrueの場合のみチェック
            if not pattern[target_leaf_idx]:
                continue
            
            # 全体の結果を評価
            result_true = root.evaluate_with_list(pattern)
            
            # target_leaf_idxだけをFalseに変えた時の結果
            # 他の条件は全く同じ
            pattern_false = pattern.copy()
            pattern_false[target_leaf_idx] = False
            result_false = root.evaluate_with_list(pattern_false)
            
            # 結果が変わる場合、有効な独立性ペア
            # （対象条件だけが異なり、結果が変わる）
            if result_true != result_false:
                valid_pairs.append((
                    tuple(pattern),
                    tuple(pattern_false)
                ))
        
        return valid_pairs
    
    def _select_minimal_patterns_greedy(self,
                                        all_independence_pairs: List[List[Tuple[Tuple[bool, ...], Tuple[bool, ...]]]],
                                        n: int) -> Set[Tuple[bool, ...]]:
        """
        貪欲法で最小パターンセットを選択
        
        各条件の独立性を示すペアを選択しつつ、パターンの共有を最大化
        
        選択基準（優先順位）:
        1. 新規パターン数が最小
        2. 既存パターンを多く再利用するペア
        """
        # 選択されたパターンの集合
        selected_patterns: Set[Tuple[bool, ...]] = set()
        
        # 条件の優先順位を決定（ペア候補が少ない順）
        condition_order = sorted(
            range(n),
            key=lambda i: len(all_independence_pairs[i])
        )
        
        for cond_idx in condition_order:
            pairs = all_independence_pairs[cond_idx]
            
            if not pairs:
                self.logger.warning(f"条件{cond_idx}に有効な独立性ペアがありません")
                continue
            
            # 既存パターンとの共有を最大化するペアを選択
            best_pair_idx = -1
            best_new_count = float('inf')
            best_reuse_count = -1  # 再利用数（多いほど良い）
            
            for pair_idx, (pat_true, pat_false) in enumerate(pairs):
                # 新しく追加が必要なパターン数をカウント
                new_count = 0
                reuse_count = 0  # 既存パターンの再利用数
                
                if pat_true not in selected_patterns:
                    new_count += 1
                else:
                    reuse_count += 1
                
                if pat_false not in selected_patterns:
                    new_count += 1
                else:
                    reuse_count += 1
                
                # 選択基準: 新規パターン数が少ない > 再利用数が多い
                if (new_count < best_new_count or 
                    (new_count == best_new_count and reuse_count > best_reuse_count)):
                    best_new_count = new_count
                    best_reuse_count = reuse_count
                    best_pair_idx = pair_idx
            
            # 最良のペアを選択
            if best_pair_idx >= 0:
                pat_true, pat_false = pairs[best_pair_idx]
                selected_patterns.add(pat_true)
                selected_patterns.add(pat_false)
        
        return selected_patterns
    
    # ===== 後方互換性のためのメソッド =====
    
    def generate_mcdc_patterns_for_complex(self,
                                          top_operator: str,
                                          conditions: List[str]) -> List[str]:
        """
        複雑な条件のMC/DCパターンを生成（後方互換）
        """
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


class MCDCPatternGeneratorV3:
    """MC/DCパターンジェネレータ v3.0 - ツリー構造ベース（後方互換）"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        # V4にデリゲート
        self._v4 = MCDCPatternGeneratorV4()
    
    def parse_condition(self, condition_text: str) -> ConditionNode:
        return self._v4.parse_condition(condition_text)
    
    def generate_mcdc_patterns(self, condition_text: str) -> Tuple[List[str], List[str]]:
        return self._v4.generate_mcdc_patterns(condition_text)
    
    def generate_mcdc_patterns_for_complex(self,
                                          top_operator: str,
                                          conditions: List[str]) -> List[str]:
        return self._v4.generate_mcdc_patterns_for_complex(top_operator, conditions)
    
    def generate_or_patterns(self, n_conditions: int = 2) -> List[str]:
        return self._v4.generate_or_patterns(n_conditions)
    
    def generate_and_patterns(self, n_conditions: int = 2) -> List[str]:
        return self._v4.generate_and_patterns(n_conditions)


# エイリアス（後方互換）
MCDCPatternGenerator = MCDCPatternGeneratorV4


if __name__ == "__main__":
    print("=== MCDCPatternGenerator v4.0 のテスト ===\n")
    
    gen = MCDCPatternGeneratorV4()
    
    def verify_mcdc(expr: str, patterns: List[str]) -> Tuple[bool, List[str]]:
        """MC/DC達成を検証し、各条件の独立性ペアを返す"""
        root = gen.parse_condition(expr)
        leaves = root.get_all_leaves()
        n = len(leaves)
        
        # パターンをタプルに変換
        pattern_tuples = set()
        for p in patterns:
            pattern_tuples.add(tuple(c == 'T' for c in p))
        
        # 各条件の独立性が示されているか確認
        independence_info = []
        all_found = True
        for target_idx in range(n):
            found = False
            found_pair = None
            for pat1 in pattern_tuples:
                for pat2 in pattern_tuples:
                    # 対象条件だけが異なるかチェック
                    differs_only_target = True
                    target_differs = False
                    for i in range(n):
                        if i == target_idx:
                            if pat1[i] != pat2[i]:
                                target_differs = True
                        else:
                            if pat1[i] != pat2[i]:
                                differs_only_target = False
                                break
                    
                    if differs_only_target and target_differs:
                        # 結果が変わるかチェック
                        r1 = root.evaluate_with_list(list(pat1))
                        r2 = root.evaluate_with_list(list(pat2))
                        if r1 != r2:
                            found = True
                            p1_str = ''.join('T' if v else 'F' for v in pat1)
                            p2_str = ''.join('T' if v else 'F' for v in pat2)
                            found_pair = f"{p1_str} ↔ {p2_str}"
                            break
                if found:
                    break
            
            if found:
                independence_info.append(f"  条件{target_idx} ({leaves[target_idx].text}): {found_pair} ✓")
            else:
                independence_info.append(f"  条件{target_idx} ({leaves[target_idx].text}): 独立性なし ✗")
                all_found = False
        
        return all_found, independence_info
    
    # テスト1: a || (b && c) - 引継ぎ資料の主要テスト
    print("テスト1: a || (b && c)")
    print("-" * 50)
    
    test_expr = "a || (b && c)"
    patterns, leaves = gen.generate_mcdc_patterns(test_expr)
    
    print(f"葉条件: {leaves}")
    print(f"パターン数: {len(patterns)} (期待: 4)")
    for i, p in enumerate(patterns, 1):
        print(f"  {i}. {p}")
    
    mcdc_ok, info = verify_mcdc(test_expr, patterns)
    print("\n独立性ペア:")
    for line in info:
        print(line)
    match1 = len(patterns) == 4 and mcdc_ok
    print(f"\nMC/DC達成: {'✓' if match1 else '✗'}")
    
    # テスト2: a && b
    print("\n" + "=" * 50)
    print("テスト2: a && b")
    print("-" * 50)
    
    patterns2, _ = gen.generate_mcdc_patterns("a && b")
    expected2 = ['FT', 'TF', 'TT']
    print(f"パターン: {patterns2}")
    print(f"期待: {expected2}")
    match2 = set(patterns2) == set(expected2)
    print(f"一致: {'✓' if match2 else '✗'}")
    
    # テスト3: a || b
    print("\n" + "=" * 50)
    print("テスト3: a || b")
    print("-" * 50)
    
    patterns3, _ = gen.generate_mcdc_patterns("a || b")
    expected3 = ['FF', 'FT', 'TF']
    print(f"パターン: {patterns3}")
    print(f"期待: {expected3}")
    match3 = set(patterns3) == set(expected3)
    print(f"一致: {'✓' if match3 else '✗'}")
    
    # テスト4: (a && b) || c
    print("\n" + "=" * 50)
    print("テスト4: (a && b) || c")
    print("-" * 50)
    
    test_expr4 = "(a && b) || c"
    patterns4, _ = gen.generate_mcdc_patterns(test_expr4)
    print(f"パターン数: {len(patterns4)} (期待: 4)")
    print(f"パターン: {patterns4}")
    mcdc_ok4, info4 = verify_mcdc(test_expr4, patterns4)
    print("\n独立性ペア:")
    for line in info4:
        print(line)
    match4 = len(patterns4) == 4 and mcdc_ok4
    print(f"\nMC/DC達成: {'✓' if match4 else '✗'}")
    
    # テスト5: a || b || c
    print("\n" + "=" * 50)
    print("テスト5: a || b || c")
    print("-" * 50)
    
    patterns5, _ = gen.generate_mcdc_patterns("a || b || c")
    expected5 = ['FFF', 'FFT', 'FTF', 'TFF']
    print(f"パターン: {patterns5}")
    print(f"期待: {expected5}")
    match5 = set(patterns5) == set(expected5)
    print(f"一致: {'✓' if match5 else '✗'}")
    
    # テスト6: a && b && c
    print("\n" + "=" * 50)
    print("テスト6: a && b && c")
    print("-" * 50)
    
    patterns6, _ = gen.generate_mcdc_patterns("a && b && c")
    expected6 = ['FTT', 'TFT', 'TTF', 'TTT']
    print(f"パターン: {patterns6}")
    print(f"期待: {expected6}")
    match6 = set(patterns6) == set(expected6)
    print(f"一致: {'✓' if match6 else '✗'}")
    
    # テスト7: a || (b && (c || d)) - 4条件テスト
    print("\n" + "=" * 50)
    print("テスト7: a || (b && (c || d))")
    print("-" * 50)
    
    test_expr7 = "a || (b && (c || d))"
    patterns7, leaves7 = gen.generate_mcdc_patterns(test_expr7)
    print(f"葉条件: {leaves7}")
    print(f"パターン数: {len(patterns7)} (期待: 5)")
    for i, p in enumerate(patterns7, 1):
        print(f"  {i}. {p}")
    
    mcdc_ok7, info7 = verify_mcdc(test_expr7, patterns7)
    print("\n独立性ペア:")
    for line in info7:
        print(line)
    match7 = len(patterns7) == 5 and mcdc_ok7
    print(f"\nMC/DC達成: {'✓' if match7 else '✗'}")
    
    # テスト8: A || B || (C && D) - 実際の難読化コードで使われる形式
    print("\n" + "=" * 50)
    print("テスト8: A || B || (C && D)")
    print("-" * 50)
    
    test_expr8 = "(A == 0) || (B == 3) || ((C == 1) && (D != 0))"
    patterns8, leaves8 = gen.generate_mcdc_patterns(test_expr8)
    
    print(f"葉条件: {leaves8}")
    print(f"パターン数: {len(patterns8)} (期待: 5)")
    for i, p in enumerate(patterns8, 1):
        print(f"  {i}. {p}")
    
    mcdc_ok8, info8 = verify_mcdc(test_expr8, patterns8)
    print("\n独立性ペア:")
    for line in info8:
        print(line)
    match8 = len(patterns8) == 5 and mcdc_ok8
    print(f"\nMC/DC達成: {'✓' if match8 else '✗'}")
    
    # 総合結果
    print("\n" + "=" * 50)
    print("総合結果")
    print("-" * 50)
    all_pass = all([match1, match2, match3, match4, match5, match6, match7, match8])
    print(f"テスト1 (a || (b && c)): {'✓' if match1 else '✗'}")
    print(f"テスト2 (a && b): {'✓' if match2 else '✗'}")
    print(f"テスト3 (a || b): {'✓' if match3 else '✗'}")
    print(f"テスト4 ((a && b) || c): {'✓' if match4 else '✗'}")
    print(f"テスト5 (a || b || c): {'✓' if match5 else '✗'}")
    print(f"テスト6 (a && b && c): {'✓' if match6 else '✗'}")
    print(f"テスト7 (a || (b && (c || d))): {'✓' if match7 else '✗'}")
    print(f"テスト8 (A || B || (C && D)): {'✓' if match8 else '✗'}")
    print(f"\n全テスト: {'✓ PASS' if all_pass else '✗ FAIL'}")
