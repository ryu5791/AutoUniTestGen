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
    target_function_code: str = ""  # v2.2: テスト対象関数の本体
    
    def to_string(self) -> str:
        parts = [
            self.header,
            self.includes,
            self.type_definitions,
            self.prototypes,
            self.mock_variables,
            self.mock_functions,
            self.test_functions,
            self.setup_teardown,
            self.target_function_code  # v2.2: 最後に追加
        ]
        return '\n\n'.join(p for p in parts if p)
    
    def save(self, filepath: str) -> None:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_string())


@dataclass
class FunctionInfo:
    """関数情報"""
    name: str
    return_type: str = "void"
    parameters: List[Dict[str, str]] = field(default_factory=list)
    local_variables: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'return_type': self.return_type,
            'parameters': self.parameters,
            'local_variables': self.local_variables
        }


@dataclass
class MockFunction:
    """モック関数の情報"""
    name: str
    return_type: str = "void"
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_variable: str = ""
    call_count_variable: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'return_type': self.return_type,
            'parameters': self.parameters,
            'return_variable': self.return_variable,
            'call_count_variable': self.call_count_variable
        }


@dataclass
class BitFieldInfo:
    """ビットフィールド情報"""
    struct_name: str  # 構造体/共用体名
    member_name: str  # メンバー名
    bit_width: int    # ビット幅
    base_type: str    # 基本型（uint8_t, uint16_tなど）
    full_path: str    # フルパス（例: mAdge.category.internal）
    
    def get_max_value(self) -> int:
        """ビットフィールドの最大値を返す"""
        return (1 << self.bit_width) - 1
    
    def get_mask(self) -> int:
        """ビットマスクを返す"""
        return (1 << self.bit_width) - 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'struct_name': self.struct_name,
            'member_name': self.member_name,
            'bit_width': self.bit_width,
            'base_type': self.base_type,
            'full_path': self.full_path
        }


@dataclass
class TypedefInfo:
    """型定義情報 (v2.2で追加)"""
    name: str
    typedef_type: str  # 'struct', 'union', 'enum', 'basic'
    definition: str
    dependencies: List[str]
    line_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'typedef_type': self.typedef_type,
            'definition': self.definition,
            'dependencies': self.dependencies,
            'line_number': self.line_number
        }


@dataclass
class VariableDeclInfo:
    """変数宣言情報 (v2.2で追加)"""
    name: str
    var_type: str
    is_extern: bool
    definition: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'var_type': self.var_type,
            'is_extern': self.is_extern,
            'definition': self.definition
        }


@dataclass
class ParsedData:
    """C言語解析結果データ"""
    file_name: str
    function_name: str
    conditions: List[Condition] = field(default_factory=list)
    external_functions: List[str] = field(default_factory=list)
    global_variables: List[str] = field(default_factory=list)
    function_info: Optional[FunctionInfo] = None
    enums: Dict[str, List[str]] = field(default_factory=dict)  # enum型名 -> 定数リスト
    enum_values: List[str] = field(default_factory=list)  # すべてのenum定数
    bitfields: Dict[str, BitFieldInfo] = field(default_factory=dict)  # メンバー名 -> ビットフィールド情報
    typedefs: List['TypedefInfo'] = field(default_factory=list)  # v2.2: 型定義情報
    variables: List['VariableDeclInfo'] = field(default_factory=list)  # v2.2: 変数宣言情報
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_name': self.file_name,
            'function_name': self.function_name,
            'conditions': [c.to_dict() for c in self.conditions],
            'external_functions': self.external_functions,
            'global_variables': self.global_variables,
            'function_info': self.function_info.to_dict() if self.function_info else None,
            'bitfields': {k: v.to_dict() for k, v in self.bitfields.items()},
            'typedefs': [td.to_dict() for td in self.typedefs],
            'variables': [v.to_dict() for v in self.variables]
        }


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
