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
                local_variables=local_variables  # v4.2.0: 追加
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
        
        # v4.1.1: 関数マクロ（引数ありマクロ）を除外
        # #define UtD30(Utx33) Utf11() のようなマクロは関数ではないため除外
        function_macro_names = self.preprocessor.get_function_macro_names()
        if function_macro_names:
            excluded_macros = functions & function_macro_names
            if excluded_macros:
                self.logger.info(f"関数マクロを外部関数から除外: {sorted(excluded_macros)}")
            functions = functions - function_macro_names
        
        # v4.0.1: 標準ライブラリ関数を除外
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
                    if isinstance(type_node, c_ast.TypeDecl):
                        return self._get_type_str(type_node.type)
                    elif isinstance(type_node, c_ast.IdentifierType):
                        return ' '.join(type_node.names)
                    elif isinstance(type_node, c_ast.PtrDecl):
                        return self._get_type_str(type_node.type) + '*'
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
        ローカル変数を抽出 (v4.2.0で追加)
        
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
            
            # for文の初期化部分は除外
            if re.match(r'\s*for\s*\(', line_clean):
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
        
        return local_vars


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
