"""
TruthTableGeneratorモジュール

MC/DC真偽表を生成
"""

import sys
import os
from typing import List, Optional

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import ParsedData, TruthTableData, TestCase, ConditionType
from src.truth_table.condition_analyzer import ConditionAnalyzer
from src.truth_table.mcdc_pattern_generator import MCDCPatternGenerator


class TruthTableGenerator:
    """真偽表ジェネレータ"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.analyzer = ConditionAnalyzer()
        self.mcdc_gen = MCDCPatternGenerator()
        self.test_number = 0
    
    def generate(self, parsed_data: ParsedData) -> TruthTableData:
        """
        真偽表を生成
        
        Args:
            parsed_data: 解析済みデータ
        
        Returns:
            真偽表データ
        """
        self.logger.info("真偽表の生成を開始")
        self.test_number = 0
        
        test_cases = []
        
        # 各条件分岐に対してテストケースを生成
        for condition in parsed_data.conditions:
            cases = self._generate_test_cases_for_condition(condition)
            test_cases.extend(cases)
        
        truth_table = TruthTableData(
            function_name=parsed_data.function_name,
            test_cases=test_cases,
            total_tests=len(test_cases)
        )
        
        self.logger.info(f"真偽表の生成が完了: {len(test_cases)}個のテストケース")
        return truth_table
    
    def _generate_test_cases_for_condition(self, condition) -> List[TestCase]:
        """
        1つの条件分岐に対するテストケースを生成
        
        Args:
            condition: 条件分岐
        
        Returns:
            テストケースのリスト
        """
        # 条件を分析
        analysis = self.analyzer.analyze_condition(condition)
        
        test_cases = []
        
        if condition.type == ConditionType.SIMPLE_IF:
            # 単純なif文: T, F
            for pattern in analysis['patterns']:
                test_case = self._create_test_case(
                    condition=condition,
                    pattern=pattern,
                    analysis=analysis
                )
                test_cases.append(test_case)
        
        elif condition.type == ConditionType.OR_CONDITION:
            # OR条件: TF, FT, FF
            for pattern in analysis['patterns']:
                test_case = self._create_test_case(
                    condition=condition,
                    pattern=pattern,
                    analysis=analysis
                )
                test_cases.append(test_case)
        
        elif condition.type == ConditionType.AND_CONDITION:
            # AND条件: TF, FT, TT
            for pattern in analysis['patterns']:
                test_case = self._create_test_case(
                    condition=condition,
                    pattern=pattern,
                    analysis=analysis
                )
                test_cases.append(test_case)
        
        elif condition.type == ConditionType.SWITCH:
            # switch文: 各case
            for case_value in condition.cases:
                pattern = f'case_{case_value}'
                test_case = self._create_test_case(
                    condition=condition,
                    pattern=pattern,
                    analysis=analysis,
                    case_value=case_value
                )
                test_cases.append(test_case)
        
        return test_cases
    
    def _create_test_case(self, condition, pattern: str, analysis: dict, case_value: Optional[str] = None) -> TestCase:
        """
        テストケースを作成
        
        Args:
            condition: 条件分岐
            pattern: 真偽パターン
            analysis: 分析結果
            case_value: case値（switch文の場合）
        
        Returns:
            テストケース
        """
        self.test_number += 1
        
        # 条件文を整形
        if condition.type == ConditionType.SWITCH:
            condition_str = f"switch ({condition.expression}) - case {case_value}"
        else:
            condition_str = f"if {condition.expression}"
        
        # 期待値を生成
        expected = self._generate_expected_value(condition, pattern, analysis, case_value)
        
        # 葉条件テキストを取得（MC/DC用）
        leaf_texts = analysis.get('leaf_texts', [])
        
        # テストケースを作成
        test_case = TestCase(
            no=self.test_number,
            truth=pattern if not pattern.startswith('case_') else '-',
            condition=condition_str,
            expected=expected,
            leaf_texts=leaf_texts
        )
        
        return test_case
    
    def _generate_expected_value(self, condition, pattern: str, analysis: dict, case_value: Optional[str] = None) -> str:
        """
        期待値を生成
        
        Args:
            condition: 条件分岐
            pattern: 真偽パターン
            analysis: 分析結果
            case_value: case値
        
        Returns:
            期待値の説明
        """
        if condition.type == ConditionType.SWITCH:
            return f"case {case_value} の処理を実行"
        
        elif condition.type == ConditionType.SIMPLE_IF:
            if pattern == 'T':
                return "条件が真の処理を実行"
            else:
                return "条件が偽の処理を実行"
        
        elif condition.type == ConditionType.OR_CONDITION:
            explanation = analysis.get('mcdc_explanation', {})
            return explanation.get(pattern, "処理を実行")
        
        elif condition.type == ConditionType.AND_CONDITION:
            explanation = analysis.get('mcdc_explanation', {})
            return explanation.get(pattern, "処理を実行")
        
        return ""
    
    def _format_condition_for_test_name(self, condition_str: str) -> str:
        """
        テスト名用に条件式を整形
        
        Args:
            condition_str: 条件式
        
        Returns:
            整形された文字列
        """
        # 不要な文字を削除
        formatted = condition_str.replace('(', '').replace(')', '').replace(' ', '_')
        
        # 特殊文字を置換
        replacements = {
            '==': 'eq',
            '!=': 'ne',
            '>': 'gt',
            '<': 'lt',
            '>=': 'ge',
            '<=': 'le',
            '||': 'or',
            '&&': 'and',
            '&': 'and',
            '|': 'or'
        }
        
        for old, new in replacements.items():
            formatted = formatted.replace(old, new)
        
        # 長すぎる場合は短縮
        if len(formatted) > 50:
            formatted = formatted[:50]
        
        return formatted


if __name__ == "__main__":
    # TruthTableGeneratorのテスト
    print("=== TruthTableGenerator のテスト ===\n")
    
    from src.data_structures import ParsedData, Condition, ConditionType
    
    # テスト用のParseDataを作成
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="test_func"
    )
    
    # 条件1: 単純なif文
    parsed_data.conditions.append(
        Condition(
            line=10,
            type=ConditionType.SIMPLE_IF,
            expression="(v10 > 30)"
        )
    )
    
    # 条件2: OR条件
    parsed_data.conditions.append(
        Condition(
            line=15,
            type=ConditionType.OR_CONDITION,
            expression="((mx63 == m47) || (mx63 == m46))",
            operator='or',
            left="(mx63 == m47)",
            right="(mx63 == m46)"
        )
    )
    
    # 条件3: switch文
    parsed_data.conditions.append(
        Condition(
            line=25,
            type=ConditionType.SWITCH,
            expression="v9",
            cases=['0', '1', '2', 'default']
        )
    )
    
    # 真偽表を生成
    generator = TruthTableGenerator()
    truth_table = generator.generate(parsed_data)
    
    print(f"関数名: {truth_table.function_name}")
    print(f"総テスト数: {truth_table.total_tests}\n")
    
    print("=== 生成されたテストケース ===")
    for tc in truth_table.test_cases:
        print(f"{tc.no:2d}. [{tc.truth:3s}] {tc.condition}")
        print(f"    期待値: {tc.expected}")
        print()
    
    # Excel形式に変換
    print("=== Excel形式 ===")
    excel_data = truth_table.to_excel_format()
    for row in excel_data[:6]:  # 最初の6行を表示
        print(row)
    
    print("\n✓ TruthTableGeneratorが正常に動作しました")
