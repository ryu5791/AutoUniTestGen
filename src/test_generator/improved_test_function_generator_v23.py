"""
改良版TestFunctionGeneratorモジュール (v2.3)

期待値推論機能を統合したUnityテスト関数生成
"""

import sys
import os
import re
from typing import List, Dict, Optional, Any

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger, sanitize_identifier
from src.data_structures import TestCase, ParsedData, Condition, ConditionType
from src.test_generator.boundary_value_calculator import BoundaryValueCalculator
from src.test_generator.comment_generator import CommentGenerator
from src.test_generator.expectation_inference_engine import (
    ExpectationInferenceEngine,
    ExpectedValue,
    ConfidenceLevel
)
from src.test_generator.return_pattern_analyzer import ReturnPatternAnalyzer


class ImprovedTestFunctionGeneratorV23:
    """改良版テスト関数ジェネレータ (v2.3)"""
    
    def __init__(self, enable_inference: bool = True, confidence_threshold: float = 0.6):
        """
        初期化
        
        Args:
            enable_inference: 期待値推論を有効にするか
            confidence_threshold: 推論を採用する最小信頼度
        """
        self.logger = setup_logger(__name__)
        self.boundary_calc = BoundaryValueCalculator()
        self.comment_gen = CommentGenerator()
        self.enable_inference = enable_inference
        self.confidence_threshold = confidence_threshold
        
        # v2.3: 推論エンジン
        if enable_inference:
            self.inference_engine = ExpectationInferenceEngine()
            self.pattern_analyzer = ReturnPatternAnalyzer()
            self.logger.info("v2.3: 期待値推論エンジンを有効化しました")
    
    def generate_test_function(
        self,
        test_case: TestCase,
        parsed_data: ParsedData,
        function_body: Optional[str] = None
    ) -> str:
        """
        テスト関数を生成
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
            function_body: 関数本体（推論用、オプション）
        
        Returns:
            テスト関数のコード
        """
        lines = []
        
        # ヘッダコメント
        comment = self.comment_gen.generate_comment(test_case, parsed_data)
        lines.append(comment)
        
        # 関数名を生成
        func_name = self._generate_test_name(test_case, parsed_data)
        
        # 関数定義
        lines.append(f"void {func_name}(void) {{")
        
        # ローカル変数の宣言
        lines.append("    // Arrange")
        lines.extend(self._generate_local_variables(parsed_data))
        
        # グローバル変数の初期化
        lines.append("")
        lines.append("    // グローバル変数の初期化")
        lines.extend(self._generate_global_init(parsed_data))
        
        # モックの設定
        lines.append("")
        lines.append("    // モック設定")
        lines.extend(self._generate_mock_setup(test_case, parsed_data))
        
        # 入力値の設定
        lines.append("")
        lines.append("    // 入力値の設定")
        lines.extend(self._generate_input_setup(test_case, parsed_data))
        
        # Act: 関数呼び出し
        lines.append("")
        lines.append("    // Act")
        call_statement = self._generate_function_call(parsed_data)
        lines.append(f"    {call_statement}")
        
        # Assert: 期待値の検証
        lines.append("")
        lines.append("    // Assert")
        
        # v2.3: 推論エンジンを使用して期待値を生成
        if self.enable_inference and function_body:
            assertions = self._generate_assertions_with_inference(
                test_case,
                parsed_data,
                function_body
            )
        else:
            assertions = self._generate_assertions_legacy(test_case, parsed_data)
        
        lines.extend(assertions)
        
        # 関数終了
        lines.append("}")
        
        return '\n'.join(lines)
    
    def _generate_assertions_with_inference(
        self,
        test_case: TestCase,
        parsed_data: ParsedData,
        function_body: str
    ) -> List[str]:
        """
        推論エンジンを使用してアサーションを生成（v2.3）
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
            function_body: 関数本体
        
        Returns:
            アサーション文のリスト
        """
        assertions = []
        
        try:
            # MC/DC条件をマップに変換
            mcdc_conditions = self._build_mcdc_conditions(test_case, parsed_data)
            
            # 変数値をマップに変換
            variable_values = self._build_variable_values(test_case, parsed_data)
            
            # 期待値を推論
            expected = self.inference_engine.infer_expected_value(
                function_body,
                mcdc_conditions,
                variable_values
            )
            
            # 推論結果に基づいてアサーションを生成
            if expected.is_inferred and expected.confidence >= self.confidence_threshold:
                # 高信頼度の推論結果
                if expected.confidence_level == ConfidenceLevel.HIGH:
                    assertions.append(
                        f"    TEST_ASSERT_EQUAL({expected.value}, result);  // {expected.comment}"
                    )
                # 中信頼度の推論結果
                elif expected.confidence_level == ConfidenceLevel.MEDIUM:
                    assertions.append(
                        f"    // {expected.comment}"
                    )
                    assertions.append(
                        f"    TEST_ASSERT_EQUAL({expected.value}, result);  // 要確認"
                    )
                # 低信頼度の推論結果
                else:
                    assertions.append(
                        f"    // {expected.comment}"
                    )
                    assertions.append(
                        f"    // 推論値: {expected.value} (手動確認推奨)"
                    )
                    assertions.append(
                        f"    TEST_ASSERT_EQUAL(/* TODO: 確認 */ {expected.value}, result);"
                    )
            else:
                # 推論失敗または信頼度が低い
                assertions.append(
                    f"    // 自動推論不可: {expected.comment}"
                )
                assertions.extend(self._generate_assertions_legacy(test_case, parsed_data))
            
            # 推論統計をログ出力
            self._log_inference_stats(expected)
            
        except Exception as e:
            self.logger.warning(f"推論中にエラー発生: {e}")
            # フォールバック: レガシーアサーション生成
            assertions.extend(self._generate_assertions_legacy(test_case, parsed_data))
        
        return assertions
    
    def _generate_assertions_legacy(self, test_case: TestCase, parsed_data: ParsedData) -> List[str]:
        """
        レガシーアサーション生成（推論なし）
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            アサーション文のリスト
        """
        assertions = []
        
        # 戻り値の検証
        if parsed_data.return_type and parsed_data.return_type != "void":
            assertions.append("    // TODO: 期待値を設定してください")
            assertions.append("    TEST_ASSERT_EQUAL(/* expected_value */, result);")
        
        # グローバル変数の検証
        if parsed_data.global_variables:
            assertions.append("")
            assertions.append("    // グローバル変数の検証")
            for var_name in parsed_data.global_variables:
                assertions.append(f"    // TEST_ASSERT_EQUAL(/* expected */, {var_name});")
        
        return assertions
    
    def _build_mcdc_conditions(self, test_case: TestCase, parsed_data: ParsedData) -> Dict[str, bool]:
        """
        MC/DC条件をマップに変換
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            条件名と真偽値のマップ
        """
        conditions = {}
        
        # テストケースにcondition_values属性がある場合のみ処理
        if hasattr(test_case, 'condition_values'):
            for i, condition in enumerate(parsed_data.conditions):
                if i < len(test_case.condition_values):
                    # 条件の識別子を作成
                    cond_id = self._get_condition_identifier(condition)
                    conditions[cond_id] = test_case.condition_values[i]
        
        return conditions
    
    def _build_variable_values(self, test_case: TestCase, parsed_data: ParsedData) -> Dict[str, Any]:
        """
        変数値をマップに変換
        
        Args:
            test_case: テストケース
            parsed_data: 解析済みデータ
        
        Returns:
            変数名と値のマップ
        """
        values = {}
        
        # パラメータの値（paramsがない場合は処理をスキップ）
        if hasattr(parsed_data, 'params') and parsed_data.params:
            for param in parsed_data.params:
                # テストケースから適切な値を取得
                # これは簡易的な実装で、実際にはもっと複雑なロジックが必要
                if param.type in ['int', 'unsigned int', 'uint8_t', 'uint16_t', 'uint32_t']:
                    values[param.name] = 1  # デフォルト値
                elif param.type in ['bool', '_Bool']:
                    values[param.name] = True
                elif param.type in ['float', 'double']:
                    values[param.name] = 1.0
                else:
                    values[param.name] = 0
        
        # グローバル変数の値
        for var_name in parsed_data.global_variables:
            values[var_name] = 0  # デフォルト値
        
        return values
    
    def _get_condition_identifier(self, condition: Condition) -> str:
        """
        条件の識別子を生成
        
        Args:
            condition: 条件オブジェクト
        
        Returns:
            条件の識別子
        """
        # 簡易的な実装
        return condition.expression
    
    def _log_inference_stats(self, expected: ExpectedValue):
        """
        推論統計をログ出力
        
        Args:
            expected: 推論結果
        """
        if expected.is_inferred:
            self.logger.info(
                f"v2.3 推論結果: 値={expected.value}, "
                f"信頼度={expected.confidence:.0%}, "
                f"レベル={expected.confidence_level.value}"
            )
        else:
            self.logger.debug(f"v2.3 推論失敗: {expected.comment}")
    
    def _generate_test_name(self, test_case: TestCase, parsed_data: ParsedData) -> str:
        """テスト関数名を生成"""
        func_name = parsed_data.function_name
        test_id = test_case.test_name if test_case.test_name else f"TC_{test_case.no:03d}"
        test_id = test_id.replace('-', '_')
        return f"test_{func_name}_{test_id}"
    
    def _generate_local_variables(self, parsed_data: ParsedData) -> List[str]:
        """ローカル変数の宣言を生成"""
        lines = []
        
        # 戻り値格納用変数
        if parsed_data.return_type and parsed_data.return_type != "void":
            lines.append(f"    {parsed_data.return_type} result;")
        
        # パラメータ用変数（paramsがある場合のみ）
        if hasattr(parsed_data, 'params') and parsed_data.params:
            for param in parsed_data.params:
                if '*' in param.type:
                    # ポインタ型の場合
                    base_type = param.type.replace('*', '').strip()
                    lines.append(f"    {base_type} {param.name}_value;")
                    lines.append(f"    {param.type} {param.name} = &{param.name}_value;")
                else:
                    lines.append(f"    {param.type} {param.name};")
        
        return lines
    
    def _generate_global_init(self, parsed_data: ParsedData) -> List[str]:
        """グローバル変数の初期化を生成"""
        lines = []
        
        # global_variablesは文字列のリストなので、シンプルな初期化のみ
        for var_name in parsed_data.global_variables:
            lines.append(f"    {var_name} = 0;")
        
        return lines
    
    def _generate_mock_setup(self, test_case: TestCase, parsed_data: ParsedData) -> List[str]:
        """モック設定を生成"""
        lines = []
        
        # external_functionsを使用
        for func_call in parsed_data.external_functions:
            # モック関数の期待値設定
            lines.append(f"    {func_call}_ExpectAndReturn(/* params */, /* return_value */);")
        
        return lines
    
    def _generate_input_setup(self, test_case: TestCase, parsed_data: ParsedData) -> List[str]:
        """入力値の設定を生成"""
        lines = []
        
        # パラメータがある場合のみ境界値を計算して設定
        if hasattr(parsed_data, 'params') and parsed_data.params:
            for i, param in enumerate(parsed_data.params):
                value = self._calculate_input_value(param, test_case, i)
                if '*' in param.type:
                    lines.append(f"    {param.name}_value = {value};")
                else:
                    lines.append(f"    {param.name} = {value};")
        
        return lines
    
    def _calculate_input_value(self, param, test_case, index) -> str:
        """入力値を計算"""
        # 簡易的な実装
        if param.type in ['int', 'unsigned int', 'uint8_t', 'uint16_t', 'uint32_t']:
            return str(index + 1)
        elif param.type in ['bool', '_Bool']:
            return 'true' if index % 2 == 0 else 'false'
        else:
            return '0'
    
    def _generate_function_call(self, parsed_data: ParsedData) -> str:
        """関数呼び出し文を生成"""
        # パラメータがある場合のみ引数を設定
        if hasattr(parsed_data, 'params') and parsed_data.params:
            params = ', '.join(p.name for p in parsed_data.params)
        else:
            params = ''
        
        if parsed_data.return_type and parsed_data.return_type != "void":
            return f"result = {parsed_data.function_name}({params});"
        else:
            return f"{parsed_data.function_name}({params});"


def generate_improved_test_function_v23(
    test_case: TestCase,
    parsed_data: ParsedData,
    function_body: Optional[str] = None,
    enable_inference: bool = True
) -> str:
    """
    改良版テスト関数を生成（v2.3）
    
    Args:
        test_case: テストケース
        parsed_data: 解析済みデータ
        function_body: 関数本体（推論用）
        enable_inference: 期待値推論を有効にするか
    
    Returns:
        生成されたテスト関数のコード
    """
    generator = ImprovedTestFunctionGeneratorV23(enable_inference=enable_inference)
    return generator.generate_test_function(test_case, parsed_data, function_body)
