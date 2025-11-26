"""
CCodeParserモジュール

C言語ソースコードを解析してParseDataを生成
"""

import sys
import os
import re
from typing import Optional, Dict

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger, read_file
from src.data_structures import ParsedData, FunctionInfo
from src.parser.preprocessor import Preprocessor
from src.parser.ast_builder import ASTBuilder
from src.parser.condition_extractor import ConditionExtractor
from src.parser.typedef_extractor import TypedefExtractor  # v2.2: 追加
from src.parser.variable_decl_extractor import VariableDeclExtractor  # v2.2: 追加


class CCodeParser:
    """C言語コードパーサー"""
    
    def __init__(self, defines: Dict[str, str] = None, include_paths: list = None, enable_includes: bool = False):
        """
        初期化
        
        Args:
            defines: 事前定義するマクロ辞書 {マクロ名: 値}
            include_paths: インクルードパスのリスト
            enable_includes: ヘッダーファイルの読み込みを有効化するか
        """
        self.logger = setup_logger(__name__)
        self.preprocessor = Preprocessor(
            defines=defines,
            include_paths=include_paths,
            enable_includes=enable_includes
        )
        self.ast_builder = ASTBuilder()
        self.typedef_extractor = TypedefExtractor()  # v2.2: 追加
        self.variable_extractor = VariableDeclExtractor()  # v2.2: 追加
    
    def parse(self, c_file_path: str, target_function: Optional[str] = None) -> Optional[ParsedData]:
        """
        C言語ファイルを解析
        
        Args:
            c_file_path: C言語ファイルのパス
            target_function: 対象関数名（Noneの場合は自動検出）
        
        Returns:
            ParsedData（失敗時はNone）
        """
        try:
            self.logger.info(f"C言語ファイルの解析を開始: {c_file_path}")
            
            # 1. ファイルを読み込み（自動エンコーディング検出）
            code = read_file(c_file_path, encoding='auto')
            
            # 2. 前処理
            preprocessed_code = self.preprocessor.preprocess(code)
            
            # 3. ASTを構築
            ast = self.ast_builder.build_ast(preprocessed_code)
            
            if ast is None:
                self.logger.error("AST構築に失敗")
                self.logger.warning("フォールバックモード: 元のソースから直接定義を抽出します")
                
                # v2.4.2: フォールバックモード - 元のソースから直接抽出
                from src.parser.source_definition_extractor import SourceDefinitionExtractor
                extractor = SourceDefinitionExtractor()
                definitions = extractor.extract_all_definitions(code)
                
                # ParsedDataを構築（最小限の情報）
                parsed_data = ParsedData(
                    file_name=os.path.basename(c_file_path),
                    function_name=target_function or "",
                    conditions=[],
                    external_functions=[],
                    global_variables=[],
                    function_info=None,
                    enums={},
                    enum_values=[],
                    bitfields={},
                    typedefs=[],
                    variables=[],
                    macros=definitions['macros'],
                    macro_definitions=definitions['macro_definitions']
                )
                
                # 型定義もTypedefInfo形式に変換
                from src.data_structures import TypedefInfo
                for i, typedef_def in enumerate(definitions['typedef_definitions']):
                    # 型名を抽出（最後の識別子がたいてい型名）
                    match = re.search(r'\}\s*(\w+)\s*;', typedef_def)
                    if match:
                        typename = match.group(1)
                        typedef_info = TypedefInfo(
                            name=typename,
                            typedef_type='unknown',
                            definition=typedef_def,
                            dependencies=[],
                            line_number=i
                        )
                        parsed_data.typedefs.append(typedef_info)
                
                self.logger.info(f"フォールバックモードで解析完了: {len(definitions['macro_definitions'])}個のマクロ、{len(definitions['typedef_definitions'])}個の型定義")
                return parsed_data
            
            # 4. 関数情報を抽出
            function_info = self._extract_function_info(ast, target_function)
            
            if function_info is None and target_function:
                self.logger.error(f"対象関数が見つかりません: {target_function}")
                return None
            
            # 5. 条件分岐を抽出
            extractor = ConditionExtractor(
                target_function=target_function or (function_info.name if function_info else None)
            )
            # v3.1: 元のソースコードの行を設定（括弧構造維持のため）
            extractor.set_source_lines(code.split('\n'))
            # v3.1: 行番号オフセットを設定
            extractor.set_line_offset(self.ast_builder.get_line_offset())
            conditions = extractor.extract_conditions(ast)
            
            # 6. 外部関数を抽出
            external_functions = self._extract_external_functions(
                conditions, ast, target_function or (function_info.name if function_info else None)
            )
            
            # 7. グローバル変数を抽出
            global_variables = self._extract_global_variables(ast)
            
            # 8. enum定数を抽出
            enums, enum_values = self._extract_enums(ast)
            
            # 9. ビットフィールド情報を取得
            bitfield_dict = {}
            for member_name, (struct_name, bit_width, base_type) in self.preprocessor.get_bitfields().items():
                from src.data_structures import BitFieldInfo
                bitfield_dict[member_name] = BitFieldInfo(
                    struct_name=struct_name,
                    member_name=member_name,
                    bit_width=bit_width,
                    base_type=base_type,
                    full_path=f"{struct_name}.{member_name}"
                )
            
            # 10. v2.2: 型定義を抽出
            typedefs = self.typedef_extractor.extract_typedefs(ast, code)
            self.logger.info(f"{len(typedefs)}個の型定義を抽出しました")
            
            # 11. v2.2: 変数宣言を抽出
            variables = self.variable_extractor.extract_variables(
                ast,
                target_function or (function_info.name if function_info else ""),
                conditions
            )
            self.logger.info(f"{len(variables)}個の変数宣言を抽出しました")
            
            # 11.5. v2.4.2: マクロ定義を元のソースから抽出
            from src.parser.source_definition_extractor import SourceDefinitionExtractor
            source_extractor = SourceDefinitionExtractor()
            macros, macro_definitions = source_extractor.extract_macro_definitions(code)
            self.logger.info(f"{len(macro_definitions)}個のマクロ定義を抽出しました")
            
            
            # 11.6. v2.8.0: 構造体定義を抽出
            struct_definitions = self.typedef_extractor.extract_struct_definitions(ast)
            self.logger.info(f"{len(struct_definitions)}個の構造体定義を抽出しました")
            # 12. ParsedDataを構築
            parsed_data = ParsedData(
                file_name=os.path.basename(c_file_path),
                function_name=target_function or (function_info.name if function_info else ""),
                conditions=conditions,
                external_functions=external_functions,
                global_variables=global_variables,
                function_info=function_info,
                enums=enums,
                enum_values=enum_values,
                bitfields=bitfield_dict,
                typedefs=typedefs,  # v2.2: 追加
                variables=variables,  # v2.2: 追加
                macros=macros,  # v2.4.2: 追加
                macro_definitions=macro_definitions,  # v2.4.2: 追加
                struct_definitions=struct_definitions  # v2.8.0: 追加
            )
            
            self.logger.info(f"解析完了: {len(conditions)}個の条件分岐を検出")
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"解析エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_function_info(self, ast, target_function: Optional[str] = None) -> Optional[FunctionInfo]:
        """
        関数情報を抽出
        
        Args:
            ast: AST
            target_function: 対象関数名
        
        Returns:
            FunctionInfo
        """
        from pycparser import c_ast
        
        class FunctionInfoVisitor(c_ast.NodeVisitor):
            def __init__(self, target):
                self.target = target
                self.func_info = None
            
            def visit_FuncDef(self, node):
                func_name = node.decl.name
                
                # 対象関数をチェック
                if self.target is None or func_name == self.target:
                    # 戻り値の型を取得
                    return_type = "void"
                    if hasattr(node.decl.type, 'type'):
                        type_node = node.decl.type.type
                        if hasattr(type_node, 'names'):
                            return_type = ' '.join(type_node.names)
                        elif hasattr(type_node, 'type') and hasattr(type_node.type, 'names'):
                            # ポインタ型などの場合
                            return_type = ' '.join(type_node.type.names)
                            if hasattr(type_node, 'quals') and type_node.quals:
                                return_type = ' '.join(type_node.quals) + ' ' + return_type
                            # ポインタの数を追加
                            ptr_count = 0
                            temp = type_node
                            while hasattr(temp, 'type'):
                                if temp.__class__.__name__ == 'PtrDecl':
                                    ptr_count += 1
                                temp = temp.type if hasattr(temp, 'type') else None
                                if temp is None:
                                    break
                            return_type += '*' * ptr_count
                    
                    # パラメータを取得
                    parameters = []
                    if node.decl.type.args:
                        for param in node.decl.type.args.params:
                            if hasattr(param, 'name') and param.name:
                                param_type = "int"  # 簡易実装
                                if hasattr(param, 'type'):
                                    if hasattr(param.type, 'type') and hasattr(param.type.type, 'names'):
                                        param_type = ' '.join(param.type.type.names)
                                parameters.append({
                                    'name': param.name,
                                    'type': param_type
                                })
                    
                    self.func_info = FunctionInfo(
                        name=func_name,
                        return_type=return_type,
                        parameters=parameters
                    )
                    
                    if self.target is None:
                        # 最初の関数を返す
                        return
        
        visitor = FunctionInfoVisitor(target_function)
        visitor.visit(ast)
        
        return visitor.func_info
    
    def _extract_external_functions(self, conditions, ast, target_function: Optional[str] = None) -> list:
        """
        外部関数を抽出（条件式と関数本体の両方から）
        
        Args:
            conditions: 条件分岐リスト
            ast: AST
            target_function: 対象関数名
        
        Returns:
            外部関数名のリスト
        """
        from src.utils import extract_all_function_names
        from pycparser import c_ast
        
        functions = set()
        
        # 1. 条件式から関数名を抽出
        for cond in conditions:
            func_names = extract_all_function_names(cond.expression)
            functions.update(func_names)
        
        # 2. 関数本体から関数呼び出しを抽出
        class FunctionCallVisitor(c_ast.NodeVisitor):
            def __init__(self, target):
                self.target = target
                self.in_target_function = False
                self.function_calls = set()
            
            def visit_FuncDef(self, node):
                func_name = node.decl.name
                if self.target is None or func_name == self.target:
                    self.in_target_function = True
                    self.generic_visit(node)
                    self.in_target_function = False
            
            def visit_FuncCall(self, node):
                if self.in_target_function and hasattr(node.name, 'name'):
                    self.function_calls.add(node.name.name)
                self.generic_visit(node)
        
        visitor = FunctionCallVisitor(target_function)
        visitor.visit(ast)
        functions.update(visitor.function_calls)
        
        # 一般的なC言語キーワードと対象関数自身を除外
        keywords = {'if', 'else', 'switch', 'case', 'default', 'for', 'while', 'do', 'return'}
        functions = functions - keywords
        if target_function:
            functions.discard(target_function)
        
        return sorted(list(functions))
    
    def _extract_global_variables(self, ast) -> list:
        """
        グローバル変数を抽出
        
        Args:
            ast: AST
        
        Returns:
            グローバル変数名のリスト
        """
        from pycparser import c_ast
        
        class GlobalVarVisitor(c_ast.NodeVisitor):
            def __init__(self):
                self.variables = []
                self.in_function = False
            
            def visit_FuncDef(self, node):
                # 関数内部はスキップ
                self.in_function = True
                self.generic_visit(node)
                self.in_function = False
            
            def visit_Decl(self, node):
                if not self.in_function and node.name:
                    # 関数宣言でない場合のみ
                    if not isinstance(node.type, c_ast.FuncDecl):
                        self.variables.append(node.name)
                self.generic_visit(node)
        
        visitor = GlobalVarVisitor()
        visitor.visit(ast)
        
        return visitor.variables
    
    def _extract_enums(self, ast) -> tuple:
        """
        enum定数を抽出
        
        Args:
            ast: AST
        
        Returns:
            (enum辞書, enum値リスト)のタプル
            enum辞書: {enum型名: [定数リスト]}
            enum値リスト: すべてのenum定数のリスト
        """
        from pycparser import c_ast
        
        enums = {}
        enum_values = []
        
        class EnumVisitor(c_ast.NodeVisitor):
            def __init__(self):
                self.enums = {}
                self.enum_values = []
            
            def visit_Enum(self, node):
                # enum定義の処理
                enum_name = node.name if node.name else "anonymous"
                
                if node.values:
                    constants = []
                    for enumerator in node.values.enumerators:
                        const_name = enumerator.name
                        constants.append(const_name)
                        self.enum_values.append(const_name)
                    
                    if enum_name != "anonymous":
                        self.enums[enum_name] = constants
                
                self.generic_visit(node)
        
        visitor = EnumVisitor()
        visitor.visit(ast)
        
        return visitor.enums, visitor.enum_values


if __name__ == "__main__":
    # CCodeParserのテスト
    print("=== CCodeParser のテスト ===\n")
    
    # テスト用サンプルファイルを作成
    sample_code = """
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;

typedef enum {
    m46 = 0,
    m47,
    m48,
    mx2
} mx26;

uint16_t f4(void);
mx26 mx27(void);
void mx31(int param);

mx26 mx63;
uint16_t v9;

void f1(void) {
    if ((f4() & 223) != 0) {
        v9 = 7;
    }
    
    if ((mx63 == m47) || (mx63 == m46)) {
        mx63 = mx27();
        if ((mx63 == m48) || (mx63 == mx2)) {
            mx31(64);
        }
    }
    
    switch (v9) {
        case 0:
            break;
        case 1:
            break;
        default:
            break;
    }
}
"""
    
    # テストファイルに書き込み
    test_file = "/tmp/test_parse.c"
    with open(test_file, 'w') as f:
        f.write(sample_code)
    
    # パーサーでテスト
    parser = CCodeParser()
    parsed_data = parser.parse(test_file, target_function="f1")
    
    if parsed_data:
        print("✓ 解析成功！\n")
        print(f"ファイル名: {parsed_data.file_name}")
        print(f"関数名: {parsed_data.function_name}")
        print(f"条件分岐数: {len(parsed_data.conditions)}")
        print(f"外部関数: {parsed_data.external_functions}")
        print(f"グローバル変数: {parsed_data.global_variables}")
        
        print("\n=== 検出された条件分岐 ===")
        for i, cond in enumerate(parsed_data.conditions, 1):
            print(f"{i}. [{cond.type.value}] {cond.expression}")
            if cond.operator:
                print(f"   左辺: {cond.left}")
                print(f"   右辺: {cond.right}")
            if cond.cases:
                print(f"   cases: {cond.cases}")
        
        print("\n✓ CCodeParserが正常に動作しました")
    else:
        print("❌ 解析に失敗しました")
