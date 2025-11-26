"""
ConditionExtractorモジュール

ASTから条件分岐を抽出
"""

import sys
import os
from typing import List, Optional, Tuple
from pycparser import c_ast

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import Condition, ConditionType


class ConditionExtractor(c_ast.NodeVisitor):
    """条件分岐抽出ビジター"""
    
    def __init__(self, target_function: Optional[str] = None):
        """
        初期化
        
        Args:
            target_function: 対象関数名（Noneの場合は全関数）
        """
        self.logger = setup_logger(__name__)
        self.target_function = target_function
        self.conditions: List[Condition] = []
        self.current_line = 0
        self.current_function = None
        self.in_target_function = False
        self.parent_context = ""
    
    def extract_conditions(self, ast: c_ast.FileAST) -> List[Condition]:
        """
        ASTから条件分岐を抽出
        
        Args:
            ast: AST
        
        Returns:
            条件分岐のリスト
        """
        self.logger.info("条件分岐の抽出を開始")
        self.conditions = []
        self.visit(ast)
        self.logger.info(f"条件分岐の抽出が完了: {len(self.conditions)}個")
        return self.conditions
    
    def visit_FuncDef(self, node: c_ast.FuncDef) -> None:
        """関数定義を訪問"""
        func_name = node.decl.name
        self.current_function = func_name
        
        # 対象関数かチェック
        if self.target_function is None or func_name == self.target_function:
            self.in_target_function = True
            self.logger.debug(f"対象関数に入る: {func_name}")
            self.generic_visit(node)
            self.in_target_function = False
            self.logger.debug(f"対象関数を出る: {func_name}")
        else:
            # 対象関数でない場合はスキップ
            pass
    
    def visit_If(self, node: c_ast.If) -> None:
        """if文を訪問"""
        if not self.in_target_function:
            return
        
        # 行番号を取得
        line = getattr(node, 'coord', None)
        line_no = line.line if line else 0
        
        # 条件式を文字列化（トップレベルなので括弧なし）
        condition_str = self._node_to_str(node.cond, is_top_level=True)
        
        # 条件式を解析
        condition_info = self._analyze_binary_op(node.cond)
        
        # Conditionオブジェクトを作成
        condition = Condition(
            line=line_no,
            type=condition_info['type'],
            expression=condition_str,
            operator=condition_info.get('operator'),
            left=condition_info.get('left'),
            right=condition_info.get('right'),
            conditions=condition_info.get('conditions'),  # 3つ以上の条件リスト
            ast_node=node,
            parent_context=self.parent_context
        )
        
        self.conditions.append(condition)
        self.logger.debug(f"if文を検出 (行{line_no}): {condition_str}")
        
        # 子ノードを訪問
        self.generic_visit(node)
    
    def visit_Switch(self, node: c_ast.Switch) -> None:
        """switch文を訪問"""
        if not self.in_target_function:
            return
        
        # 行番号を取得
        line = getattr(node, 'coord', None)
        line_no = line.line if line else 0
        
        # switch式を文字列化
        switch_expr = self._node_to_str(node.cond)
        
        # case値を抽出
        cases = self._extract_switch_cases(node)
        
        # Conditionオブジェクトを作成
        condition = Condition(
            line=line_no,
            type=ConditionType.SWITCH,
            expression=switch_expr,
            cases=cases,
            ast_node=node,
            parent_context=self.parent_context
        )
        
        self.conditions.append(condition)
        self.logger.debug(f"switch文を検出 (行{line_no}): {switch_expr}, cases: {cases}")
        
        # switch内部のコンテキストを設定
        old_context = self.parent_context
        self.parent_context = f"switch ({switch_expr})"
        
        # 子ノードを訪問
        self.generic_visit(node)
        
        self.parent_context = old_context
    
    def _analyze_binary_op(self, node) -> dict:
        """
        二項演算子を解析（3つ以上の条件に対応）
        
        Args:
            node: ASTノード
        
        Returns:
            解析結果の辞書
        """
        if isinstance(node, c_ast.BinaryOp):
            operator = node.op
            
            # OR条件
            if operator == '||':
                # 全てのOR条件を抽出
                conditions = self._extract_all_conditions(node, '||')
                
                return {
                    'type': ConditionType.OR_CONDITION,
                    'operator': 'or',
                    'conditions': conditions,
                    'left': conditions[0] if len(conditions) > 0 else '',
                    'right': conditions[1] if len(conditions) > 1 else ''
                }
            
            # AND条件
            elif operator == '&&':
                # 全てのAND条件を抽出
                conditions = self._extract_all_conditions(node, '&&')
                
                return {
                    'type': ConditionType.AND_CONDITION,
                    'operator': 'and',
                    'conditions': conditions,
                    'left': conditions[0] if len(conditions) > 0 else '',
                    'right': conditions[1] if len(conditions) > 1 else ''
                }
        
        # 単純な条件
        return {'type': ConditionType.SIMPLE_IF}
    
    def _extract_all_conditions(self, node, target_operator: str) -> List[str]:
        """
        同じ演算子で結合された全ての条件を抽出
        
        Args:
            node: ASTノード
            target_operator: 対象の演算子（'||' or '&&'）
        
        Returns:
            条件のリスト
        """
        conditions = []
        
        def traverse(n):
            if isinstance(n, c_ast.BinaryOp) and n.op == target_operator:
                # 左辺を再帰的に探索
                traverse(n.left)
                # 右辺を再帰的に探索
                traverse(n.right)
            else:
                # 葉ノード（実際の条件）
                conditions.append(self._node_to_str(n))
        
        traverse(node)
        return conditions
    
    def _extract_switch_cases(self, switch_node: c_ast.Switch) -> List:
        """
        switch文からcase値を抽出
        
        Args:
            switch_node: switchのASTノード
        
        Returns:
            case値のリスト
        """
        cases = []
        
        def visit_cases(node):
            if isinstance(node, c_ast.Case):
                if node.expr:
                    # case値を文字列化
                    case_value = self._node_to_str(node.expr)
                    cases.append(case_value)
            elif isinstance(node, c_ast.Default):
                cases.append('default')
            
            # 子ノードを再帰的に探索
            for child in node:
                visit_cases(child)
        
        if switch_node.stmt:
            visit_cases(switch_node.stmt)
        
        return cases
    
    def _node_to_str(self, node, is_top_level: bool = False) -> str:
        """
        ASTノードを文字列に変換
        
        Args:
            node: ASTノード
            is_top_level: トップレベル（最外側）かどうか
        
        Returns:
            文字列表現
        """
        if node is None:
            return ""
        
        # ID（変数名）
        if isinstance(node, c_ast.ID):
            return node.name
        
        # 定数
        if isinstance(node, c_ast.Constant):
            return node.value
        
        # 二項演算子
        if isinstance(node, c_ast.BinaryOp):
            left = self._node_to_str(node.left)
            right = self._node_to_str(node.right)
            # トップレベルの論理演算子の場合は括弧なし
            # 比較演算子やその他の演算子は括弧あり
            op = node.op
            if op in ('||', '&&'):
                # 論理演算子：トップレベルなら括弧なし
                if is_top_level:
                    return f"{left} {op} {right}"
                else:
                    return f"({left} {op} {right})"
            else:
                # 比較演算子等：常に括弧あり（元のソースに合わせる）
                return f"({left} {op} {right})"
        
        # 単項演算子
        if isinstance(node, c_ast.UnaryOp):
            operand = self._node_to_str(node.expr)
            if node.op == 'p++':
                return f"{operand}++"
            elif node.op == 'p--':
                return f"{operand}--"
            else:
                return f"{node.op}{operand}"
        
        # 関数呼び出し
        if isinstance(node, c_ast.FuncCall):
            func_name = self._node_to_str(node.name)
            args = []
            if node.args:
                for arg in node.args.exprs:
                    args.append(self._node_to_str(arg))
            args_str = ', '.join(args)
            return f"{func_name}({args_str})"
        
        # 配列アクセス
        if isinstance(node, c_ast.ArrayRef):
            name = self._node_to_str(node.name)
            subscript = self._node_to_str(node.subscript)
            return f"{name}[{subscript}]"
        
        # 構造体メンバアクセス
        if isinstance(node, c_ast.StructRef):
            struct = self._node_to_str(node.name)
            return f"{struct}{node.type}{node.field.name}"
        
        # キャスト
        if isinstance(node, c_ast.Cast):
            return self._node_to_str(node.expr)
        
        # その他
        try:
            return str(node)
        except:
            return "<unknown>"


if __name__ == "__main__":
    # ConditionExtractorのテスト
    print("=== ConditionExtractor のテスト ===\n")
    
    # テスト用サンプルコード
    sample_code = """
int f4(void);
int m47, m46, m48, mx2, m64;
int mx27(void);
void mx31(int);

int test_func(void) {
    int v9 = 0;
    int mx63 = 1;
    
    if ((f4() & 0xdf) != 0) {
        v9 = 7;
    }
    
    if ((mx63 == m47) || (mx63 == m46)) {
        mx63 = mx27();
        
        if ((mx63 == m48) || (mx63 == mx2)) {
            mx31(m64);
        }
    }
    
    switch (v9) {
        case 0:
            init();
            break;
        case 1:
            if (check()) {
                process();
            }
            break;
        case 2:
            cleanup();
            break;
        default:
            error();
            break;
    }
    
    return 0;
}

void init(void);
int check(void);
void process(void);
void cleanup(void);
void error(void);
"""
    
    # ASTを構築
    from src.parser.ast_builder import ASTBuilder
    
    builder = ASTBuilder()
    ast = builder.build_ast(sample_code)
    
    if ast:
        # 条件分岐を抽出
        extractor = ConditionExtractor(target_function="test_func")
        conditions = extractor.extract_conditions(ast)
        
        print(f"抽出された条件分岐: {len(conditions)}個\n")
        
        for i, cond in enumerate(conditions, 1):
            print(f"{i}. タイプ: {cond.type.value}")
            print(f"   式: {cond.expression}")
            if cond.operator:
                print(f"   演算子: {cond.operator}")
                print(f"   左辺: {cond.left}")
                print(f"   右辺: {cond.right}")
            if cond.cases:
                print(f"   case値: {cond.cases}")
            if cond.parent_context:
                print(f"   コンテキスト: {cond.parent_context}")
            print()
        
        print("✓ ConditionExtractorが正常に動作しました")
    else:
        print("❌ AST構築に失敗しました")
