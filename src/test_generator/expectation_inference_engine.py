"""
期待値推論エンジン

テストケースの期待値を条件分岐とMC/DC解析結果から自動推論する。
"""

import re
import ast
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """推論信頼度レベル"""
    HIGH = "HIGH"        # 90-100%: 明確な戻り値
    MEDIUM = "MEDIUM"    # 60-89%: 計算可能な式
    LOW = "LOW"          # 30-59%: 複雑な計算
    UNCERTAIN = "UNCERTAIN"  # <30%: 推論困難


@dataclass
class ExpectedValue:
    """推論された期待値"""
    value: Any                    # 推論された値
    confidence: float             # 信頼度 (0.0 - 1.0)
    confidence_level: ConfidenceLevel  # 信頼度レベル
    comment: str                  # 説明コメント
    is_inferred: bool = True      # 推論されたかどうか


@dataclass
class ReturnStatement:
    """return文の情報"""
    expression: str               # return式
    line_number: int             # 行番号
    condition_context: str       # 条件コンテキスト
    is_constant: bool           # 定数かどうか
    value: Optional[Any] = None  # 評価可能な場合の値


class ExpectationInferenceEngine:
    """期待値推論エンジン"""
    
    def __init__(self):
        self.confidence_threshold = 0.6  # 推論を採用する最小信頼度
        self.return_patterns = {}        # キャッシュされた戻り値パターン
        
    def infer_expected_value(
        self,
        function_body: str,
        mcdc_conditions: Dict[str, bool],
        variable_values: Optional[Dict[str, Any]] = None
    ) -> ExpectedValue:
        """
        テストケースの期待値を推論
        
        Args:
            function_body: 関数本体のコード
            mcdc_conditions: MC/DC条件の真偽値マップ
            variable_values: 変数の値（オプション）
            
        Returns:
            推論された期待値
        """
        try:
            # 1. return文を抽出
            return_statements = self._extract_return_statements(function_body)
            
            if not return_statements:
                return self._create_uncertain_value("No return statements found")
            
            # 2. 実行パスを特定
            executed_return = self._find_executed_return(
                return_statements,
                mcdc_conditions,
                function_body
            )
            
            if not executed_return:
                return self._create_uncertain_value("Cannot determine execution path")
            
            # 3. 戻り値を評価
            expected_value = self._evaluate_return_expression(
                executed_return,
                variable_values or {}
            )
            
            # 4. 信頼度を計算
            confidence = self._calculate_confidence(executed_return, expected_value)
            
            return ExpectedValue(
                value=expected_value,
                confidence=confidence,
                confidence_level=self._get_confidence_level(confidence),
                comment=self._generate_comment(executed_return, confidence),
                is_inferred=True
            )
            
        except Exception as e:
            logger.warning(f"期待値推論中にエラー: {e}")
            return self._create_uncertain_value(f"Inference error: {str(e)}")
    
    def _extract_return_statements(self, function_body: str) -> List[ReturnStatement]:
        """関数本体からreturn文を抽出"""
        statements = []
        lines = function_body.split('\n')
        
        # 簡易的なコンテキスト追跡
        current_context = []
        indent_stack = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # コンテキストの更新
            if any(keyword in stripped for keyword in ['if', 'else if', 'else', 'switch', 'case', 'default:']):
                indent = len(line) - len(line.lstrip())
                
                # インデントレベルの調整
                while indent_stack and indent_stack[-1][0] >= indent:
                    indent_stack.pop()
                    if current_context:
                        current_context.pop()
                
                # switch/case文の特別な処理
                if 'switch' in stripped or 'case' in stripped or 'default:' in stripped:
                    current_context.append(stripped.replace(':', ''))
                else:
                    current_context.append(stripped)
                indent_stack.append((indent, stripped))
            
            # return文の検出（セミコロンはオプショナル）
            return_match = re.match(r'\s*return\s+([^;]+);?', line)
            if return_match:
                expression = return_match.group(1).strip()
                if expression.endswith(';'):
                    expression = expression[:-1]
                
                # 定数かどうかを判定
                is_constant, value = self._is_constant_expression(expression)
                
                statement = ReturnStatement(
                    expression=expression,
                    line_number=i,
                    condition_context=' -> '.join(current_context) if current_context else 'default',
                    is_constant=is_constant,
                    value=value
                )
                statements.append(statement)
        
        return statements
    
    def _is_constant_expression(self, expression: str) -> Tuple[bool, Optional[Any]]:
        """式が定数かどうかを判定し、可能なら値を評価"""
        try:
            # 単純な数値リテラル
            if expression.isdigit() or (expression.startswith('-') and expression[1:].isdigit()):
                return True, int(expression)
            
            # 16進数
            if expression.startswith('0x') or expression.startswith('0X'):
                return True, int(expression, 16)
            
            # 浮動小数点
            if '.' in expression:
                try:
                    value = float(expression)
                    return True, value
                except ValueError:
                    pass
            
            # 文字リテラル
            if expression.startswith("'") and expression.endswith("'"):
                return True, ord(expression[1:-1]) if len(expression) == 3 else None
            
            # よく使われる定数
            common_constants = {
                'true': 1, 'TRUE': 1,
                'false': 0, 'FALSE': 0,
                'NULL': 0, 'nullptr': 0
            }
            if expression in common_constants:
                return True, common_constants[expression]
            
            return False, None
            
        except Exception:
            return False, None
    
    def _find_executed_return(
        self,
        return_statements: List[ReturnStatement],
        mcdc_conditions: Dict[str, bool],
        function_body: str
    ) -> Optional[ReturnStatement]:
        """MC/DC条件に基づいて実行されるreturn文を特定"""
        
        # 条件に基づいてreturn文を選択
        for stmt in return_statements:
            # defaultコンテキスト（else節など）
            if stmt.condition_context == 'default' or 'else' in stmt.condition_context:
                # 他の条件がすべてfalseの場合
                if not any(mcdc_conditions.values()):
                    return stmt
            
            # 条件コンテキストとMC/DC条件のマッチング
            if self._matches_mcdc_conditions(stmt.condition_context, mcdc_conditions):
                return stmt
        
        # マッチしない場合、条件に基づいて適切なreturn文を選択
        # if文の場合、最初の条件がtrueなら最初のreturn、そうでなければ2番目
        if return_statements:
            # 簡易的なロジック: 条件の値に基づいて選択
            true_conditions = sum(1 for v in mcdc_conditions.values() if v)
            if true_conditions > 0 and len(return_statements) > 0:
                return return_statements[0]  # 最初の条件がtrue
            elif len(return_statements) > 1:
                return return_statements[1]  # else節
        
        # デフォルトで最初のreturn文を返す
        return return_statements[0] if return_statements else None
    
    def _matches_mcdc_conditions(
        self,
        condition_context: str,
        mcdc_conditions: Dict[str, bool]
    ) -> bool:
        """条件コンテキストがMC/DC条件にマッチするか確認"""
        # 簡易的な実装
        # TODO: より正確なマッチングロジックを実装
        
        # if文のマッチング
        if 'if' in condition_context:
            # 条件がtrueの場合
            for cond, value in mcdc_conditions.items():
                if value and cond in condition_context:
                    return True
        
        return False
    
    def _evaluate_return_expression(
        self,
        return_stmt: ReturnStatement,
        variable_values: Dict[str, Any]
    ) -> Any:
        """return式を評価して値を推定"""
        
        # 定数の場合
        if return_stmt.is_constant and return_stmt.value is not None:
            return return_stmt.value
        
        expression = return_stmt.expression
        
        # 単純な変数参照
        if expression in variable_values:
            return variable_values[expression]
        
        # 単純な算術式を評価
        try:
            # 変数を値で置換
            eval_expr = expression
            for var, val in variable_values.items():
                eval_expr = eval_expr.replace(var, str(val))
            
            # 安全な評価（限定的な演算子のみ）
            if all(c in '0123456789+-*/() ' for c in eval_expr):
                result = eval(eval_expr)
                return result
        except Exception:
            pass
        
        # 評価できない場合はデフォルト値
        return self._get_default_value_for_type(expression)
    
    def _get_default_value_for_type(self, expression: str) -> Any:
        """式から型を推測してデフォルト値を返す"""
        # ポインタ
        if '*' in expression or '->' in expression:
            return 'NULL'
        
        # 関数呼び出し
        if '(' in expression and ')' in expression:
            return 0  # 多くの関数は0を返す
        
        # デフォルトは0
        return 0
    
    def _calculate_confidence(
        self,
        return_stmt: ReturnStatement,
        expected_value: Any
    ) -> float:
        """推論の信頼度を計算"""
        
        # 定数の場合は高信頼度
        if return_stmt.is_constant:
            return 0.95
        
        # 数値リテラルの場合
        if isinstance(expected_value, (int, float)):
            return 0.85
        
        # 単純な変数参照
        if not any(op in return_stmt.expression for op in ['+', '-', '*', '/', '%', '&', '|', '^']):
            return 0.70
        
        # 算術式
        if any(op in return_stmt.expression for op in ['+', '-', '*', '/']):
            return 0.60
        
        # ビット演算
        if any(op in return_stmt.expression for op in ['&', '|', '^', '<<', '>>']):
            return 0.50
        
        # 関数呼び出し
        if '(' in return_stmt.expression:
            return 0.30
        
        # その他
        return 0.20
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """信頼度スコアからレベルを判定"""
        if confidence >= 0.90:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.60:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.30:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN
    
    def _generate_comment(self, return_stmt: ReturnStatement, confidence: float) -> str:
        """推論結果の説明コメントを生成"""
        if return_stmt.is_constant:
            return f"定数値 (信頼度: {confidence:.0%})"
        
        if confidence >= 0.90:
            return f"推論: 高信頼度 ({confidence:.0%})"
        elif confidence >= 0.60:
            return f"推論: 中信頼度 ({confidence:.0%})"
        elif confidence >= 0.30:
            return f"推論: 低信頼度 ({confidence:.0%}) - 要確認"
        else:
            return f"推論: 不確実 ({confidence:.0%}) - 手動設定推奨"
    
    def _create_uncertain_value(self, reason: str) -> ExpectedValue:
        """不確実な推論結果を作成"""
        return ExpectedValue(
            value=None,
            confidence=0.0,
            confidence_level=ConfidenceLevel.UNCERTAIN,
            comment=f"推論不可: {reason}",
            is_inferred=False
        )
    
    def analyze_function_returns(self, function_body: str) -> Dict[str, Any]:
        """
        関数の戻り値パターンを分析
        
        Returns:
            戻り値パターンの統計情報
        """
        return_statements = self._extract_return_statements(function_body)
        
        analysis = {
            'total_returns': len(return_statements),
            'constant_returns': sum(1 for s in return_statements if s.is_constant),
            'values': [],
            'patterns': []
        }
        
        for stmt in return_statements:
            if stmt.is_constant and stmt.value is not None:
                analysis['values'].append(stmt.value)
            
            # パターンを抽出
            if 'if' in stmt.condition_context:
                analysis['patterns'].append('conditional')
            elif 'switch' in stmt.condition_context or 'case' in stmt.condition_context:
                analysis['patterns'].append('switch')
            else:
                analysis['patterns'].append('default')
        
        # 最頻値を計算
        if analysis['values']:
            from collections import Counter
            value_counts = Counter(analysis['values'])
            analysis['most_common_value'] = value_counts.most_common(1)[0][0]
        
        return analysis


def infer_expected_values_for_test(
    function_body: str,
    test_cases: List[Dict[str, Any]]
) -> List[ExpectedValue]:
    """
    複数のテストケースに対して期待値を推論
    
    Args:
        function_body: 関数本体
        test_cases: テストケースのリスト
        
    Returns:
        推論された期待値のリスト
    """
    engine = ExpectationInferenceEngine()
    results = []
    
    for test_case in test_cases:
        mcdc_conditions = test_case.get('conditions', {})
        variable_values = test_case.get('inputs', {})
        
        expected = engine.infer_expected_value(
            function_body,
            mcdc_conditions,
            variable_values
        )
        results.append(expected)
    
    return results
