"""
強化されたAST解析器 (v2.3)

より詳細な情報抽出とデータフロー解析を行う
"""

import pycparser
from pycparser import c_ast
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field


@dataclass
class VariableInfo:
    """変数の詳細情報"""
    name: str
    type: str
    is_global: bool = False
    is_input: bool = False
    is_output: bool = False
    is_pointer: bool = False
    assignments: List[Tuple[int, Any]] = field(default_factory=list)  # (行番号, 値)
    usages: List[int] = field(default_factory=list)  # 使用箇所の行番号


@dataclass
class BranchEffect:
    """分岐内での影響"""
    condition: str
    truth_value: bool
    line_number: int
    modified_variables: Dict[str, Any]  # 変数名: 新しい値
    function_calls: List[str]
    returns: Optional[Any] = None


class EnhancedASTAnalyzer:
    """強化されたAST解析器"""
    
    def __init__(self):
        self.variables: Dict[str, VariableInfo] = {}
        self.branch_effects: List[BranchEffect] = []
        self.function_calls: Dict[str, List[Tuple[int, List[Any]]]] = {}  # 関数名: [(行番号, 引数)]
        self.current_line = 0
        
    def analyze_function(self, func_ast: c_ast.FuncDef, global_vars: Set[str] = None) -> Dict:
        """関数全体を詳細に解析"""
        self.global_vars = global_vars or set()
        
        # パラメータを入力変数として登録
        if func_ast.decl.type.args:
            for param in func_ast.decl.type.args.params:
                if isinstance(param, c_ast.Decl):
                    self._register_variable(param, is_input=True)
        
        # 関数本体を解析
        self._analyze_compound(func_ast.body)
        
        # データフロー解析
        self._analyze_data_flow()
        
        return {
            'variables': self.variables,
            'branch_effects': self.branch_effects,
            'function_calls': self.function_calls
        }
    
    def extract_branch_effects(self, if_node: c_ast.If, truth_value: bool) -> BranchEffect:
        """if文の分岐内での影響を抽出"""
        branch = if_node.iftrue if truth_value else if_node.iffalse
        if not branch:
            return None
        
        effect = BranchEffect(
            condition=self._ast_to_string(if_node.cond),
            truth_value=truth_value,
            line_number=if_node.coord.line if if_node.coord else 0,
            modified_variables={},
            function_calls=[]
        )
        
        # 分岐内の処理を解析
        self._extract_effects_from_compound(branch, effect)
        
        return effect
    
    def extract_switch_effects(self, switch_node: c_ast.Switch, 
                              case_value: Any) -> BranchEffect:
        """switch文のcase内での影響を抽出"""
        effect = BranchEffect(
            condition=f"switch({self._ast_to_string(switch_node.cond)}) case {case_value}",
            truth_value=True,
            line_number=switch_node.coord.line if switch_node.coord else 0,
            modified_variables={},
            function_calls=[]
        )
        
        # switch文の該当caseを探して解析
        if switch_node.stmt:
            self._extract_case_effects(switch_node.stmt, case_value, effect)
        
        return effect
    
    def track_variable_flow(self, var_name: str) -> Dict:
        """変数のデータフローを追跡"""
        if var_name not in self.variables:
            return {}
        
        var_info = self.variables[var_name]
        flow = {
            'definitions': var_info.assignments,
            'usages': var_info.usages,
            'is_modified': len(var_info.assignments) > 1,
            'last_value': var_info.assignments[-1][1] if var_info.assignments else None
        }
        
        return flow
    
    def detect_side_effects(self, ast_node) -> Dict:
        """副作用を検出"""
        side_effects = {
            'global_modifications': [],
            'pointer_modifications': [],
            'function_calls': []
        }
        
        class SideEffectVisitor(c_ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.effects = side_effects
            
            def visit_Assignment(self, node):
                # グローバル変数への代入をチェック
                if isinstance(node.lvalue, c_ast.ID):
                    if node.lvalue.name in self.analyzer.global_vars:
                        value = self.analyzer._extract_value(node.rvalue)
                        self.effects['global_modifications'].append(
                            (node.lvalue.name, value)
                        )
                # ポインタ経由の代入をチェック
                elif isinstance(node.lvalue, c_ast.UnaryOp) and node.lvalue.op == '*':
                    self.effects['pointer_modifications'].append(
                        self.analyzer._ast_to_string(node.lvalue)
                    )
                self.generic_visit(node)
            
            def visit_FuncCall(self, node):
                if isinstance(node.name, c_ast.ID):
                    self.effects['function_calls'].append(node.name.name)
                self.generic_visit(node)
        
        visitor = SideEffectVisitor(self)
        visitor.visit(ast_node)
        
        return side_effects
    
    def _register_variable(self, decl_node: c_ast.Decl, is_input: bool = False):
        """変数を登録"""
        var_name = decl_node.name
        var_type = self._get_type_string(decl_node.type)
        is_pointer = self._is_pointer_type(decl_node.type)
        
        self.variables[var_name] = VariableInfo(
            name=var_name,
            type=var_type,
            is_global=var_name in self.global_vars,
            is_input=is_input,
            is_pointer=is_pointer
        )
    
    def _analyze_compound(self, compound: c_ast.Compound):
        """複合文を解析"""
        if not compound or not compound.block_items:
            return
        
        for item in compound.block_items:
            self._analyze_statement(item)
    
    def _analyze_statement(self, stmt):
        """文を解析"""
        if isinstance(stmt, c_ast.Decl):
            self._register_variable(stmt)
            if stmt.init:
                self._record_assignment(stmt.name, stmt.init)
        
        elif isinstance(stmt, c_ast.Assignment):
            if isinstance(stmt.lvalue, c_ast.ID):
                self._record_assignment(stmt.lvalue.name, stmt.rvalue)
        
        elif isinstance(stmt, c_ast.FuncCall):
            self._record_function_call(stmt)
        
        elif isinstance(stmt, c_ast.If):
            # if文の分岐を解析
            true_effect = self.extract_branch_effects(stmt, True)
            if true_effect:
                self.branch_effects.append(true_effect)
            
            false_effect = self.extract_branch_effects(stmt, False)
            if false_effect:
                self.branch_effects.append(false_effect)
        
        elif isinstance(stmt, c_ast.Switch):
            # switch文を解析
            case_values = self._extract_case_values_from_switch(stmt)
            for case_val in case_values:
                effect = self.extract_switch_effects(stmt, case_val)
                if effect:
                    self.branch_effects.append(effect)
        
        elif isinstance(stmt, c_ast.Compound):
            self._analyze_compound(stmt)
        
        elif isinstance(stmt, c_ast.Return):
            # return文を記録
            pass
    
    def _record_assignment(self, var_name: str, value_node):
        """代入を記録"""
        if var_name in self.variables:
            value = self._extract_value(value_node)
            line = value_node.coord.line if hasattr(value_node, 'coord') and value_node.coord else 0
            self.variables[var_name].assignments.append((line, value))
            self.variables[var_name].is_output = True
    
    def _record_function_call(self, func_call: c_ast.FuncCall):
        """関数呼び出しを記録"""
        if isinstance(func_call.name, c_ast.ID):
            func_name = func_call.name.name
            args = []
            if func_call.args:
                for arg in func_call.args.exprs:
                    args.append(self._extract_value(arg))
            
            line = func_call.coord.line if func_call.coord else 0
            if func_name not in self.function_calls:
                self.function_calls[func_name] = []
            self.function_calls[func_name].append((line, args))
    
    def _extract_effects_from_compound(self, compound, effect: BranchEffect):
        """複合文から影響を抽出"""
        if isinstance(compound, c_ast.Compound):
            if compound.block_items:
                for item in compound.block_items:
                    self._extract_effect_from_statement(item, effect)
        else:
            self._extract_effect_from_statement(compound, effect)
    
    def _extract_effect_from_statement(self, stmt, effect: BranchEffect):
        """文から影響を抽出"""
        if isinstance(stmt, c_ast.Assignment):
            if isinstance(stmt.lvalue, c_ast.ID):
                var_name = stmt.lvalue.name
                value = self._extract_value(stmt.rvalue)
                effect.modified_variables[var_name] = value
        
        elif isinstance(stmt, c_ast.FuncCall):
            if isinstance(stmt.name, c_ast.ID):
                effect.function_calls.append(stmt.name.name)
        
        elif isinstance(stmt, c_ast.Return):
            if stmt.expr:
                effect.returns = self._extract_value(stmt.expr)
        
        elif isinstance(stmt, c_ast.Compound):
            self._extract_effects_from_compound(stmt, effect)
    
    def _extract_case_effects(self, stmt, case_value, effect: BranchEffect):
        """switch文のcaseから影響を抽出"""
        # TODO: switch文のAST構造を解析してcase内の処理を抽出
        pass
    
    def _extract_case_values_from_switch(self, switch_node: c_ast.Switch) -> List[Any]:
        """switch文からcase値を抽出"""
        case_values = []
        
        class CaseVisitor(c_ast.NodeVisitor):
            def __init__(self):
                self.cases = []
            
            def visit_Case(self, node):
                if node.expr:
                    if isinstance(node.expr, c_ast.Constant):
                        self.cases.append(node.expr.value)
                    elif isinstance(node.expr, c_ast.ID):
                        self.cases.append(node.expr.name)
                else:
                    self.cases.append('default')
                self.generic_visit(node)
        
        visitor = CaseVisitor()
        visitor.visit(switch_node)
        
        return visitor.cases
    
    def _analyze_data_flow(self):
        """データフロー解析"""
        # 変数の使用箇所を分析して入力/出力を判定
        for var_name, var_info in self.variables.items():
            if not var_info.assignments and var_info.usages:
                var_info.is_input = True
            elif var_info.assignments and not var_info.is_global:
                var_info.is_output = True
    
    def _extract_value(self, node) -> Any:
        """ASTノードから値を抽出"""
        if isinstance(node, c_ast.Constant):
            return node.value
        elif isinstance(node, c_ast.ID):
            return node.name
        elif isinstance(node, c_ast.UnaryOp):
            if node.op == '-':
                sub_value = self._extract_value(node.expr)
                try:
                    return -int(sub_value)
                except:
                    return f"-{sub_value}"
        elif isinstance(node, c_ast.BinaryOp):
            left = self._extract_value(node.left)
            right = self._extract_value(node.right)
            return f"{left} {node.op} {right}"
        elif isinstance(node, c_ast.FuncCall):
            if isinstance(node.name, c_ast.ID):
                return f"{node.name.name}()"
        
        return None
    
    def _ast_to_string(self, node) -> str:
        """ASTノードを文字列に変換"""
        if isinstance(node, c_ast.BinaryOp):
            left = self._ast_to_string(node.left)
            right = self._ast_to_string(node.right)
            return f"({left} {node.op} {right})"
        elif isinstance(node, c_ast.UnaryOp):
            expr = self._ast_to_string(node.expr)
            if node.op in ['++', '--', '!', '~', '-', '+', '*', '&']:
                return f"{node.op}{expr}"
            else:
                return f"{expr}{node.op}"
        elif isinstance(node, c_ast.ID):
            return node.name
        elif isinstance(node, c_ast.Constant):
            return str(node.value)
        elif isinstance(node, c_ast.FuncCall):
            if isinstance(node.name, c_ast.ID):
                return f"{node.name.name}()"
        else:
            return "complex_expression"
    
    def _get_type_string(self, type_node) -> str:
        """型ノードから型文字列を取得"""
        if isinstance(type_node, c_ast.TypeDecl):
            return self._get_type_string(type_node.type)
        elif isinstance(type_node, c_ast.IdentifierType):
            return ' '.join(type_node.names)
        elif isinstance(type_node, c_ast.PtrDecl):
            return self._get_type_string(type_node.type) + '*'
        elif isinstance(type_node, c_ast.ArrayDecl):
            return self._get_type_string(type_node.type) + '[]'
        else:
            return 'unknown'
    
    def _is_pointer_type(self, type_node) -> bool:
        """ポインタ型かどうか判定"""
        if isinstance(type_node, c_ast.PtrDecl):
            return True
        elif isinstance(type_node, c_ast.TypeDecl):
            return self._is_pointer_type(type_node.type) if type_node.type else False
        return False
