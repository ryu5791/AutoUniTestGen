"""
データ構造定義モジュール

C言語単体テスト自動生成ツールで使用するデータクラスを定義
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ConditionType(Enum):
    """条件分岐の種類"""
    SIMPLE_IF = "simple_if"
    OR_CONDITION = "or_condition"
    AND_CONDITION = "and_condition"
    SWITCH = "switch"


@dataclass
class Condition:
    """条件分岐の情報"""
    line: int
    type: ConditionType
    expression: str
    operator: Optional[str] = None
    left: Optional[str] = None
    right: Optional[str] = None
    conditions: Optional[List[str]] = None
    cases: Optional[List[Any]] = None
    ast_node: Any = None
    parent_context: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'line': self.line,
            'type': self.type.value,
            'expression': self.expression
        }


@dataclass
class TestCase:
    """テストケースの情報"""
    no: int
    truth: str
    condition: str
    expected: str = ""
    test_name: str = ""
    comment: str = ""
    input_values: Dict[str, Any] = field(default_factory=dict)
    output_values: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'no': self.no,
            'truth': self.truth,
            'condition': self.condition,
            'expected': self.expected
        }


@dataclass
class TruthTableData:
    """真偽表のデータ"""
    function_name: str
    test_cases: List[TestCase] = field(default_factory=list)
    total_tests: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'function_name': self.function_name,
            'test_cases': [tc.to_dict() for tc in self.test_cases],
            'total_tests': self.total_tests
        }


@dataclass
class TestCode:
    """生成されたテストコード"""
    header: str = ""
    includes: str = ""
    type_definitions: str = ""
    prototypes: str = ""
    mock_variables: str = ""
    mock_functions: str = ""
    test_functions: str = ""
    setup_teardown: str = ""
    
    def to_string(self) -> str:
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
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_string())


@dataclass
class IOTableData:
    """I/O表のデータ"""
    input_variables: List[str] = field(default_factory=list)
    output_variables: List[str] = field(default_factory=list)
    test_data: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
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
