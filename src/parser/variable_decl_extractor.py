"""
VariableDeclExtractorモジュール

テスト対象関数で使用される変数宣言を抽出する
v4.7: 関数ポインタテーブルの抽出機能を追加
"""

import re
import sys
import os
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger

try:
    from pycparser import c_ast
except ImportError:
    c_ast = None


@dataclass
class VariableDeclInfo:
    """変数宣言情報"""
    name: str
    var_type: str
    is_extern: bool
    definition: str


class VariableDeclExtractor:
    """変数宣言抽出器"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.global_vars: Dict[str, VariableDeclInfo] = {}
    
    def extract_variables(self, ast, function_name: str, conditions: List) -> List[VariableDeclInfo]:
        """
        関数で使用される変数を抽出
        
        Args:
            ast: pycparserのAST
            function_name: 対象関数名
            conditions: 条件式のリスト
        
        Returns:
            List[VariableDeclInfo]: 変数宣言情報のリスト
        """
        # 条件式から使用されている変数名を収集
        used_vars = self._collect_used_variables(conditions)
        
        # ASTからグローバル変数を抽出
        if ast and c_ast:
            self._extract_global_vars_from_ast(ast)
        
        # 使用されている変数のうち、グローバル変数のものを選択
        result = []
        for var_name in used_vars:
            if var_name in self.global_vars:
                result.append(self.global_vars[var_name])
            else:
                # ASTから取得できなかった場合は推測で生成
                var_info = self._create_inferred_variable(var_name)
                if var_info:
                    result.append(var_info)
        
        self.logger.info(f"{len(result)}個の変数宣言を抽出しました")
        return result
    
    def _collect_used_variables(self, conditions: List) -> Set[str]:
        """
        条件式から使用されている変数名を収集
        
        Args:
            conditions: 条件式のリスト
        
        Returns:
            変数名の集合
        """
        variables = set()
        
        for condition in conditions:
            # conditionオブジェクトから式を取得
            expression = getattr(condition, 'expression', '')
            if not expression:
                continue
            
            # 式から変数名を抽出（簡易版）
            # パターン: 英数字とアンダースコアの組み合わせ
            var_pattern = r'\b([A-Za-z_][A-Za-z0-9_]*)\b'
            matches = re.findall(var_pattern, expression)
            
            # 演算子、キーワード、数値を除外
            keywords = {
                'if', 'else', 'switch', 'case', 'default', 'break',
                'return', 'for', 'while', 'do', 'continue',
                'sizeof', 'typeof', 'true', 'false', 'NULL'
            }
            
            for match in matches:
                # 数値で始まるものは除外
                if match[0].isdigit():
                    continue
                # キーワードは除外
                if match in keywords:
                    continue
                # 関数呼び出しの可能性があるものは除外（後で関数名と判定）
                variables.add(match)
        
        return variables
    
    def _extract_global_vars_from_ast(self, ast):
        """
        ASTからグローバル変数を抽出
        
        Args:
            ast: pycparserのAST
        """
        if c_ast is None:
            return
        
        self._visit_ast_for_globals(ast)
    
    def _visit_ast_for_globals(self, node, depth=0):
        """
        ASTを巡回してグローバル変数を抽出
        
        Args:
            node: ASTノード
            depth: 再帰の深さ
        """
        if depth > 100:  # 無限再帰防止
            return
        
        if c_ast is None:
            return
        
        # FileASTの直下のDeclがグローバル変数
        if isinstance(node, c_ast.FileAST):
            for ext in node.ext:
                if isinstance(ext, c_ast.Decl):
                    self._process_global_decl(ext)
        
        # 子ノードを再帰的に訪問（FileASTのみ処理）
        if isinstance(node, c_ast.FileAST):
            for child_name, child in node.children():
                self._visit_ast_for_globals(child, depth + 1)
    
    def _process_global_decl(self, decl_node):
        """
        グローバル変数宣言を処理
        
        Args:
            decl_node: pycparser の Decl ノード
        """
        if c_ast is None:
            return
        
        try:
            var_name = decl_node.name
            if not var_name:
                return
            
            # 関数宣言は除外
            if isinstance(decl_node.type, c_ast.FuncDecl):
                return
            
            # 型情報を取得
            var_type = self._get_type_string(decl_node.type)
            
            # extern宣言を生成
            definition = f"extern {var_type} {var_name};"
            
            var_info = VariableDeclInfo(
                name=var_name,
                var_type=var_type,
                is_extern=True,
                definition=definition
            )
            
            self.global_vars[var_name] = var_info
        
        except Exception as e:
            self.logger.warning(f"グローバル変数処理中にエラー: {e}")
    
    def _get_type_string(self, type_node) -> str:
        """
        型ノードから型文字列を取得
        
        Args:
            type_node: 型のASTノード
        
        Returns:
            型文字列
        """
        if c_ast is None:
            return "int"
        
        try:
            if isinstance(type_node, c_ast.TypeDecl):
                return self._get_type_string(type_node.type)
            
            elif isinstance(type_node, c_ast.IdentifierType):
                return ' '.join(type_node.names)
            
            elif isinstance(type_node, c_ast.PtrDecl):
                base_type = self._get_type_string(type_node.type)
                return f"{base_type}*"
            
            elif isinstance(type_node, c_ast.ArrayDecl):
                base_type = self._get_type_string(type_node.type)
                # 配列サイズは省略
                return f"{base_type}[]"
            
            elif isinstance(type_node, c_ast.Struct):
                if type_node.name:
                    return f"struct {type_node.name}"
                return "struct"
            
            elif isinstance(type_node, c_ast.Union):
                if type_node.name:
                    return f"union {type_node.name}"
                return "union"
            
            elif isinstance(type_node, c_ast.Enum):
                if type_node.name:
                    return f"enum {type_node.name}"
                return "enum"
            
            else:
                return "int"
        
        except Exception as e:
            self.logger.warning(f"型文字列取得中にエラー: {e}")
            return "int"
    
    def _create_inferred_variable(self, var_name: str) -> Optional[VariableDeclInfo]:
        """
        推測で変数宣言情報を作成
        
        Args:
            var_name: 変数名
        
        Returns:
            VariableDeclInfo または None
        """
        # 命名規則から型を推測
        var_type = self._infer_type_from_name(var_name)
        
        definition = f"extern {var_type} {var_name};"
        
        return VariableDeclInfo(
            name=var_name,
            var_type=var_type,
            is_extern=True,
            definition=definition
        )
    
    def _infer_type_from_name(self, var_name: str) -> str:
        """
        変数名から型を推測
        
        Args:
            var_name: 変数名
        
        Returns:
            推測される型
        """
        # 命名規則に基づく推測
        # Utm で始まる → uint8_t が多い
        if var_name.startswith('Utm'):
            return 'uint8_t'
        
        # Utx で始まる → 型名の可能性が高い（変数ではない）
        if var_name.startswith('Utx'):
            return 'uint8_t'  # デフォルト
        
        # v で始まる → int
        if var_name.startswith('v'):
            return 'int'
        
        # m で始まる → enum定数の可能性
        if var_name.startswith('m'):
            return 'int'
        
        # デフォルト
        return 'int'
    
    def is_likely_function(self, var_name: str) -> bool:
        """
        変数名が関数名である可能性が高いかチェック
        
        Args:
            var_name: 変数名
        
        Returns:
            関数名の可能性が高い場合True
        """
        # 一般的な関数の命名規則
        # - f で始まる（f1, f2, f4など）
        # - Utf で始まる（Utf1, Utf2など）
        function_patterns = [
            r'^f[0-9]+$',  # f1, f2, ...
            r'^Utf[0-9]+$',  # Utf1, Utf2, ...
        ]
        
        for pattern in function_patterns:
            if re.match(pattern, var_name):
                return True
        
        return False
    
    def is_likely_enum_constant(self, var_name: str) -> bool:
        """
        変数名がenum定数である可能性が高いかチェック
        
        Args:
            var_name: 変数名
        
        Returns:
            enum定数の可能性が高い場合True
        """
        # enum定数の命名規則
        # - m で始まって数字が続く（m1, m47など）
        enum_patterns = [
            r'^m[0-9]+$',  # m1, m47, ...
        ]
        
        for pattern in enum_patterns:
            if re.match(pattern, var_name):
                return True
        
        return False
    
    def extract_function_pointer_tables(self, source_code: str) -> List[Dict]:
        """
        関数ポインタテーブルを抽出 (v4.7新規)
        
        パターン例:
        static void (*p_event_ctrldet_first[])(uint8_t i) = {
            &event_open_ctrldet,
            &event_close_ctrldet,
        };
        
        Args:
            source_code: ソースコード
        
        Returns:
            関数ポインタテーブル情報のリスト
        """
        from src.data_structures import FunctionPointerTable
        
        tables = []
        
        # 正規表現パターン（複数行対応）
        # [storage] return_type (*name[])(params) = { &func1, &func2, ... };
        pattern = re.compile(r'''
            (?P<storage>static\s+|extern\s+)?      # ストレージクラス (optional)
            (?P<return_type>\w+(?:\s*\*)?)\s*      # 戻り値型（ポインタ含む）
            \(\s*\*\s*                              # (*
            (?P<tblname>\w+)                          # 配列名
            \s*\[\s*(?P<size>\d*)\s*\]\s*\)        # [サイズ])
            \s*\(\s*(?P<params>[^)]*)\s*\)         # (パラメータ)
            \s*=\s*\{                               # = {
            (?P<init>[^}]+)                        # 初期化子
            \}                                      # }
        ''', re.VERBOSE | re.MULTILINE)
        
        # 関数参照パターン（&func または func）
        func_ref_pattern = re.compile(r'&?\s*(\w+)')
        
        for match in pattern.finditer(source_code):
            storage = (match.group('storage') or '').strip()
            return_type = match.group('return_type').strip()
            name = match.group('tblname').strip()
            size_str = match.group('size').strip()
            params = match.group('params').strip()
            init_list = match.group('init')
            
            # 初期化子から関数名を抽出
            functions = []
            for func_match in func_ref_pattern.finditer(init_list):
                func_name = func_match.group(1).strip()
                # 数値やコメント除去
                if func_name and not func_name.isdigit() and func_name not in ['NULL', 'null']:
                    functions.append(func_name)
            
            # 配列サイズ
            size = int(size_str) if size_str else len(functions)
            
            # パラメータ型リストを解析
            param_types = []
            if params and params != 'void':
                for param in params.split(','):
                    param = param.strip()
                    if param:
                        # "uint8_t i" -> "uint8_t"
                        parts = param.split()
                        if len(parts) >= 1:
                            # 最後の単語は変数名の可能性が高い
                            if len(parts) > 1:
                                param_types.append(' '.join(parts[:-1]))
                            else:
                                param_types.append(parts[0])
            
            # 行番号を取得
            line_number = source_code[:match.start()].count('\n') + 1
            
            table = FunctionPointerTable(
                name=name,
                storage=storage,
                return_type=return_type,
                params=params,
                param_types=param_types,
                functions=functions,
                size=size,
                line_number=line_number
            )
            
            tables.append(table)
            self.logger.info(f"関数ポインタテーブルを検出: {name} ({len(functions)}個の関数)")
        
        return tables
