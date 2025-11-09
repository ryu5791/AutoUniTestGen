"""
Unity Test Generator v2.3 with Expectation Inference

期待値の自動推論機能を統合したテストジェネレーター
"""

import os
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# v2.3の新モジュール
from src.inference.expectation_inference_engine import (
    ExpectationInferenceEngine, 
    InferredExpectation,
    SmartTODOGenerator
)
from src.analyzer.enhanced_ast_analyzer import (
    EnhancedASTAnalyzer,
    BranchEffect,
    VariableInfo
)


class UnityTestGeneratorV23:
    """Unity Test Generator v2.3"""
    
    def __init__(self):
        self.inference_engine = ExpectationInferenceEngine()
        self.ast_analyzer = EnhancedASTAnalyzer()
        self.todo_generator = SmartTODOGenerator()
        self.expectations_cache = {}
        
    def generate_test_function_v23(self, test_case, parsed_data, function_name) -> str:
        """v2.3: 期待値推論を使用してテスト関数を生成"""
        lines = []
        test_name = self._generate_test_name(test_case, function_name)
        
        # テスト関数のシグネチャ
        lines.append(f"void {test_name}(void)")
        lines.append("{")
        
        # テストケース情報のコメント
        lines.extend(self._generate_test_comments_v23(test_case))
        
        # 変数の初期化
        lines.extend(self._generate_variable_init_v23(test_case, parsed_data))
        
        # モック設定
        lines.extend(self._generate_mock_setup_v23(test_case, parsed_data))
        
        # テスト対象関数の呼び出し
        lines.extend(self._generate_function_call(function_name, parsed_data))
        
        # 期待値の自動推論とアサーション生成（v2.3の核心）
        lines.extend(self._generate_smart_assertions_v23(test_case, parsed_data))
        
        # モック呼び出し回数チェック
        lines.extend(self._generate_mock_checks_v23(parsed_data))
        
        lines.append("}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_test_comments_v23(self, test_case) -> List[str]:
        """v2.3: より具体的なコメントを生成"""
        lines = []
        lines.append("    // " + "=" * 60)
        lines.append(f"    // テストケース {test_case['no']}")
        
        # 条件と真偽値
        if 'condition' in test_case:
            condition = test_case['condition']
            truth = test_case.get('truth', '')
            lines.append(f"    // 条件: {condition}")
            lines.append(f"    // 真偽: {truth}")
            
            # v2.3: 条件から推論される期待動作を追加
            inferred_behavior = self._infer_expected_behavior(condition, truth)
            if inferred_behavior:
                lines.append(f"    // 推論された期待動作: {inferred_behavior}")
        
        # 既存の期待値
        if 'expected' in test_case:
            lines.append(f"    // 期待結果: {test_case['expected']}")
        
        lines.append("    // " + "=" * 60)
        lines.append("")
        
        return lines
    
    def _generate_variable_init_v23(self, test_case, parsed_data) -> List[str]:
        """v2.3: スマートな変数初期化"""
        lines = []
        lines.append("    // 変数の初期化")
        
        # グローバル変数の初期化
        for var in parsed_data.get('global_variables', []):
            # v2.3: 条件から適切な初期値を推論
            init_value = self._infer_initial_value(var, test_case)
            lines.append(f"    {var} = {init_value};")
        
        lines.append("")
        return lines
    
    def _generate_smart_assertions_v23(self, test_case, parsed_data) -> List[str]:
        """v2.3: 期待値を自動推論してアサーションを生成"""
        lines = []
        lines.append("    // 結果の検証 (v2.3: 自動推論)")
        
        # 条件から期待値を推論
        condition = test_case.get('condition', '')
        truth = test_case.get('truth', '')
        
        expectations = self._infer_expectations(condition, truth, parsed_data)
        
        if expectations:
            # 推論された期待値に基づくアサーション
            for exp in expectations:
                if exp.confidence >= 0.7:
                    # 信頼度が高い場合は直接アサーション生成
                    assertion = self.inference_engine.generate_smart_assertion(exp)
                    lines.append(f"    {assertion}")
                    lines.append(f"    // 推論根拠: {exp.reason} (信頼度: {exp.confidence:.1%})")
                else:
                    # 信頼度が低い場合はヒント付きTODO
                    todo = self._generate_helpful_todo(exp, test_case)
                    lines.extend([f"    {line}" for line in todo.split('\n')])
        else:
            # 推論できない場合は従来のTODOコメント（ただしより具体的に）
            lines.append("    // TODO: 以下から適切な期待値を設定してください")
            lines.append(f"    // 条件 '{condition}' が {truth} の場合の結果を確認")
            lines.append("    // TEST_ASSERT_EQUAL(期待値, 実際の値);")
            lines.append("    // TEST_ASSERT_TRUE(条件);")
            lines.append("    // TEST_ASSERT_NOT_NULL(ポインタ);")
        
        lines.append("")
        return lines
    
    def _infer_expectations(self, condition: str, truth: str, 
                           parsed_data: dict) -> List[InferredExpectation]:
        """条件と真偽値から期待値を推論"""
        expectations = []
        
        # 真偽値のパース
        truth_values = self._parse_truth_values(truth)
        
        # 各条件について推論
        if '||' in condition:
            # OR条件の場合
            sub_conditions = condition.split('||')
            for i, sub_cond in enumerate(sub_conditions):
                if i < len(truth_values):
                    truth_val = truth_values[i] == 'T'
                    sub_expectations = self.inference_engine.infer_from_condition(
                        sub_cond.strip(), truth_val
                    )
                    expectations.extend(sub_expectations)
        
        elif '&&' in condition:
            # AND条件の場合
            sub_conditions = condition.split('&&')
            for i, sub_cond in enumerate(sub_conditions):
                if i < len(truth_values):
                    truth_val = truth_values[i] == 'T'
                    sub_expectations = self.inference_engine.infer_from_condition(
                        sub_cond.strip(), truth_val
                    )
                    expectations.extend(sub_expectations)
        
        else:
            # 単一条件の場合
            truth_val = 'T' in truth
            expectations = self.inference_engine.infer_from_condition(
                condition.strip(), truth_val
            )
        
        # switch文の処理
        if 'switch' in condition.lower():
            case_match = re.search(r'case\s+(\w+)', condition)
            if case_match:
                case_value = case_match.group(1)
                # switch変数を特定して期待値を設定
                switch_var = self._extract_switch_variable(condition)
                if switch_var:
                    expectations.append(InferredExpectation(
                        variable=switch_var,
                        value=case_value,
                        assertion_type='TEST_ASSERT_EQUAL',
                        confidence=0.95,
                        reason=f"switch文のcase {case_value}"
                    ))
        
        # グローバル変数への影響も推論
        global_effects = self._infer_global_effects(condition, truth, parsed_data)
        expectations.extend(global_effects)
        
        return expectations
    
    def _infer_initial_value(self, variable: str, test_case: dict) -> str:
        """変数の適切な初期値を推論"""
        condition = test_case.get('condition', '')
        truth = test_case.get('truth', '')
        
        # 条件に変数が含まれている場合
        if variable in condition:
            # 比較演算子がある場合は境界値を設定
            patterns = [
                (f'{variable}\\s*>\\s*(\\d+)', lambda x: str(int(x) + 1)),
                (f'{variable}\\s*>=\\s*(\\d+)', lambda x: x),
                (f'{variable}\\s*<\\s*(\\d+)', lambda x: str(int(x) - 1)),
                (f'{variable}\\s*<=\\s*(\\d+)', lambda x: x),
                (f'{variable}\\s*==\\s*(\\d+)', lambda x: x),
            ]
            
            for pattern, value_func in patterns:
                match = re.search(pattern, condition)
                if match:
                    base_value = match.group(1)
                    if 'T' in truth:
                        return value_func(base_value)
                    else:
                        # 条件が偽の場合は異なる値
                        return str(int(base_value) + 100)
        
        # switch文の場合
        if 'switch' in condition.lower() and variable in condition:
            case_match = re.search(r'case\s+(\w+)', condition)
            if case_match:
                return case_match.group(1)
        
        # デフォルト値
        return "0"
    
    def _infer_expected_behavior(self, condition: str, truth: str) -> str:
        """条件から期待される動作を推論"""
        behaviors = []
        
        # 関数呼び出しの検出
        func_calls = re.findall(r'(\w+)\s*\(', condition)
        for func in func_calls:
            if func not in ['if', 'while', 'for', 'switch']:
                behaviors.append(f"{func}()が呼び出される")
        
        # 変数への影響
        if '=' in condition and '==' not in condition and '!=' not in condition:
            behaviors.append("変数への代入が発生")
        
        # 比較演算の結果
        if any(op in condition for op in ['>', '<', '>=', '<=', '==', '!=']):
            if 'T' in truth:
                behaviors.append("条件が成立し、真の分岐を実行")
            else:
                behaviors.append("条件が不成立、偽の分岐を実行")
        
        return "、".join(behaviors) if behaviors else None
    
    def _infer_global_effects(self, condition: str, truth: str, 
                             parsed_data: dict) -> List[InferredExpectation]:
        """グローバル変数への影響を推論"""
        expectations = []
        
        # parsed_dataから分岐の影響情報を取得（事前に解析済みと仮定）
        # 実際の実装では、ASTを解析して分岐内の処理を特定
        
        # 簡単な例: 条件が真の場合にグローバル変数が変更される
        global_vars = parsed_data.get('global_variables', [])
        for var in global_vars:
            # ヒューリスティック: 条件内に変数が含まれていれば影響あり
            if var in condition:
                # 仮の推論: 条件が真なら変数が変更される可能性
                if 'T' in truth:
                    expectations.append(InferredExpectation(
                        variable=var,
                        value="modified_value",  # 実際は詳細な解析が必要
                        assertion_type='TEST_ASSERT_EQUAL',
                        confidence=0.5,
                        reason=f"条件 '{condition}' による可能性のある変更"
                    ))
        
        return expectations
    
    def _generate_helpful_todo(self, expectation: InferredExpectation, 
                              test_case: dict) -> str:
        """より具体的で有用なTODOコメントを生成"""
        lines = []
        lines.append(f"// TODO: {expectation.variable} の期待値を確認してください")
        lines.append(f"//   推論: {expectation.reason}")
        lines.append(f"//   信頼度: {expectation.confidence:.1%}")
        
        # アサーションの例を提供
        if expectation.assertion_type == 'TEST_ASSERT_EQUAL':
            lines.append(f"//   例: TEST_ASSERT_EQUAL(期待値, {expectation.variable});")
        elif expectation.assertion_type == 'TEST_ASSERT_NULL':
            lines.append(f"//   例: TEST_ASSERT_NULL({expectation.variable});")
        elif expectation.assertion_type == 'TEST_ASSERT_NOT_NULL':
            lines.append(f"//   例: TEST_ASSERT_NOT_NULL({expectation.variable});")
        
        # 推論された値がある場合はヒントとして表示
        if expectation.value is not None and expectation.value != "modified_value":
            lines.append(f"//   ヒント: 値は {expectation.value} の可能性があります")
        
        return "\n".join(lines)
    
    def _parse_truth_values(self, truth: str) -> List[str]:
        """真偽値文字列をパース"""
        # "TF" -> ['T', 'F'], "T" -> ['T'], etc.
        return list(truth.upper())
    
    def _extract_switch_variable(self, condition: str) -> Optional[str]:
        """switch文から変数名を抽出"""
        match = re.search(r'switch\s*\((\w+)\)', condition)
        if match:
            return match.group(1)
        return None
    
    def _generate_test_name(self, test_case, function_name: str) -> str:
        """テスト関数名を生成"""
        return f"test_{function_name}_{test_case['no']:03d}"
    
    def _generate_function_call(self, function_name: str, parsed_data: dict) -> List[str]:
        """テスト対象関数の呼び出しを生成"""
        lines = []
        lines.append("    // テスト対象関数の呼び出し")
        lines.append(f"    {function_name}();")
        lines.append("")
        return lines
    
    def _generate_mock_setup_v23(self, test_case, parsed_data) -> List[str]:
        """モック設定を生成"""
        lines = []
        lines.append("    // モック設定")
        
        for func in parsed_data.get('external_functions', []):
            # 条件から適切なモック戻り値を推論
            mock_value = self._infer_mock_return_value(func, test_case)
            lines.append(f"    mock_{func}_return_value = {mock_value};")
        
        lines.append("")
        return lines
    
    def _infer_mock_return_value(self, function_name: str, test_case: dict) -> str:
        """モック関数の適切な戻り値を推論"""
        condition = test_case.get('condition', '')
        truth = test_case.get('truth', '')
        
        # 関数が条件に含まれている場合
        if function_name in condition:
            # ビット演算の場合
            if f"{function_name}()" in condition and "&" in condition:
                # 条件が真になるような値を設定
                if 'T' in truth:
                    return "0xFF"  # ビットが立っている値
                else:
                    return "0x00"  # ビットが立っていない値
            
            # 比較演算の場合
            patterns = [
                (f'{function_name}\\(\\)\\s*==\\s*(\\w+)', lambda x: x),
                (f'{function_name}\\(\\)\\s*!=\\s*(\\w+)', lambda x: f"~{x}"),
            ]
            
            for pattern, value_func in patterns:
                match = re.search(pattern, condition)
                if match:
                    return value_func(match.group(1))
        
        # デフォルト値
        return "0"
    
    def _generate_mock_checks_v23(self, parsed_data) -> List[str]:
        """モック呼び出しチェックを生成"""
        lines = []
        lines.append("    // モック呼び出し回数チェック")
        
        for func in parsed_data.get('external_functions', []):
            lines.append(f"    TEST_ASSERT_EQUAL(1, mock_{func}_call_count);")
        
        lines.append("")
        return lines
