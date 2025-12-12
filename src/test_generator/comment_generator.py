"""
CommentGeneratorモジュール

テスト関数のヘッダコメントを生成
"""

import sys
import os
from typing import Dict, List

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import TestCase, ParsedData, ConditionType


class CommentGenerator:
    """コメントジェネレータ"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def generate_comment(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """
        テストケースのヘッダコメントを生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            ヘッダコメント
        """
        lines = []
        
        # コメント開始
        lines.append("/**")
        lines.append(f" * テストケース {test_case.no}: {test_case.condition}")
        lines.append(" *")
        
        # 対象分岐
        lines.append(" * 【対象分岐】")
        lines.append(f" * {test_case.condition}")
        lines.append(" *")
        
        # 真偽パターン
        if test_case.truth and test_case.truth != '-':
            lines.append(f" * 【真偽パターン】")
            lines.append(f" * {test_case.truth}")
            lines.append(" *")
        
        # 期待動作
        lines.append(" * 【期待動作】")
        lines.append(f" * {test_case.expected}")
        lines.append(" *")
        
        # テスト条件（詳細）
        condition_detail = self._generate_condition_detail(test_case, parsed_data)
        if condition_detail:
            lines.append(" * 【テスト条件】")
            for detail_line in condition_detail:
                lines.append(f" * {detail_line}")
            lines.append(" *")
        
        # コメント終了
        lines.append(" */")
        
        return '\n'.join(lines)
    
    def _generate_condition_detail(self, test_case: TestCase, parsed_data: ParsedData) -> List[str]:
        """
        条件の詳細を生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            詳細行のリスト
        """
        details = []
        
        # leaf_textsがある場合は、それを使って正確な詳細を生成
        if test_case.leaf_texts and len(test_case.leaf_texts) == len(test_case.truth):
            details.append(f"条件詳細（{len(test_case.leaf_texts)}個）:")
            for i, (leaf_text, truth_char) in enumerate(zip(test_case.leaf_texts, test_case.truth), 1):
                truth_str = "真" if truth_char == 'T' else "偽"
                details.append(f"  条件{i}: {leaf_text} → {truth_str}")
            return details
        
        # 対応する条件を検索
        matching_condition = None
        for cond in parsed_data.conditions:
            if cond.expression in test_case.condition:
                matching_condition = cond
                break
        
        if not matching_condition:
            return details
        
        # 条件タイプ別に詳細を生成
        if matching_condition.type == ConditionType.SIMPLE_IF:
            details.append(f"条件式: {matching_condition.expression}")
            if test_case.truth == 'T':
                details.append("→ 真の場合の処理を実行")
            else:
                details.append("→ 偽の場合の処理をスキップ")
        
        elif matching_condition.type == ConditionType.OR_CONDITION:
            if matching_condition.conditions:
                # leaf_textsがない場合は従来の方法
                details.append(f"OR条件（{len(matching_condition.conditions)}個）:")
                for i, cond in enumerate(matching_condition.conditions, 1):
                    if i - 1 < len(test_case.truth):
                        truth_val = test_case.truth[i - 1]
                        truth_str = "真" if truth_val == 'T' else "偽"
                        details.append(f"  条件{i}: {cond} → {truth_str}")
            else:
                details.append(f"左辺: {matching_condition.left}")
                details.append(f"右辺: {matching_condition.right}")
        
        elif matching_condition.type == ConditionType.AND_CONDITION:
            if matching_condition.conditions:
                # leaf_textsがない場合は従来の方法
                details.append(f"AND条件（{len(matching_condition.conditions)}個）:")
                for i, cond in enumerate(matching_condition.conditions, 1):
                    if i - 1 < len(test_case.truth):
                        truth_val = test_case.truth[i - 1]
                        truth_str = "真" if truth_val == 'T' else "偽"
                        details.append(f"  条件{i}: {cond} → {truth_str}")
            else:
                details.append(f"左辺: {matching_condition.left}")
                details.append(f"右辺: {matching_condition.right}")
        
        elif matching_condition.type == ConditionType.SWITCH:
            # case値を抽出
            if 'case' in test_case.condition:
                import re
                match = re.search(r'case\s+(\w+)', test_case.condition)
                if match:
                    case_value = match.group(1)
                    details.append(f"switch式: {matching_condition.expression}")
                    details.append(f"実行するcase: {case_value}")
        
        return details
    
    def generate_test_summary(self, test_cases: List[TestCase]) -> str:
        """
        全テストケースのサマリーコメントを生成
        
        Args:
            test_cases: テストケースのリスト
        
        Returns:
            サマリーコメント
        """
        lines = []
        lines.append("/**")
        lines.append(" * テストケース一覧")
        lines.append(" *")
        lines.append(f" * 総テスト数: {len(test_cases)}")
        lines.append(" *")
        
        # タイプ別の集計
        from collections import Counter
        truth_counts = Counter(tc.truth for tc in test_cases if tc.truth and tc.truth != '-')
        
        if truth_counts:
            lines.append(" * 【真偽パターン別】")
            for truth, count in sorted(truth_counts.items()):
                lines.append(f" *   {truth:4s}: {count:2d}個")
            lines.append(" *")
        
        lines.append(" */")
        
        return '\n'.join(lines)
    
    def generate_function_header(self, function_name: str, description: str = "") -> str:
        """
        関数のヘッダコメントを生成
        
        Args:
            function_name: 関数名
            description: 説明
        
        Returns:
            ヘッダコメント
        """
        lines = []
        lines.append("/**")
        lines.append(f" * {function_name}")
        if description:
            lines.append(" *")
            lines.append(f" * {description}")
        lines.append(" */")
        
        return '\n'.join(lines)


if __name__ == "__main__":
    # CommentGeneratorのテスト
    print("=" * 70)
    print("CommentGenerator のテスト")
    print("=" * 70)
    print()
    
    from src.data_structures import TestCase, ParsedData, Condition, ConditionType
    
    # テスト用データ
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="test_func"
    )
    
    # 条件を追加
    parsed_data.conditions.append(
        Condition(
            line=10,
            type=ConditionType.SIMPLE_IF,
            expression="(v10 > 30)"
        )
    )
    
    parsed_data.conditions.append(
        Condition(
            line=15,
            type=ConditionType.OR_CONDITION,
            expression="((mx63 == m47) || (mx63 == m46))",
            operator='or',
            left="(mx63 == m47)",
            right="(mx63 == m46)",
            conditions=["(mx63 == m47)", "(mx63 == m46)"]
        )
    )
    
    # テストケース
    test_case1 = TestCase(
        no=1,
        truth="T",
        condition="if (v10 > 30)",
        expected="条件が真の処理を実行"
    )
    
    test_case2 = TestCase(
        no=3,
        truth="TF",
        condition="if ((mx63 == m47) || (mx63 == m46))",
        expected="左辺が真、右辺が偽"
    )
    
    # コメントを生成
    generator = CommentGenerator()
    
    print("テスト1: 単純条件のコメント")
    print("-" * 70)
    print(generator.generate_comment(test_case1, parsed_data))
    print()
    
    print("テスト2: OR条件のコメント")
    print("-" * 70)
    print(generator.generate_comment(test_case2, parsed_data))
    print()
    
    print("テスト3: テストサマリー")
    print("-" * 70)
    print(generator.generate_test_summary([test_case1, test_case2]))
    print()
    
    print("テスト4: 関数ヘッダー")
    print("-" * 70)
    print(generator.generate_function_header("test_01_v10_gt_30_T", "境界値テスト"))
    print()
    
    print("✓ CommentGeneratorが正常に動作しました")
