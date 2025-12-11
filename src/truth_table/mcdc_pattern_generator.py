"""
MCDCPatternGenerator v4.7.3 - 階層分解アルゴリズム (シンプル版)

複合条件を解析し、構造情報を活用して最小MC/DCパターンを生成する。
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
    AND = 'and'
    OR = 'or'
    LEAF = 'leaf'


@dataclass
class ConditionNode:
    operator: OperatorType
    text: str
    children: List['ConditionNode'] = field(default_factory=list)
    
    def is_leaf(self) -> bool:
        return self.operator == OperatorType.LEAF
    
    def get_all_leaves(self) -> List['ConditionNode']:
        if self.is_leaf():
            return [self]
        leaves = []
        for child in self.children:
            leaves.extend(child.get_all_leaves())
        return leaves
    
    def count_leaves(self) -> int:
        return len(self.get_all_leaves())
    
    def evaluate(self, values: Dict[int, bool], leaf_index: List[int] = None) -> bool:
        """短絡評価なしで評価"""
        if leaf_index is None:
            leaf_index = [0]
        
        if self.is_leaf():
            idx = leaf_index[0]
            leaf_index[0] += 1
            return values.get(idx, False)
        
        if self.operator == OperatorType.OR:
            results = [child.evaluate(values, leaf_index) for child in self.children]
            return any(results)
        elif self.operator == OperatorType.AND:
            results = [child.evaluate(values, leaf_index) for child in self.children]
            return all(results)
        return False
    
    def evaluate_with_list(self, values: List[bool]) -> bool:
        return self.evaluate({i: v for i, v in enumerate(values)})
    
    def __repr__(self):
        if self.is_leaf():
            return f"Leaf({self.text})"
        return f"{self.operator.value.upper()}({', '.join(repr(c) for c in self.children)})"


class MCDCPatternGeneratorV4:
    """MC/DCパターンジェネレータ v4.7.3"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    def parse_condition(self, condition_text: str) -> ConditionNode:
        text = condition_text.strip()
        text = self._remove_outer_parens(text)
        
        or_parts = self._split_by_operator(text, '||')
        if len(or_parts) > 1:
            children = [self.parse_condition(part) for part in or_parts]
            return ConditionNode(OperatorType.OR, text, children)
        
        and_parts = self._split_by_operator(text, '&&')
        if len(and_parts) > 1:
            children = [self.parse_condition(part) for part in and_parts]
            return ConditionNode(OperatorType.AND, text, children)
        
        return ConditionNode(OperatorType.LEAF, text)
    
    def _split_by_operator(self, text: str, operator: str) -> List[str]:
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
        
        return [self._remove_outer_parens(p) for p in parts]
    
    def _remove_outer_parens(self, text: str) -> str:
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
        root = self.parse_condition(condition_text)
        leaves = root.get_all_leaves()
        n = len(leaves)
        
        self.logger.info(f"条件式をパース: {n}個の葉条件を検出")
        
        # 各条件の独立性ペア候補を全探索で生成
        all_pairs = []
        for target_idx in range(n):
            pairs = self._find_independence_pairs(root, target_idx, n)
            all_pairs.append(pairs)
        
        # 貪欲法で最小パターンセットを選択
        selected = self._select_minimal_patterns(all_pairs, n)
        
        pattern_strings = [''.join('T' if v else 'F' for v in p) 
                          for p in sorted(selected)]
        leaf_texts = [leaf.text for leaf in leaves]
        
        self.logger.info(f"生成されたパターン数: {len(pattern_strings)}個 (最小化済み)")
        
        return pattern_strings, leaf_texts
    
    def _find_independence_pairs(self, root: ConditionNode, target_idx: int, n: int) -> List[Tuple[Tuple[bool, ...], Tuple[bool, ...]]]:
        """対象条件の全ての有効な独立性ペアを探索"""
        valid_pairs = []
        
        for i in range(2 ** n):
            pattern = [(i >> j) & 1 == 1 for j in range(n)]
            
            if not pattern[target_idx]:
                continue
            
            result_true = root.evaluate_with_list(pattern)
            
            pattern_false = pattern.copy()
            pattern_false[target_idx] = False
            result_false = root.evaluate_with_list(pattern_false)
            
            if result_true != result_false:
                valid_pairs.append((tuple(pattern), tuple(pattern_false)))
        
        return valid_pairs
    
    def _select_minimal_patterns(self, all_pairs: List[List[Tuple]], n: int) -> Set[Tuple[bool, ...]]:
        """貪欲法で最小パターンセットを選択"""
        selected: Set[Tuple[bool, ...]] = set()
        
        # ペア候補が少ない条件から処理
        order = sorted(range(n), key=lambda i: len(all_pairs[i]))
        
        for cond_idx in order:
            pairs = all_pairs[cond_idx]
            
            if not pairs:
                self.logger.warning(f"条件{cond_idx}に有効な独立性ペアがありません")
                continue
            
            best_pair = None
            best_new_count = float('inf')
            best_reuse_count = -1
            
            for pat_true, pat_false in pairs:
                new_count = 0
                reuse_count = 0
                
                if pat_true not in selected:
                    new_count += 1
                else:
                    reuse_count += 1
                
                if pat_false not in selected:
                    new_count += 1
                else:
                    reuse_count += 1
                
                if (new_count < best_new_count or 
                    (new_count == best_new_count and reuse_count > best_reuse_count)):
                    best_new_count = new_count
                    best_reuse_count = reuse_count
                    best_pair = (pat_true, pat_false)
            
            if best_pair:
                selected.add(best_pair[0])
                selected.add(best_pair[1])
        
        return selected
    
    # 後方互換メソッド
    def generate_mcdc_patterns_for_complex(self, top_operator: str, conditions: List[str]) -> List[str]:
        op_str = ' || ' if top_operator == 'or' else ' && '
        combined = op_str.join(f'({c})' for c in conditions)
        patterns, _ = self.generate_mcdc_patterns(combined)
        return patterns
    
    def generate_or_patterns(self, n_conditions: int = 2) -> List[str]:
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
        return ['T', 'F']
    
    def generate_and_patterns(self, n_conditions: int = 2) -> List[str]:
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
        return ['T', 'F']


class MCDCPatternGeneratorV3:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self._v4 = MCDCPatternGeneratorV4()
    
    def parse_condition(self, condition_text: str) -> ConditionNode:
        return self._v4.parse_condition(condition_text)
    
    def generate_mcdc_patterns(self, condition_text: str) -> Tuple[List[str], List[str]]:
        return self._v4.generate_mcdc_patterns(condition_text)
    
    def generate_mcdc_patterns_for_complex(self, top_operator: str, conditions: List[str]) -> List[str]:
        return self._v4.generate_mcdc_patterns_for_complex(top_operator, conditions)
    
    def generate_or_patterns(self, n_conditions: int = 2) -> List[str]:
        return self._v4.generate_or_patterns(n_conditions)
    
    def generate_and_patterns(self, n_conditions: int = 2) -> List[str]:
        return self._v4.generate_and_patterns(n_conditions)


MCDCPatternGenerator = MCDCPatternGeneratorV4


if __name__ == "__main__":
    print("=== MCDCPatternGenerator v4.7.3 テスト ===\n")
    
    gen = MCDCPatternGeneratorV4()
    
    def verify_mcdc(expr: str, patterns: List[str]) -> Tuple[bool, List[str]]:
        root = gen.parse_condition(expr)
        leaves = root.get_all_leaves()
        n = len(leaves)
        
        pattern_tuples = set(tuple(c == 'T' for c in p) for p in patterns)
        
        info = []
        all_found = True
        for target_idx in range(n):
            found = False
            for pat1 in pattern_tuples:
                for pat2 in pattern_tuples:
                    differs_only_target = all(
                        pat1[i] == pat2[i] if i != target_idx else pat1[i] != pat2[i]
                        for i in range(n)
                    )
                    if differs_only_target:
                        r1 = root.evaluate_with_list(list(pat1))
                        r2 = root.evaluate_with_list(list(pat2))
                        if r1 != r2:
                            found = True
                            p1_str = ''.join('T' if v else 'F' for v in pat1)
                            p2_str = ''.join('T' if v else 'F' for v in pat2)
                            info.append(f"  条件{target_idx} ({leaves[target_idx].text}): {p1_str} <-> {p2_str}")
                            break
                if found:
                    break
            if not found:
                info.append(f"  条件{target_idx} ({leaves[target_idx].text}): 独立性なし")
                all_found = False
        
        return all_found, info
    
    test_cases = [
        ("a || (b && c)", 4),
        ("(A||B)&&C", 4),
        ("a && b", 3),
        ("a || b", 3),
        ("(a && b) || c", 4),
        ("a || b || c", 4),
        ("a && b && c", 4),
        ("a || (b && (c || d))", 5),
    ]
    
    all_pass = True
    
    for expr, expected in test_cases:
        print(f"テスト: {expr}")
        patterns, leaves = gen.generate_mcdc_patterns(expr)
        
        root = gen.parse_condition(expr)
        print(f"  パターン: {patterns}")
        
        t = sum(1 for p in patterns if root.evaluate_with_list([c == 'T' for c in p]))
        f = len(patterns) - t
        print(f"  T/F分布: T={t}, F={f}")
        
        mcdc_ok, info = verify_mcdc(expr, patterns)
        for line in info:
            print(line)
        
        passed = len(patterns) == expected and mcdc_ok
        all_pass = all_pass and passed
        print(f"  結果: {'PASS' if passed else 'FAIL'}\n")
    
    print(f"総合結果: {'PASS' if all_pass else 'FAIL'}")
