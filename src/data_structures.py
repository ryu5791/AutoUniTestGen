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
    # v5.1.1: return文の値を追加
    return_value_if_true: Optional[str] = None   # 条件が真の場合のreturn値
    return_value_if_false: Optional[str] = None  # 条件が偽の場合のreturn値
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'line': self.line,
            'type': self.type.value,
            'expression': self.expression,
            'return_value_if_true': self.return_value_if_true,
            'return_value_if_false': self.return_value_if_false
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
    leaf_texts: List[str] = field(default_factory=list)  # 葉条件のテキストリスト（MC/DC用）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'no': self.no,
            'truth': self.truth,
            'condition': self.condition,
            'expected': self.expected,
            'leaf_texts': self.leaf_texts
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
    
    def to_excel_format(self) -> List[List[Any]]:
        """
        Excel出力用のフォーマットに変換
        
        Returns:
            2次元リスト（ヘッダー行 + データ行）
        """
        if not self.test_cases:
            return []
        
        # 条件名のリストを収集（すべてのテストケースから）
        condition_names = []
        for tc in self.test_cases:
            if hasattr(tc, 'condition_values') and tc.condition_values:
                for cond_name in tc.condition_values.keys():
                    if cond_name not in condition_names:
                        condition_names.append(cond_name)
        
        # ヘッダー行
        header = ['No', 'テスト名'] + condition_names + ['条件式']
        
        # データ行
        rows = [header]
        for idx, tc in enumerate(self.test_cases, 1):
            row = [idx, tc.test_name]
            
            # 条件値
            for cond_name in condition_names:
                if hasattr(tc, 'condition_values') and tc.condition_values:
                    val = tc.condition_values.get(cond_name, '-')
                    row.append('T' if val else 'F')
                else:
                    row.append('-')
            
            # 条件式
            if hasattr(tc, 'condition') and tc.condition:
                if hasattr(tc.condition, 'expression'):
                    condition_str = tc.condition.expression
                else:
                    condition_str = str(tc.condition)
            else:
                condition_str = ''
            row.append(condition_str)
            
            rows.append(row)
        
        return rows


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
class FunctionSignature:
    """関数シグネチャ情報（v4.0）"""
    name: str
    return_type: str = "int"
    parameters: List[Dict[str, str]] = field(default_factory=list)
    # parameters例: [{"type": "uint8_t", "name": "Utv1"}, {"type": "int", "name": "count"}]
    is_static: bool = False
    
    def format_parameters(self) -> str:
        """パラメータ文字列を生成: 'uint8_t Utv1, int Utv2' or 'void'"""
        if not self.parameters:
            return "void"
        return ", ".join(f"{p['type']} {p['name']}" for p in self.parameters)
    
    def format_declaration(self) -> str:
        """完全な関数宣言を生成: 'uint8_t Utf8(void)'"""
        static_prefix = "static " if self.is_static else ""
        return f"{static_prefix}{self.return_type} {self.name}({self.format_parameters()})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'return_type': self.return_type,
            'parameters': self.parameters,
            'is_static': self.is_static
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
    """変数宣言情報 (v2.2で追加, v5.0.0でstatic/配列/構造体対応)"""
    name: str
    var_type: str
    is_extern: bool
    definition: str
    is_static: bool = False           # v5.0.0: static変数かどうか
    is_array: bool = False            # v5.0.0: 配列かどうか
    array_size: Optional[int] = None  # v5.0.0: 配列サイズ
    is_struct: bool = False           # v5.0.0: 構造体かどうか
    struct_type: str = ""             # v5.0.0: 構造体の型名
    initial_value: str = ""           # v5.0.0: 初期値（ソースから抽出）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'var_type': self.var_type,
            'is_extern': self.is_extern,
            'definition': self.definition,
            'is_static': self.is_static,
            'is_array': self.is_array,
            'array_size': self.array_size,
            'is_struct': self.is_struct,
            'struct_type': self.struct_type,
            'initial_value': self.initial_value
        }


@dataclass
class LocalVariableInfo:
    """ローカル変数情報 (v4.2.0で追加, v4.3.2でループ変数対応)"""
    name: str
    var_type: str
    scope: str  # 関数名やブロック識別
    line_number: int = 0
    is_initialized: bool = False
    initial_value: str = ""
    is_loop_variable: bool = False  # v4.3.2: for文等のループ変数かどうか
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'var_type': self.var_type,
            'scope': self.scope,
            'line_number': self.line_number,
            'is_initialized': self.is_initialized,
            'initial_value': self.initial_value,
            'is_loop_variable': self.is_loop_variable
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
class FunctionPointerTable:
    """関数ポインタテーブル情報 (v4.7で追加)"""
    name: str                              # テーブル名
    storage: str                           # static/extern/なし
    return_type: str                       # 戻り値の型
    params: str                            # パラメータリスト（文字列）
    param_types: List[str] = field(default_factory=list)  # パラメータの型リスト
    functions: List[str] = field(default_factory=list)    # 登録されている関数名
    size: Optional[int] = None             # 配列サイズ（指定がある場合）
    line_number: int = 0                   # ソースコード内の行番号
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'storage': self.storage,
            'return_type': self.return_type,
            'params': self.params,
            'param_types': self.param_types,
            'functions': self.functions,
            'size': self.size,
            'line_number': self.line_number
        }
    
    def format_declaration(self) -> str:
        """テーブル宣言を生成"""
        storage_prefix = f"{self.storage} " if self.storage else ""
        return f"{storage_prefix}{self.return_type} (*{self.name}[])({self.params})"
    
    def format_definition(self) -> str:
        """テーブル定義全体を生成（初期化子付き）"""
        decl = self.format_declaration()
        func_refs = ",\n    ".join(f"&{func}" for func in self.functions)
        return f"{decl} = {{\n    {func_refs}\n}};"


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
    function_signatures: Dict[str, 'FunctionSignature'] = field(default_factory=dict)  # v4.0: 関数シグネチャ
    local_variables: Dict[str, 'LocalVariableInfo'] = field(default_factory=dict)  # v4.2.0: ローカル変数情報
    function_pointer_tables: List['FunctionPointerTable'] = field(default_factory=list)  # v4.7: 関数ポインタテーブル
    static_variables: List['VariableDeclInfo'] = field(default_factory=list)  # v5.0.0: static変数詳細情報
    global_variable_infos: List['VariableDeclInfo'] = field(default_factory=list)  # v5.0.0: グローバル変数詳細情報
    
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
            'struct_definitions': [s.to_dict() for s in self.struct_definitions],
            'function_signatures': {k: v.to_dict() for k, v in self.function_signatures.items()},  # v4.0
            'function_pointer_tables': [t.to_dict() for t in self.function_pointer_tables],  # v4.7
            'static_variables': [v.to_dict() for v in self.static_variables],  # v5.0.0
            'global_variable_infos': [v.to_dict() for v in self.global_variable_infos]  # v5.0.0
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
