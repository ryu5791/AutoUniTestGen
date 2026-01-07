"""
ASTBuilderモジュール

pycparserを使用してC言語のASTを構築
"""

import sys
import os
from typing import Optional
from pycparser import c_parser, c_ast, parse_file

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger, get_resource_path, get_project_root


class ASTBuilder:
    """ASTビルダー"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.parser = c_parser.CParser()
        self.line_offset = 0  # v3.1: プリペンドされた行数のオフセット
    
    def get_line_offset(self) -> int:
        """
        プリペンドされた行数のオフセットを取得
        
        Returns:
            行番号オフセット
        """
        return self.line_offset
    
    def build_ast(self, code: str, use_cpp: bool = False) -> Optional[c_ast.FileAST]:
        """
        ASTを構築
        
        Args:
            code: C言語ソースコード
            use_cpp: プリプロセッサを使用するか
        
        Returns:
            構築されたAST（失敗時はNone）
        """
        try:
            self.logger.info("ASTの構築を開始")
            
            # fake_libc_includeを追加
            code = self._add_fake_includes(code)
            
            # ASTを構築
            ast = self.parser.parse(code, filename='<string>')
            
            self.logger.info("ASTの構築が完了")
            return ast
            
        except Exception as e:
            self._handle_parse_error(e, code)
            return None
    
    def build_ast_from_file(self, filepath: str) -> Optional[c_ast.FileAST]:
        """
        ファイルからASTを構築
        
        Args:
            filepath: C言語ファイルのパス
        
        Returns:
            構築されたAST（失敗時はNone）
        """
        try:
            self.logger.info(f"ファイルからASTを構築: {filepath}")
            
            # ファイルを読み込み
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            return self.build_ast(code)
            
        except Exception as e:
            self.logger.error(f"ファイル読み込みエラー: {str(e)}")
            return None
    
    def _add_fake_includes(self, code: str) -> str:
        """
        標準型定義とマクロを追加
        
        外部ファイルから標準型定義を読み込み、コードの先頭に追加する。
        ファイルが見つからない場合は、埋め込みの定義を使用する。
        
        Args:
            code: ソースコード
        
        Returns:
            標準定義追加後のコード
        """
        standard_definitions = ""
        
        # v4.8.1: PyInstaller対応のパス解決
        project_root = get_project_root()
        
        # 標準型定義ファイルを読み込み
        types_file = os.path.join(project_root, 'standard_types.h')
        macros_file = os.path.join(project_root, 'standard_macros.h')
        
        try:
            if os.path.exists(types_file):
                with open(types_file, 'r', encoding='utf-8') as f:
                    standard_definitions += f.read() + "\n\n"
                self.logger.debug(f"標準型定義を読み込み: {types_file}")
            else:
                # ファイルが存在しない場合は埋め込み定義を使用
                standard_definitions += self._get_embedded_type_definitions() + "\n\n"
                self.logger.debug("埋め込み標準型定義を使用")
            
            if os.path.exists(macros_file):
                with open(macros_file, 'r', encoding='utf-8') as f:
                    standard_definitions += f.read() + "\n\n"
                self.logger.debug(f"標準マクロ定義を読み込み: {macros_file}")
            else:
                # ファイルが存在しない場合は埋め込み定義を使用
                standard_definitions += self._get_embedded_macro_definitions() + "\n\n"
                self.logger.debug("埋め込み標準マクロ定義を使用")
                
        except Exception as e:
            self.logger.warning(f"標準定義ファイルの読み込みエラー: {e}")
            # エラー時は埋め込み定義を使用
            standard_definitions = self._get_embedded_type_definitions() + "\n\n"
            standard_definitions += self._get_embedded_macro_definitions() + "\n\n"
        
        # コードの先頭に標準定義を追加
        # v3.1: プリペンドされる行数をオフセットとして保存
        self.line_offset = len(standard_definitions.split('\n')) - 1
        self.logger.debug(f"行番号オフセット: {self.line_offset}")
        return standard_definitions + code
    
    def _get_embedded_type_definitions(self) -> str:
        """
        埋め込み型定義を返す（フォールバック用）
        """
        return """
typedef signed char        int8_t;
typedef short              int16_t;
typedef int                int32_t;
typedef long long          int64_t;
typedef unsigned char      uint8_t;
typedef unsigned short     uint16_t;
typedef unsigned int       uint32_t;
typedef unsigned long long uint64_t;
typedef unsigned long      size_t;
typedef long               ssize_t;
typedef enum { false = 0, true = 1 } bool;
"""
    
    def _get_embedded_macro_definitions(self) -> str:
        """
        埋め込みマクロ定義を返す（フォールバック用）
        
        注意: pycparserは#defineをサポートしないため、
        定数変数として定義する
        """
        return """
/* pycparser互換: #defineの代わりに定数として定義 */
static void* const NULL = 0;
static const int INT8_MIN = (-127 - 1);
static const int INT8_MAX = 127;
static const unsigned int UINT8_MAX = 0xffU;
"""
    
    def _handle_parse_error(self, error: Exception, code: str = "") -> None:
        """
        パースエラーを処理
        
        Args:
            error: エラー
            code: エラーが発生したコード
        """
        self.logger.error(f"ASTパースエラー: {str(error)}")
        
        if not code:
            return
        
        # エラー箇所を特定
        error_msg = str(error)
        import re
        
        # 複数の行番号パターンに対応
        # パターン1: <string>:45:1: 形式
        # パターン2: line 45 形式
        line_no = None
        
        match = re.search(r'<string>:(\d+):\d+:', error_msg)
        if match:
            line_no = int(match.group(1))
        else:
            match = re.search(r'line (\d+)', error_msg)
            if match:
                line_no = int(match.group(1))
        
        if line_no is None:
            return
        
        lines = code.split('\n')
        
        if 0 < line_no <= len(lines):
            # 前後の行を表示（前後5行）
            context_range = 5
            start = max(0, line_no - 1 - context_range)
            end = min(len(lines), line_no + context_range)
            
            self.logger.error(f"エラー発生箇所 (行 {line_no}):")
            self.logger.error("-" * 60)
            for i in range(start, end):
                marker = ">>> " if i == line_no - 1 else "    "
                self.logger.error(f"{marker}{i+1:4d}: {lines[i]}")
            self.logger.error("-" * 60)
    
    def visit_ast(self, ast: c_ast.FileAST, visitor: c_ast.NodeVisitor) -> None:
        """
        ASTを訪問
        
        Args:
            ast: AST
            visitor: ビジター
        """
        visitor.visit(ast)
    
    def print_ast(self, ast: c_ast.FileAST) -> None:
        """
        ASTを表示（デバッグ用）
        
        Args:
            ast: AST
        """
        if ast:
            ast.show()


class SimpleASTVisitor(c_ast.NodeVisitor):
    """シンプルなASTビジター（テスト用）"""
    
    def __init__(self):
        self.functions = []
        self.typedefs = []
        self.variables = []
    
    def visit_FuncDef(self, node):
        """関数定義を訪問"""
        func_name = node.decl.name
        self.functions.append(func_name)
        print(f"関数定義: {func_name}")
        self.generic_visit(node)
    
    def visit_Typedef(self, node):
        """typedef定義を訪問"""
        typedef_name = node.name
        self.typedefs.append(typedef_name)
        print(f"typedef: {typedef_name}")
        self.generic_visit(node)
    
    def visit_Decl(self, node):
        """変数宣言を訪問"""
        if node.name and not isinstance(node.type, c_ast.FuncDecl):
            self.variables.append(node.name)
            print(f"変数宣言: {node.name}")
        self.generic_visit(node)


if __name__ == "__main__":
    # ASTBuilderのテスト
    print("=== ASTBuilder のテスト ===\n")
    
    # テスト用サンプルコード
    sample_code = """
typedef enum {
    VALUE_A = 0,
    VALUE_B,
    VALUE_C
} MyEnum;

int global_var = 10;

int add(int a, int b) {
    return a + b;
}

void main_func(void) {
    int local_var = 20;
    int result = add(global_var, local_var);
    
    if (result > 0) {
        global_var++;
    }
}
"""
    
    builder = ASTBuilder()
    ast = builder.build_ast(sample_code)
    
    if ast:
        print("AST構築成功！\n")
        
        # ビジターでAST探索
        print("=== AST探索結果 ===")
        visitor = SimpleASTVisitor()
        builder.visit_ast(ast, visitor)
        
        print(f"\n検出された関数: {visitor.functions}")
        print(f"検出されたtypedef: {visitor.typedefs}")
        print(f"検出された変数: {visitor.variables}")
        
        print("\n✓ ASTBuilderが正常に動作しました")
    else:
        print("❌ AST構築に失敗しました")
