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
from src.utils import setup_logger


class ASTBuilder:
    """ASTビルダー"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.parser = c_parser.CParser()
    
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
        fake_libc_includeを追加または標準型定義を追加
        
        Args:
            code: ソースコード
        
        Returns:
            fake_include追加後のコード
        """
        # 標準型定義を追加（stdint.h相当）
        standard_types = """
typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
typedef unsigned long long uint64_t;
typedef signed char int8_t;
typedef signed short int16_t;
typedef signed int int32_t;
typedef signed long long int64_t;
typedef unsigned long size_t;
typedef long ssize_t;
typedef int bool;

"""
        
        # コードの先頭に標準型定義を追加
        return standard_types + code
    
    def _handle_parse_error(self, error: Exception, code: str = "") -> None:
        """
        パースエラーを処理
        
        Args:
            error: エラー
            code: エラーが発生したコード
        """
        self.logger.error(f"ASTパースエラー: {str(error)}")
        
        # エラー箇所を特定
        error_msg = str(error)
        
        # 行番号が含まれている場合
        import re
        match = re.search(r'line (\d+)', error_msg)
        if match and code:
            line_no = int(match.group(1))
            lines = code.split('\n')
            
            if 0 < line_no <= len(lines):
                self.logger.error(f"エラー行({line_no}): {lines[line_no-1]}")
                
                # 前後の行も表示
                start = max(0, line_no - 3)
                end = min(len(lines), line_no + 2)
                
                self.logger.debug("エラー周辺のコード:")
                for i in range(start, end):
                    marker = ">>> " if i == line_no - 1 else "    "
                    self.logger.debug(f"{marker}{i+1:4d}: {lines[i]}")
    
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
