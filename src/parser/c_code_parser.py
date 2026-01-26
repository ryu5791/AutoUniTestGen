"""
CCodeParserモジュール

C言語ソースコードを解析してParseDataを生成
"""

import sys
import os
import re
from typing import Optional, Dict, List

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger, read_file
from src.data_structures import ParsedData, FunctionInfo, FunctionSignature, LocalVariableInfo
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
            
            # 6. 外部関数を抽出（v4.0.1: 標準ライブラリ関数を除外）
            external_functions = self._extract_external_functions(
                conditions, ast, target_function or (function_info.name if function_info else None),
                source_code=code  # v4.0.1: ソースコードを渡す
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
            
            # 11.7. v4.0: 関数シグネチャを抽出
            function_signatures = self._extract_function_signatures(ast, code)
            self.logger.info(f"{len(function_signatures)}個の関数シグネチャを抽出しました")
            
            # 11.8. v4.2.0: ローカル変数を抽出
            local_variables = self._extract_local_variables(
                code, 
                target_function or (function_info.name if function_info else "")
            )
            self.logger.info(f"{len(local_variables)}個のローカル変数を抽出しました")
            
            # 11.9. v4.7: 関数ポインタテーブルを抽出
            function_pointer_tables = self.variable_extractor.extract_function_pointer_tables(code)
            self.logger.info(f"{len(function_pointer_tables)}個の関数ポインタテーブルを抽出しました")
            
            # 11.10. v4.7: 関数ポインタテーブル内の関数を外部関数として追加登録
            table_functions, table_signatures = self._register_function_table_entries(
                function_pointer_tables, function_signatures
            )
            external_functions = list(set(external_functions) | table_functions)
            function_signatures.update(table_signatures)
            self.logger.info(f"関数ポインタテーブルから{len(table_functions)}個の関数を登録しました")
            
            # 11.11. v5.0.0: static変数とグローバル変数の詳細情報を抽出
            static_variables, global_variable_infos = self._extract_variable_details(ast, code)
            self.logger.info(f"{len(static_variables)}個のstatic変数、{len(global_variable_infos)}個のグローバル変数詳細を抽出しました")
            
            # 11.12. v5.1.2: 関数の最終return値を取得
            function_final_return = getattr(extractor, 'function_final_return', None)
            
            # 11.13. v5.1.4 Phase 3: 全return文を取得
            all_return_statements = getattr(extractor, 'all_return_statements', [])
            
            # 11.14. v5.1.6 Phase 4: ローカル変数の代入元関数を取得
            local_var_assignments = getattr(extractor, 'local_var_assignments', {})
            
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
                struct_definitions=struct_definitions,  # v2.8.0: 追加
                function_signatures=function_signatures,  # v4.0: 追加
                local_variables=local_variables,  # v4.2.0: 追加
                function_pointer_tables=function_pointer_tables,  # v4.7: 追加
                static_variables=static_variables,  # v5.0.0: 追加
                global_variable_infos=global_variable_infos,  # v5.0.0: 追加
                function_final_return=function_final_return,  # v5.1.2: 追加
                all_return_statements=all_return_statements,  # v5.1.4: 追加
                local_var_assignments=local_var_assignments  # v5.1.6: 追加
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
        
        def get_type_str(type_node) -> str:
            """型ノードから型文字列を取得（const修飾子、ポインタ対応）"""
            if isinstance(type_node, c_ast.TypeDecl):
                # const修飾子を取得
                quals = getattr(type_node, 'quals', []) or []
                base_type = get_type_str(type_node.type)
                if 'const' in quals:
                    return f'const {base_type}'
                return base_type
            elif isinstance(type_node, c_ast.IdentifierType):
                return ' '.join(type_node.names)
            elif isinstance(type_node, c_ast.PtrDecl):
                # ポインタの場合、const修飾子をチェック
                quals = getattr(type_node, 'quals', []) or []
                base_type = get_type_str(type_node.type)
                ptr_type = base_type + '*'
                if 'const' in quals:
                    ptr_type = ptr_type + ' const'
                return ptr_type
            elif isinstance(type_node, c_ast.ArrayDecl):
                return get_type_str(type_node.type) + '*'
            elif isinstance(type_node, c_ast.Struct):
                # 構造体型
                return f'struct {type_node.name}' if type_node.name else 'struct'
            elif isinstance(type_node, c_ast.Enum):
                # 列挙型
                return f'enum {type_node.name}' if type_node.name else 'enum'
            elif isinstance(type_node, c_ast.FuncDecl):
                # 関数ポインタ型
                return 'void*'  # 簡易実装
            else:
                return 'int'
        
        class FunctionInfoVisitor(c_ast.NodeVisitor):
            def __init__(self, target):
                self.target = target
                self.func_info = None
            
            def visit_FuncDef(self, node):
                func_name = node.decl.name
                
                # 対象関数をチェック
                if self.target is None or func_name == self.target:
                    # 戻り値の型を取得（ポインタ対応）
                    return_type = "void"
                    if hasattr(node.decl.type, 'type'):
                        return_type = get_type_str(node.decl.type.type)
                    
                    # パラメータを取得
                    parameters = []
                    if node.decl.type.args:
                        for param in node.decl.type.args.params:
                            if hasattr(param, 'name') and param.name:
                                # v4.8.5: 正確な型取得（const char* 等に対応）
                                param_type = get_type_str(param.type) if hasattr(param, 'type') else 'int'
                                # void型単独の場合はスキップ
                                if param_type == 'void' and (param.name is None or param.name == ''):
                                    continue
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
    
    def _extract_external_functions(self, conditions, ast, target_function: Optional[str] = None,
                                      source_code: str = None) -> list:
        """
        外部関数を抽出（条件式と関数本体の両方から）
        
        v4.0.1: 標準ライブラリ関数を除外
        v4.1.1: 関数マクロ（引数ありマクロ）を除外
        
        Args:
            conditions: 条件分岐リスト
            ast: AST
            target_function: 対象関数名
            source_code: ソースコード（標準ライブラリ関数除外用）
        
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
                if self.in_target_function:
                    # 通常の関数呼び出し（node.name が ID の場合）
                    if hasattr(node.name, 'name'):
                        self.function_calls.add(node.name.name)
                    # 配列経由の関数ポインタ呼び出し（node.name が ArrayRef の場合）
                    # p_event_ctrldet_first[index](param) のような場合はスキップ
                    # （テーブル内の関数は別途登録される）
                self.generic_visit(node)
        
        visitor = FunctionCallVisitor(target_function)
        visitor.visit(ast)
        functions.update(visitor.function_calls)
        
        # 一般的なC言語キーワードと対象関数自身を除外
        keywords = {'if', 'else', 'switch', 'case', 'default', 'for', 'while', 'do', 'return'}
        functions = functions - keywords
        if target_function:
            functions.discard(target_function)
        
        # v4.1.1: 関数マクロ（引数ありマクロ）を除外
        # #define UtD30(Utx33) Utf11() のようなマクロは関数ではないため除外
        function_macro_names = self.preprocessor.get_function_macro_names()
        if function_macro_names:
            excluded_macros = functions & function_macro_names
            if excluded_macros:
                self.logger.info(f"関数マクロを外部関数から除外: {sorted(excluded_macros)}")
            functions = functions - function_macro_names
        
        # v4.0.1: 標準ライブラリ関数を除外
        # v4.7: 非文字列（ASTノード等）をフィルタリング
        functions = {f for f in functions if isinstance(f, str)}
        
        if source_code:
            try:
                from src.parser.stdlib_function_extractor import StdlibFunctionExtractor
                stdlib_extractor = StdlibFunctionExtractor()
                filtered_functions = stdlib_extractor.filter_external_functions(
                    list(functions), source_code
                )
                return sorted(filtered_functions)
            except Exception as e:
                self.logger.warning(f"標準ライブラリ関数の除外に失敗: {e}")
        
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
    
    def _extract_variable_details(self, ast, source_code: str) -> tuple:
        """
        グローバル変数とstatic変数の詳細情報を抽出 (v5.0.0)
        
        Args:
            ast: AST
            source_code: ソースコード
        
        Returns:
            (static_variables, global_variable_infos) のタプル
        """
        from pycparser import c_ast
        from src.data_structures import VariableDeclInfo
        
        static_vars = []
        global_vars = []
        
        class DetailedVarVisitor(c_ast.NodeVisitor):
            def __init__(self, source):
                self.source = source
                self.static_variables = []
                self.global_variables = []
                self.in_function = False
                self.current_function = None
                self.in_struct = False  # 構造体定義内かどうか
            
            def visit_FuncDef(self, node):
                # 関数内部の処理
                old_in_function = self.in_function
                old_function = self.current_function
                self.in_function = True
                self.current_function = node.decl.name if node.decl else None
                self.generic_visit(node)
                self.in_function = old_in_function
                self.current_function = old_function
            
            def visit_Struct(self, node):
                # 構造体定義内は処理しない（メンバーを変数として抽出しない）
                old_in_struct = self.in_struct
                self.in_struct = True
                self.generic_visit(node)
                self.in_struct = old_in_struct
            
            def visit_Decl(self, node):
                # 構造体定義内のメンバーは除外
                if self.in_struct:
                    self.generic_visit(node)
                    return
                
                if node.name and not isinstance(node.type, c_ast.FuncDecl):
                    # 変数宣言のみ処理
                    is_static = 'static' in (node.storage or [])
                    is_extern = 'extern' in (node.storage or [])
                    
                    # 関数内のstatic変数は外部からアクセスできないので除外
                    if self.in_function:
                        # 関数内のstatic変数はスコープ外からアクセスできないので収集しない
                        self.generic_visit(node)
                        return
                    
                    # 型情報を取得
                    var_type = self._get_type_string(node.type)
                    is_array = isinstance(node.type, c_ast.ArrayDecl)
                    array_size = self._get_array_size(node.type) if is_array else None
                    is_struct = 'struct' in var_type or self._is_struct_type(node.type)
                    struct_type = self._get_struct_type(node.type) if is_struct else ""
                    
                    # 初期値を取得
                    initial_value = self._get_initial_value(node.init) if node.init else ""
                    
                    # 定義文を生成
                    definition = self._generate_definition(node, var_type, is_array, array_size)
                    
                    var_info = VariableDeclInfo(
                        name=node.name,
                        var_type=var_type,
                        is_extern=is_extern,
                        definition=definition,
                        is_static=is_static,
                        is_array=is_array,
                        array_size=array_size,
                        is_struct=is_struct,
                        struct_type=struct_type,
                        initial_value=initial_value
                    )
                    
                    # グローバルスコープの変数を収集
                    # v5.0.2: extern変数も含める（テスト時にリセットするため）
                    if is_static:
                        self.static_variables.append(var_info)
                    else:
                        # extern変数も含めてglobal_variablesに追加
                        self.global_variables.append(var_info)
                
                self.generic_visit(node)
            
            def _get_type_string(self, node) -> str:
                """型ノードから型文字列を取得"""
                if isinstance(node, c_ast.TypeDecl):
                    return self._get_type_string(node.type)
                elif isinstance(node, c_ast.IdentifierType):
                    return ' '.join(node.names)
                elif isinstance(node, c_ast.PtrDecl):
                    return self._get_type_string(node.type) + '*'
                elif isinstance(node, c_ast.ArrayDecl):
                    return self._get_type_string(node.type)
                elif isinstance(node, c_ast.Struct):
                    return f"struct {node.name}" if node.name else "struct"
                elif isinstance(node, c_ast.Enum):
                    return f"enum {node.name}" if node.name else "enum"
                else:
                    return "unknown"
            
            def _get_array_size(self, node) -> int:
                """配列サイズを取得"""
                if isinstance(node, c_ast.ArrayDecl):
                    if node.dim:
                        if isinstance(node.dim, c_ast.Constant):
                            try:
                                return int(node.dim.value)
                            except:
                                return 0
                return 0
            
            def _is_struct_type(self, node) -> bool:
                """構造体型かどうか判定"""
                if isinstance(node, c_ast.TypeDecl):
                    return self._is_struct_type(node.type)
                elif isinstance(node, c_ast.Struct):
                    return True
                elif isinstance(node, c_ast.ArrayDecl):
                    return self._is_struct_type(node.type)
                elif isinstance(node, c_ast.PtrDecl):
                    return self._is_struct_type(node.type)
                return False
            
            def _get_struct_type(self, node) -> str:
                """構造体の型名を取得"""
                if isinstance(node, c_ast.TypeDecl):
                    return self._get_struct_type(node.type)
                elif isinstance(node, c_ast.Struct):
                    return node.name if node.name else ""
                elif isinstance(node, c_ast.ArrayDecl):
                    return self._get_struct_type(node.type)
                elif isinstance(node, c_ast.PtrDecl):
                    return self._get_struct_type(node.type)
                elif isinstance(node, c_ast.IdentifierType):
                    # typedef名の場合
                    return ' '.join(node.names)
                return ""
            
            def _get_initial_value(self, init_node) -> str:
                """初期値を文字列で取得"""
                if init_node is None:
                    return ""
                if isinstance(init_node, c_ast.Constant):
                    return init_node.value
                elif isinstance(init_node, c_ast.InitList):
                    # 配列・構造体の初期化リスト
                    values = []
                    for expr in init_node.exprs:
                        values.append(self._get_initial_value(expr))
                    return "{" + ", ".join(values) + "}"
                elif isinstance(init_node, c_ast.UnaryOp):
                    return init_node.op + self._get_initial_value(init_node.expr)
                elif isinstance(init_node, c_ast.BinaryOp):
                    return f"{self._get_initial_value(init_node.left)} {init_node.op} {self._get_initial_value(init_node.right)}"
                elif isinstance(init_node, c_ast.ID):
                    return init_node.name
                elif isinstance(init_node, c_ast.NamedInitializer):
                    # .member = value 形式
                    names = [n.name if hasattr(n, 'name') else str(n) for n in init_node.name]
                    return f".{'.'.join(names)} = {self._get_initial_value(init_node.expr)}"
                else:
                    return str(init_node)
            
            def _generate_definition(self, node, var_type: str, is_array: bool, array_size: int) -> str:
                """変数定義文を生成"""
                storage = ' '.join(node.storage) + ' ' if node.storage else ''
                if is_array and array_size:
                    return f"{storage}{var_type} {node.name}[{array_size}];"
                elif is_array:
                    return f"{storage}{var_type} {node.name}[];"
                else:
                    return f"{storage}{var_type} {node.name};"
        
        visitor = DetailedVarVisitor(source_code)
        visitor.visit(ast)
        
        return visitor.static_variables, visitor.global_variables
    
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
    
    def _extract_function_signatures(self, ast, source_code: str) -> Dict[str, FunctionSignature]:
        """
        関数宣言からシグネチャを抽出（v4.0）
        
        Args:
            ast: pycparser AST（Noneの場合は正規表現フォールバック）
            source_code: ソースコード文字列
        
        Returns:
            Dict[関数名, FunctionSignature]
        """
        from pycparser import c_ast
        
        signatures = {}
        
        # AST解析を試みる
        if ast is not None:
            class SignatureVisitor(c_ast.NodeVisitor):
                def __init__(self):
                    self.sigs = {}
                
                def visit_Decl(self, node):
                    # 関数宣言（プロトタイプ）を処理
                    if isinstance(node.type, c_ast.FuncDecl):
                        func_name = node.name
                        if func_name:
                            sig = self._extract_from_func_decl(node)
                            if sig:
                                self.sigs[func_name] = sig
                    self.generic_visit(node)
                
                def _extract_from_func_decl(self, node) -> Optional[FunctionSignature]:
                    func_decl = node.type
                    
                    # 戻り値型
                    return_type = self._get_type_str(func_decl.type)
                    
                    # パラメータ
                    parameters = []
                    if func_decl.args and func_decl.args.params:
                        for i, param in enumerate(func_decl.args.params):
                            if hasattr(param, 'name') and hasattr(param, 'type'):
                                param_type = self._get_type_str(param.type)
                                param_name = param.name
                                # void型単独の場合はスキップ（パラメータリスト全体が (void) の場合）
                                if param_type == 'void' and (param_name is None or param_name == ''):
                                    continue
                                # パラメータ名がNoneの場合はデフォルト名を付与
                                if param_name is None:
                                    param_name = f"arg{i}"
                                parameters.append({
                                    "type": param_type,
                                    "name": param_name
                                })
                    
                    # static修飾子
                    is_static = 'static' in (node.storage or [])
                    
                    return FunctionSignature(
                        name=node.name,
                        return_type=return_type,
                        parameters=parameters,
                        is_static=is_static
                    )
                
                def _get_type_str(self, type_node) -> str:
                    """型ノードから型文字列を取得（v4.3.4: const修飾子対応）"""
                    if isinstance(type_node, c_ast.TypeDecl):
                        # const修飾子を取得
                        quals = getattr(type_node, 'quals', []) or []
                        base_type = self._get_type_str(type_node.type)
                        if 'const' in quals:
                            return f'const {base_type}'
                        return base_type
                    elif isinstance(type_node, c_ast.IdentifierType):
                        return ' '.join(type_node.names)
                    elif isinstance(type_node, c_ast.PtrDecl):
                        # ポインタの場合、const修飾子をチェック
                        quals = getattr(type_node, 'quals', []) or []
                        base_type = self._get_type_str(type_node.type)
                        ptr_type = base_type + ' *'
                        if 'const' in quals:
                            ptr_type = ptr_type + ' const'
                        return ptr_type
                    elif isinstance(type_node, c_ast.ArrayDecl):
                        return self._get_type_str(type_node.type) + '*'
                    else:
                        return 'int'
            
            visitor = SignatureVisitor()
            visitor.visit(ast)
            signatures = visitor.sigs
        
        # 正規表現フォールバック（AST解析できなかった関数用）
        regex_sigs = self._extract_signatures_regex(source_code)
        for name, sig in regex_sigs.items():
            if name not in signatures:
                signatures[name] = sig
                self.logger.debug(f"正規表現フォールバックでシグネチャ抽出: {name}")
        
        return signatures
    
    def _extract_signatures_regex(self, source_code: str) -> Dict[str, FunctionSignature]:
        """正規表現でプロトタイプ宣言からシグネチャを抽出（フォールバック）"""
        signatures = {}
        
        # プロトタイプ宣言パターン
        # static? 戻り値型 関数名(パラメータ);
        pattern = r'^(?:(static)\s+)?(\w+(?:\s*\*)?)\s+(\w+)\s*\(([^)]*)\)\s*;'
        
        for match in re.finditer(pattern, source_code, re.MULTILINE):
            is_static = match.group(1) is not None
            return_type = match.group(2).strip()
            func_name = match.group(3).strip()
            params_str = match.group(4).strip()
            
            parameters = []
            if params_str and params_str.lower() != 'void':
                for param in params_str.split(','):
                    param = param.strip()
                    if not param:
                        continue
                    # "uint8_t value" → type="uint8_t", name="value"
                    # "uint8_t *ptr" → type="uint8_t*", name="ptr"
                    parts = param.rsplit(' ', 1)
                    if len(parts) == 2:
                        ptype = parts[0].strip()
                        pname = parts[1].strip()
                        # ポインタ記号の正規化
                        if pname.startswith('*'):
                            ptype += '*'
                            pname = pname[1:]
                        parameters.append({
                            "type": ptype,
                            "name": pname
                        })
            
            signatures[func_name] = FunctionSignature(
                name=func_name,
                return_type=return_type,
                parameters=parameters,
                is_static=is_static
            )
        
        return signatures
    
    def _extract_local_variables(self, source_code: str, function_name: str) -> Dict[str, LocalVariableInfo]:
        """
        ローカル変数を抽出 (v4.2.0で追加, v4.3.2でfor文内変数宣言対応)
        
        Args:
            source_code: ソースコード
            function_name: 対象関数名
        
        Returns:
            Dict[変数名, LocalVariableInfo]
        """
        local_vars = {}
        
        if not function_name:
            return local_vars
        
        # 関数本体を抽出
        # パターン: static? 戻り値型 関数名(パラメータ) { ... }
        func_pattern = rf'(?:static\s+)?\w+(?:\s*\*)?[^{{;]*?\b{re.escape(function_name)}\s*\([^)]*\)\s*\{{'
        
        match = re.search(func_pattern, source_code, re.MULTILINE)
        if not match:
            return local_vars
        
        start = match.end()
        
        # 対応する閉じ括弧を探す
        brace_count = 1
        end = start
        for i in range(start, len(source_code)):
            if source_code[i] == '{':
                brace_count += 1
            elif source_code[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i
                    break
        
        function_body = source_code[start:end]
        
        # ローカル変数宣言パターン
        # 型名 変数名 [= 初期値];
        # 例: Utx10 Utx73;
        #     Utx189 Utx125 = {0};
        #     uint8_t Utv17 = UCHAR_MAX;
        #     bool Utx68 = false;
        local_var_pattern = r'(?:^|\n|\{)\s*(\w+(?:\s+\w+)?)\s+(\w+)\s*(?:=\s*([^;]+?))?\s*;'
        
        # C言語キーワードを除外するためのセット
        keywords = {'if', 'else', 'for', 'while', 'switch', 'case', 'default', 
                   'return', 'break', 'continue', 'goto', 'sizeof', 'typedef',
                   'extern', 'static', 'const', 'volatile', 'register'}
        
        # 基本型セット
        basic_types = {'int', 'char', 'short', 'long', 'float', 'double', 'void',
                      'unsigned', 'signed', 'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
                      'int8_t', 'int16_t', 'int32_t', 'int64_t', 'bool', 'size_t'}
        
        lines = function_body.split('\n')
        for line_no, line in enumerate(lines, 1):
            # コメントを除去
            line_clean = re.sub(r'//.*$', '', line)
            line_clean = re.sub(r'/\*.*?\*/', '', line_clean)
            
            # v4.3.2: for文内の変数宣言を抽出（for文を完全にスキップしない）
            for_var_match = re.search(r'for\s*\(\s*(\w+(?:\s+\w+)?)\s+(\w+)\s*=\s*([^;]+)', line_clean)
            if for_var_match:
                type_name = for_var_match.group(1).strip()
                var_name = for_var_match.group(2).strip()
                init_value = for_var_match.group(3).strip()
                
                # キーワードチェック
                if type_name.lower() not in keywords and var_name.lower() not in keywords:
                    # 型名が有効かチェック
                    if re.match(r'^[A-Za-z_]', type_name):
                        # 変数名が有効かチェック
                        if re.match(r'^[A-Za-z_]\w*$', var_name):
                            local_vars[var_name] = LocalVariableInfo(
                                name=var_name,
                                var_type=type_name,
                                scope=function_name,
                                line_number=line_no,
                                is_initialized=True,
                                initial_value=init_value,
                                is_loop_variable=True  # v4.3.2: ループ変数フラグ
                            )
                            self.logger.debug(f"for文内ループ変数を検出: {var_name} (型: {type_name})")
                # for文の行は通常のパターンではスキップ
                continue
            
            # 関数呼び出しは除外
            if re.search(r'\w+\s*\([^)]*\)\s*;', line_clean) and '=' not in line_clean:
                continue
            
            # 型名+変数名のパターンを検索
            for match in re.finditer(local_var_pattern, line_clean):
                type_name = match.group(1).strip()
                var_name = match.group(2).strip()
                init_value = match.group(3).strip() if match.group(3) else ""
                
                # キーワードチェック
                if type_name.lower() in keywords or var_name.lower() in keywords:
                    continue
                
                # 型名が有効かチェック（アルファベットで始まる）
                if not re.match(r'^[A-Za-z_]', type_name):
                    continue
                
                # 変数名が有効かチェック
                if not re.match(r'^[A-Za-z_]\w*$', var_name):
                    continue
                
                # 制御構造キーワードを除外
                if var_name in keywords:
                    continue
                
                local_vars[var_name] = LocalVariableInfo(
                    name=var_name,
                    var_type=type_name,
                    scope=function_name,
                    line_number=line_no,
                    is_initialized=bool(init_value),
                    initial_value=init_value
                )
        
        self.logger.info(f"ローカル変数抽出完了: {list(local_vars.keys())}")
        return local_vars
    
    def _register_function_table_entries(self, tables: List, 
                                          existing_signatures: Dict[str, FunctionSignature]
                                         ) -> tuple:
        """
        関数ポインタテーブル内の関数を外部関数として登録 (v4.7新規)
        
        Args:
            tables: 関数ポインタテーブルのリスト
            existing_signatures: 既存の関数シグネチャ辞書
        
        Returns:
            (追加された関数名のセット, 新しいシグネチャ辞書)
        """
        new_functions = set()
        new_signatures = {}
        
        for table in tables:
            for func_name in table.functions:
                # 既に登録されていない場合のみ追加
                if func_name not in existing_signatures:
                    # パラメータリストを解析
                    parameters = []
                    if table.params and table.params != 'void':
                        param_parts = table.params.split(',')
                        for i, part in enumerate(param_parts):
                            part = part.strip()
                            if part:
                                # "uint8_t i" -> {"type": "uint8_t", "name": "i"}
                                words = part.split()
                                if len(words) >= 2:
                                    ptype = ' '.join(words[:-1])
                                    pname = words[-1]
                                else:
                                    ptype = words[0] if words else 'int'
                                    pname = f'arg{i}'
                                parameters.append({'type': ptype, 'name': pname})
                    
                    # シグネチャを作成
                    signature = FunctionSignature(
                        name=func_name,
                        return_type=table.return_type,
                        parameters=parameters,
                        is_static=table.storage == 'static'
                    )
                    new_signatures[func_name] = signature
                    self.logger.debug(f"関数ポインタテーブル {table.name} から関数を登録: {func_name}")
                
                new_functions.add(func_name)
        
        return new_functions, new_signatures


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
