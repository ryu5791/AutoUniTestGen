"""
データ構造定義モジュール

C言語単体テスト自動生成ツールで使用するデータクラスを定義
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ConditionType(Enum):
    """条件分岐の種類"""
    SIMPLE_IF = "simple_if"          # 単純なif文
    OR_CONDITION = "or_condition"     # OR条件
    AND_CONDITION = "and_condition"   # AND条件
    SWITCH = "switch"                 # switch文


@dataclass
class Condition:
    """条件分岐の情報"""
    line: int                          # 行番号
    type: ConditionType                # 条件の種類
    expression: str                    # 条件式の文字列表現
    operator: Optional[str] = None     # 二項演算子（OR/ANDの場合）
    left: Optional[str] = None         # 左辺の条件式（2条件の場合の互換性用）
    right: Optional[str] = None        # 右辺の条件式（2条件の場合の互換性用）
    conditions: Optional[List[str]] = None  # 全ての条件のリスト（3つ以上対応）
    cases: Optional[List[Any]] = None  # switch文のcase値リスト
    ast_node: Any = None               # ASTノード（pycparser）
    parent_context: str = ""           # 親のコンテキスト（switch内のif等）
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'line': self.line,
            'type': self.type.value,
            'expression': self.expression,
            'operator': self.operator,
            'left': self.left,
            'right': self.right,
            'conditions': self.conditions,
            'cases': self.cases,
            'parent_context': self.parent_context
        }


@dataclass
class FunctionInfo:
    """関数の情報"""
    name: str                          # 関数名
    return_type: str                   # 戻り値の型
    parameters: List[Dict[str, str]]   # パラメータリスト
    is_static: bool = False            # static関数かどうか
    line_start: int = 0                # 開始行
    line_end: int = 0                  # 終了行
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'name': self.name,
            'return_type': self.return_type,
            'parameters': self.parameters,
            'is_static': self.is_static,
            'line_start': self.line_start,
            'line_end': self.line_end
        }


@dataclass
class ParsedData:
    """C言語ファイルの解析結果"""
    file_name: str                                # ファイル名
    function_name: str                            # テスト対象関数名
    conditions: List[Condition] = field(default_factory=list)       # 条件分岐リスト
    external_functions: List[str] = field(default_factory=list)     # 外部関数リスト
    global_variables: List[str] = field(default_factory=list)       # グローバル変数リスト
    function_info: Optional[FunctionInfo] = None  # 関数情報
    type_definitions: Dict[str, Any] = field(default_factory=dict)  # 型定義
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'file_name': self.file_name,
            'function_name': self.function_name,
            'conditions': [c.to_dict() for c in self.conditions],
            'external_functions': self.external_functions,
            'global_variables': self.global_variables,
            'function_info': self.function_info.to_dict() if self.function_info else None,
            'type_definitions': self.type_definitions
        }


@dataclass
class TestCase:
    """テストケースの情報"""
    no: int                            # テストケース番号
    truth: str                         # 真偽パターン（T, F, TF, FT等）
    condition: str                     # 判定文
    expected: str = ""                 # 期待値
    test_name: str = ""                # テスト関数名
    comment: str = ""                  # ヘッダコメント
    input_values: Dict[str, Any] = field(default_factory=dict)   # 入力値
    output_values: Dict[str, Any] = field(default_factory=dict)  # 出力値（期待値）
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'no': self.no,
            'truth': self.truth,
            'condition': self.condition,
            'expected': self.expected,
            'test_name': self.test_name,
            'comment': self.comment,
            'input_values': self.input_values,
            'output_values': self.output_values
        }


@dataclass
class TruthTableData:
    """真偽表のデータ"""
    function_name: str                           # 対象関数名
    test_cases: List[TestCase] = field(default_factory=list)  # テストケースリスト
    total_tests: int = 0                         # 総テスト数
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'function_name': self.function_name,
            'test_cases': [tc.to_dict() for tc in self.test_cases],
            'total_tests': self.total_tests
        }
    
    def to_excel_format(self) -> List[List[Any]]:
        """Excel形式のリストに変換"""
        rows = [['No.', '真偽', '判定文', '期待値']]
        for tc in self.test_cases:
            rows.append([tc.no, tc.truth, tc.condition, tc.expected])
        return rows


@dataclass
class MockFunction:
    """モック関数の情報"""
    name: str                          # 関数名
    return_type: str                   # 戻り値の型
    parameters: List[Dict[str, str]]   # パラメータリスト
    return_variable: str = ""          # 戻り値変数名
    call_count_variable: str = ""      # 呼び出し回数変数名
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'name': self.name,
            'return_type': self.return_type,
            'parameters': self.parameters,
            'return_variable': self.return_variable,
            'call_count_variable': self.call_count_variable
        }


@dataclass
class TestCode:
    """生成されたテストコード"""
    header: str = ""                   # ヘッダーコメント
    includes: str = ""                 # #include文
    type_definitions: str = ""         # 型定義
    prototypes: str = ""               # プロトタイプ宣言
    mock_variables: str = ""           # モック用グローバル変数
    mock_functions: str = ""           # モック関数実装
    test_functions: str = ""           # テスト関数群
    setup_teardown: str = ""           # setUp/tearDown関数
    
    def to_string(self) -> str:
        """完全なコード文字列に変換"""
        parts = [
            self.header,
            self.includes,
            self.type_definitions,
            self.prototypes,
            self.mock_variables,
            self.mock_functions,
            self.test_functions,
            self.setup_teardown
        ]
        return '\n\n'.join(p for p in parts if p)
    
    def save(self, filepath: str) -> None:
        """ファイルに保存"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_string())


@dataclass
class IOTableData:
    """I/O表のデータ"""
    input_variables: List[str] = field(default_factory=list)   # 入力変数リスト
    output_variables: List[str] = field(default_factory=list)  # 出力変数リスト
    test_data: List[Dict[str, Any]] = field(default_factory=list)  # テストデータ
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'input_variables': self.input_variables,
            'output_variables': self.output_variables,
            'test_data': self.test_data
        }
    
    def to_excel_format(self) -> List[List[Any]]:
        """Excel形式のリストに変換"""
        # ヘッダー行1: input/output
        header1 = ['', ''] + ['input'] * len(self.input_variables) + \
                  ['output'] * len(self.output_variables)
        
        # ヘッダー行2: 変数名
        header2 = ['No', 'テスト名'] + self.input_variables + self.output_variables
        
        # データ行
        data_rows = []
        for idx, test in enumerate(self.test_data, 1):
            row = [idx, test.get('test_name', '')]
            
            # 入力値
            for var in self.input_variables:
                value = test.get('inputs', {}).get(var, '-')
                row.append(value)
            
            # 出力値
            for var in self.output_variables:
                value = test.get('outputs', {}).get(var, '-')
                row.append(value)
            
            data_rows.append(row)
        
        return [header1, header2] + data_rows


if __name__ == "__main__":
    # データ構造のテスト
    print("=== データ構造定義のテスト ===")
    
    # Conditionのテスト
    cond = Condition(
        line=10,
        type=ConditionType.SIMPLE_IF,
        expression="(f4() & 0xdf) != 0"
    )
    print(f"Condition: {cond.to_dict()}")
    
    # TestCaseのテスト
    tc = TestCase(
        no=1,
        truth="T",
        condition="if ((f4() & 0xdf) != 0)",
        expected="v9が7"
    )
    print(f"\nTestCase: {tc.to_dict()}")
    
    # TruthTableDataのテスト
    ttd = TruthTableData(
        function_name="f1",
        test_cases=[tc],
        total_tests=1
    )
    print(f"\nTruthTableData Excel形式:\n{ttd.to_excel_format()}")
    
    print("\n✓ データ構造定義が正常に動作しました")
