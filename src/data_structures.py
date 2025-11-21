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
    main_function: str = ""  # v2.3: main関数
    
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
            self.target_function_code,  # v2.2: 最後の前に追加
            self.main_function  # v2.3: 最後に追加
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
class StructMember:
    """構造体メンバー情報 (v2.8.0で追加)"""
    name: str                              # メンバー名（例: "status"）
    type: str                              # 型名（例: "uint8_t"）
    bit_width: Optional[int] = None        # ビット幅（ビットフィールドの場合）
    is_pointer: bool = False               # ポインタかどうか
    is_array: bool = False                 # 配列かどうか
    array_size: Optional[int] = None       # 配列サイズ
    nested_struct: Optional['StructDefinition'] = None  # ネストした構造体
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = {
            'name': self.name,
            'type': self.type,
            'bit_width': self.bit_width,
            'is_pointer': self.is_pointer,
            'is_array': self.is_array,
            'array_size': self.array_size
        }
        if self.nested_struct:
            result['nested_struct'] = self.nested_struct.to_dict()
        return result
    
    def get_full_type(self) -> str:
        """完全な型名を取得（ポインタや配列を含む）"""
        type_str = self.type
        if self.is_pointer:
            type_str += '*'
        if self.is_array and self.array_size:
            type_str += f'[{self.array_size}]'
        return type_str


@dataclass
class StructDefinition:
    """構造体定義情報 (v2.8.0で追加)"""
    name: str                              # 構造体名（例: "state_def_t"）
    members: List[StructMember] = field(default_factory=list)
    is_typedef: bool = True                # typedefされているか
    original_name: Optional[str] = None    # 元の構造体名（typedef前）
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'name': self.name,
            'members': [m.to_dict() for m in self.members],
            'is_typedef': self.is_typedef,
            'original_name': self.original_name
        }
    
    def get_member(self, member_name: str) -> Optional[StructMember]:
        """メンバーを名前で検索"""
        for member in self.members:
            if member.name == member_name:
                return member
        return None
    
    def get_all_members_flat(self, prefix: str = "") -> List[tuple]:
        """
        すべてのメンバーをフラットなリストで取得（ネスト対応）
        
        Args:
            prefix: メンバー名のプレフィックス
        
        Returns:
            [(アクセスパス, StructMember), ...] のリスト
            例: [("status", member1), ("position.x", member2)]
        """
        result = []
        for member in self.members:
            access_path = f"{prefix}.{member.name}" if prefix else member.name
            
            if member.nested_struct:
                # ネストした構造体の場合、再帰的に展開
                nested_members = member.nested_struct.get_all_members_flat(access_path)
                result.extend(nested_members)
            else:
                # 通常のメンバー
                result.append((access_path, member))
        
        return result


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
    macros: Dict[str, str] = field(default_factory=dict)  # v2.4.2: マクロ定義 {名前: 値}
    macro_definitions: List[str] = field(default_factory=list)  # v2.4.2: マクロ定義文字列のリスト
    struct_definitions: List[StructDefinition] = field(default_factory=list)  # v2.8.0: 構造体定義
    
    def get_struct_definition(self, type_name: str) -> Optional[StructDefinition]:
        """
        型名から構造体定義を取得
        
        Args:
            type_name: 構造体の型名
        
        Returns:
            StructDefinition または None
        """
        # 型名をクリーンアップ（ポインタ記号などを除去）
        clean_name = type_name.replace('*', '').replace('const', '').strip()
        
        # 構造体定義を検索
        for struct_def in self.struct_definitions:
            if struct_def.name == clean_name:
                return struct_def
            # original_nameでも検索
            if struct_def.original_name == clean_name:
                return struct_def
        
        return None
    
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
            'variables': [v.to_dict() for v in self.variables],
            'macros': self.macros,
            'macro_definitions': self.macro_definitions,
            'struct_definitions': [s.to_dict() for s in self.struct_definitions]
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
