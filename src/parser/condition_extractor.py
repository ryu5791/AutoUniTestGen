"""
ConditionExtractorモジュール

ASTから条件分岐を抽出
"""

import sys
import os
from typing import List, Optional, Tuple, Dict, Any
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
        self.source_lines: List[str] = []  # v3.1: 元のソースコードの行を保持
        self.line_offset: int = 0  # v3.1: 行番号オフセット
        self.function_final_return: Optional[str] = None  # v5.1.2: 関数の最終return値
        self.all_return_statements: List[Tuple[int, str]] = []  # v5.1.4: 全return文
        self.local_var_assignments: Dict[str, str] = {}  # v5.1.6: ローカル変数の代入元関数
        self.global_var_modifications: List[Dict[str, Any]] = []  # v5.1.7: グローバル変数の変更履歴
    
    def set_source_lines(self, source_lines: List[str]) -> None:
        """
        元のソースコードの行を設定
        
        Args:
            source_lines: ソースコードの行リスト
        """
        self.source_lines = source_lines
        self.logger.debug(f"ソースコード {len(source_lines)} 行を設定しました")
    
    def set_line_offset(self, offset: int) -> None:
        """
        行番号オフセットを設定
        
        v3.1: ASTの行番号から元のソース行番号に変換するためのオフセット
        
        Args:
            offset: 行番号オフセット（プリペンドされた行数）
        """
        self.line_offset = offset
        self.logger.debug(f"行番号オフセット: {offset}")
    
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
            
            # v5.1.2: 関数の最終return文を抽出
            self.function_final_return = self._extract_function_final_return(node)
            self.logger.debug(f"関数の最終return: {self.function_final_return}")
            
            # v5.1.4 Phase 3: 関数内の全return文を抽出
            self.all_return_statements = self._extract_all_return_statements(node)
            self.logger.debug(f"関数内の全return文: {len(self.all_return_statements)}個")
            
            # v5.1.6 Phase 4: ローカル変数への関数呼び出し代入を抽出
            self.local_var_assignments = self._extract_local_var_assignments(node)
            self.logger.debug(f"ローカル変数代入: {self.local_var_assignments}")
            
            # v5.1.7: グローバル/static変数の変更を抽出
            self.global_var_modifications = self._extract_global_var_modifications(node)
            self.logger.debug(f"グローバル変数変更: {len(self.global_var_modifications)}件")
            
            self.generic_visit(node)
            self.in_target_function = False
            self.logger.debug(f"対象関数を出る: {func_name}")
        else:
            # 対象関数でない場合はスキップ
            pass
    
    def _extract_global_var_modifications(self, func_node: c_ast.FuncDef) -> List[Dict[str, Any]]:
        """
        グローバル/static変数への変更を抽出 (v5.1.7)
        
        例: g_total_calls++;  → {'var': 'g_total_calls', 'op': '++', 'line': 52, 'condition': None}
        例: g_system_fault = true; → {'var': 'g_system_fault', 'op': '=', 'value': 'true', 'line': 58, 'condition': 'raw_temp == -999'}
        
        Args:
            func_node: 関数定義のASTノード
        
        Returns:
            変更情報のリスト
        """
        modifications = []
        current_condition = None
        condition_stack = []
        
        def visit_node(node, in_condition=None):
            nonlocal current_condition
            
            # if文の条件を追跡
            if isinstance(node, c_ast.If):
                cond_str = self._node_to_str(node.cond) if node.cond else None
                
                # true分岐を処理
                if node.iftrue:
                    for child_name, child in node.iftrue.children() if hasattr(node.iftrue, 'children') else []:
                        visit_node(child, in_condition=cond_str)
                    if isinstance(node.iftrue, (c_ast.Assignment, c_ast.UnaryOp)):
                        visit_node(node.iftrue, in_condition=cond_str)
                
                # false分岐を処理
                if node.iffalse:
                    for child_name, child in node.iffalse.children() if hasattr(node.iffalse, 'children') else []:
                        visit_node(child, in_condition=f"!({cond_str})")
                return
            
            # インクリメント/デクリメント演算子
            if isinstance(node, c_ast.UnaryOp):
                if node.op in ['++', '--', 'p++', 'p--']:
                    if isinstance(node.expr, c_ast.ID):
                        var_name = node.expr.name
                        line = getattr(node, 'coord', None)
                        line_no = line.line - self.line_offset if line else 0
                        modifications.append({
                            'var': var_name,
                            'op': node.op.replace('p', ''),
                            'value': None,
                            'line': line_no,
                            'condition': in_condition
                        })
            
            # 代入演算子
            if isinstance(node, c_ast.Assignment):
                if isinstance(node.lvalue, c_ast.ID):
                    var_name = node.lvalue.name
                    value = self._node_to_str(node.rvalue) if node.rvalue else None
                    line = getattr(node, 'coord', None)
                    line_no = line.line - self.line_offset if line else 0
                    modifications.append({
                        'var': var_name,
                        'op': node.op,
                        'value': value,
                        'line': line_no,
                        'condition': in_condition
                    })
            
            # 子ノードを再帰的に訪問
            for child_name, child in node.children():
                visit_node(child, in_condition=in_condition)
        
        if func_node.body:
            visit_node(func_node.body)
        
        return modifications
    
    def _extract_local_var_assignments(self, func_node: c_ast.FuncDef) -> Dict[str, str]:
        """
        ローカル変数への関数呼び出し代入を抽出 (v5.1.6 Phase 4)
        
        例: int risk = evaluate_heat_risk(temp, humidity);
        → {'risk': 'evaluate_heat_risk'}
        
        Args:
            func_node: 関数定義のASTノード
        
        Returns:
            {変数名: 関数名} の辞書
        """
        assignments = {}
        
        def visit_node(node):
            # 変数宣言時の初期化をチェック
            if isinstance(node, c_ast.Decl):
                if node.init and isinstance(node.init, c_ast.FuncCall):
                    var_name = node.name
                    if node.init.name and hasattr(node.init.name, 'name'):
                        func_name = node.init.name.name
                        assignments[var_name] = func_name
                        self.logger.debug(f"代入検出: {var_name} = {func_name}(...)")
            
            # 代入文をチェック
            if isinstance(node, c_ast.Assignment):
                if isinstance(node.rvalue, c_ast.FuncCall):
                    if isinstance(node.lvalue, c_ast.ID):
                        var_name = node.lvalue.name
                        if node.rvalue.name and hasattr(node.rvalue.name, 'name'):
                            func_name = node.rvalue.name.name
                            assignments[var_name] = func_name
                            self.logger.debug(f"代入検出: {var_name} = {func_name}(...)")
            
            # 子ノードを再帰的に訪問
            for child_name, child in node.children():
                visit_node(child)
        
        if func_node.body:
            visit_node(func_node.body)
        
        return assignments
    
    def _extract_all_return_statements(self, func_node: c_ast.FuncDef) -> List[Tuple[int, str]]:
        """
        関数内の全return文を抽出 (v5.1.4 Phase 3)
        
        Args:
            func_node: 関数定義のASTノード
        
        Returns:
            (行番号, return値)のタプルのリスト
        """
        return_statements = []
        
        def visit_node(node):
            if isinstance(node, c_ast.Return):
                line = getattr(node, 'coord', None)
                line_no = line.line - self.line_offset if line else 0
                if node.expr:
                    value = self._node_to_str(node.expr)
                else:
                    value = "void"
                return_statements.append((line_no, value))
            
            # 子ノードを再帰的に訪問
            for child_name, child in node.children():
                visit_node(child)
        
        if func_node.body:
            visit_node(func_node.body)
        
        return return_statements
    
    def _extract_function_final_return(self, func_node: c_ast.FuncDef) -> Optional[str]:
        """
        関数の最終return文（デフォルトreturn）を抽出 (v5.1.2)
        
        関数本体の末尾にあるreturn文を探す
        これは条件分岐を通過した後の「フォールスルー」return値
        
        Args:
            func_node: 関数定義のASTノード
        
        Returns:
            最終return値の文字列、またはNone
        """
        if not func_node.body or not isinstance(func_node.body, c_ast.Compound):
            return None
        
        if not func_node.body.block_items:
            return None
        
        # 関数本体の末尾から探索
        block_items = func_node.body.block_items
        
        # 末尾の文がreturn文かチェック
        last_item = block_items[-1]
        if isinstance(last_item, c_ast.Return):
            if last_item.expr:
                return self._node_to_str(last_item.expr)
            else:
                return "void"
        
        return None
    
    def visit_If(self, node: c_ast.If) -> None:
        """if文を訪問"""
        if not self.in_target_function:
            return
        
        # 行番号を取得
        line = getattr(node, 'coord', None)
        ast_line_no = line.line if line else 0
        
        # v3.1: オフセットを適用して元のソース行番号を取得
        original_line_no = ast_line_no - self.line_offset
        
        # v4.8.4: ASTノードから条件式を構築（括弧構造を維持）
        # これにより、コメントによる行番号ずれの問題を回避
        condition_str = self._node_to_str(node.cond, is_top_level=True)
        
        # 括弧で囲む（一貫性のため）
        if not condition_str.startswith('('):
            condition_str = f'({condition_str})'
        
        self.logger.debug(f"ASTから条件式を構築 (AST行{ast_line_no}→元行{original_line_no}): {condition_str[:50]}...")
        
        # v4.8.4: 条件式テキストから直接解析（ASTノードの行番号ずれ問題を回避）
        condition_info = self._analyze_condition_text(condition_str)
        
        # v5.1.1: if文のtrue/false分岐のreturn値を抽出
        return_value_if_true = self._extract_return_value(node.iftrue)
        return_value_if_false = self._extract_return_value(node.iffalse) if node.iffalse else None
        
        # Conditionオブジェクトを作成
        condition = Condition(
            line=original_line_no,  # v3.1: 元のソースの行番号を使用
            type=condition_info['type'],
            expression=condition_str,
            operator=condition_info.get('operator'),
            left=condition_info.get('left'),
            right=condition_info.get('right'),
            conditions=condition_info.get('conditions'),  # 3つ以上の条件リスト
            ast_node=node,
            parent_context=self.parent_context,
            return_value_if_true=return_value_if_true,    # v5.1.1
            return_value_if_false=return_value_if_false   # v5.1.1
        )
        
        self.conditions.append(condition)
        self.logger.debug(f"if文を検出 (元行{original_line_no}): {condition_str}, return_true={return_value_if_true}, return_false={return_value_if_false}")
        
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
    
    def _analyze_condition_text(self, condition_str: str) -> dict:
        """
        v4.8.4: 条件式テキストを直接解析（ASTノードの行番号ずれ問題を回避）
        
        Args:
            condition_str: 条件式テキスト
        
        Returns:
            解析結果の辞書
        """
        if not condition_str:
            return {'type': ConditionType.SIMPLE_IF}
        
        # トップレベルの演算子を特定
        top_op = self._find_top_level_operator(condition_str)
        
        if top_op == '||':
            # OR条件
            conditions = self._split_by_top_operator(condition_str, '||')
            return {
                'type': ConditionType.OR_CONDITION,
                'operator': 'or',
                'conditions': conditions,
                'left': conditions[0] if len(conditions) > 0 else '',
                'right': conditions[1] if len(conditions) > 1 else ''
            }
        
        elif top_op == '&&':
            # AND条件
            conditions = self._split_by_top_operator(condition_str, '&&')
            return {
                'type': ConditionType.AND_CONDITION,
                'operator': 'and',
                'conditions': conditions,
                'left': conditions[0] if len(conditions) > 0 else '',
                'right': conditions[1] if len(conditions) > 1 else ''
            }
        
        # 単純な条件
        return {'type': ConditionType.SIMPLE_IF}
    
    def _find_top_level_operator(self, text: str) -> Optional[str]:
        """
        トップレベル（最も外側）の論理演算子を見つける
        
        Args:
            text: 条件式テキスト
        
        Returns:
            演算子（'||' or '&&'）またはNone
        """
        text = text.strip()
        # 外側の括弧を除去
        while text.startswith('(') and text.endswith(')'):
            depth = 0
            valid = True
            for i, char in enumerate(text[1:-1], 1):
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth < 0:
                        valid = False
                        break
            if valid and depth == 0:
                text = text[1:-1].strip()
            else:
                break
        
        depth = 0
        i = 0
        while i < len(text):
            char = text[i]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif depth == 0:
                # トップレベルで演算子を探す
                # ||を先にチェック（優先度が低いため外側に来る）
                if text[i:i+2] == '||':
                    return '||'
                if text[i:i+2] == '&&':
                    # まだ||があるかもしれないので、最後まで探索
                    pass
            i += 1
        
        # ||がなければ&&を探す
        depth = 0
        i = 0
        while i < len(text):
            char = text[i]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif depth == 0 and text[i:i+2] == '&&':
                return '&&'
            i += 1
        
        return None
    
    def _split_by_top_operator(self, text: str, operator: str) -> List[str]:
        """
        トップレベルの演算子で条件式を分割
        
        Args:
            text: 条件式テキスト
            operator: 演算子（'||' or '&&'）
        
        Returns:
            分割された条件のリスト
        """
        text = text.strip()
        # 外側の括弧を除去
        while text.startswith('(') and text.endswith(')'):
            depth = 0
            valid = True
            for i, char in enumerate(text[1:-1], 1):
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth < 0:
                        valid = False
                        break
            if valid and depth == 0:
                text = text[1:-1].strip()
            else:
                break
        
        parts = []
        current = ""
        depth = 0
        i = 0
        op_len = len(operator)
        
        while i < len(text):
            char = text[i]
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif depth == 0 and text[i:i+op_len] == operator:
                if current.strip():
                    parts.append(current.strip())
                current = ""
                i += op_len - 1
            else:
                current += char
            i += 1
        
        if current.strip():
            parts.append(current.strip())
        
        return parts
    
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
    
    def _extract_return_value(self, block_node) -> Optional[str]:
        """
        ブロックからreturn値を抽出 (v5.1.1)
        
        if文のtrue/false分岐内のreturn文を探して、その値を返す
        
        Args:
            block_node: if文のiftrue または iffalse ブロック
        
        Returns:
            return値の文字列、またはNone（return文がない場合）
        """
        if block_node is None:
            return None
        
        # Return文を直接チェック
        if isinstance(block_node, c_ast.Return):
            if block_node.expr:
                return self._node_to_str(block_node.expr)
            else:
                return "void"  # return; の場合
        
        # Compound（ブロック）の場合、最初のreturn文を探す
        if isinstance(block_node, c_ast.Compound):
            if block_node.block_items:
                for item in block_node.block_items:
                    # 直接return文の場合
                    if isinstance(item, c_ast.Return):
                        if item.expr:
                            return self._node_to_str(item.expr)
                        else:
                            return "void"
                    # ネストしたif文の場合は再帰的に探索しない
                    # （最初の直接return文のみを対象とする）
        
        # それ以外のノードの場合
        # 子ノードに直接Returnがあるか確認
        for child_name, child in block_node.children():
            if isinstance(child, c_ast.Return):
                if child.expr:
                    return self._node_to_str(child.expr)
                else:
                    return "void"
        
        return None
    
    def _extract_switch_cases(self, switch_node: c_ast.Switch) -> List:
        """
        switch文からcase値を抽出（直接の子caseのみ、ネストしたswitchのcaseは除外）
        
        v4.7.2: ネストしたswitch文のcaseが混入するバグを修正
        
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
                # caseのstmts内を探索（ただし内側のswitchは除外）
                if node.stmts:
                    for stmt in node.stmts:
                        # 内側のSwitch文は除外（そのswitchは別途独立して処理される）
                        if not isinstance(stmt, c_ast.Switch):
                            visit_cases(stmt)
            elif isinstance(node, c_ast.Default):
                cases.append('default')
                # defaultのstmts内を探索（ただし内側のswitchは除外）
                if node.stmts:
                    for stmt in node.stmts:
                        if not isinstance(stmt, c_ast.Switch):
                            visit_cases(stmt)
            elif isinstance(node, c_ast.Compound):
                # Compound内を探索（ただし内側のswitchは除外）
                if node.block_items:
                    for item in node.block_items:
                        if not isinstance(item, c_ast.Switch):
                            visit_cases(item)
            else:
                # その他のノードは子を探索（ただし内側のswitchは除外）
                for child in node:
                    if not isinstance(child, c_ast.Switch):
                        visit_cases(child)
        
        if switch_node.stmt:
            visit_cases(switch_node.stmt)
        
        return cases
    
    def _extract_condition_from_source(self, start_line: int) -> str:
        """
        元のソースコードからif文の条件式を抽出
        
        v3.1: 元のソースの括弧構造を維持するため、ASTから再構築せず直接抽出
        
        Args:
            start_line: if文の開始行番号（1から始まる）
        
        Returns:
            条件式テキスト（抽出失敗時は空文字列）
        """
        if not self.source_lines or start_line < 1:
            return ""
        
        # ソースの行番号は1から始まるが、リストは0から始まる
        line_idx = start_line - 1
        if line_idx >= len(self.source_lines):
            return ""
        
        text = ""
        paren_depth = 0
        started = False
        found_if = False
        
        # 開始行から探索
        for i in range(line_idx, len(self.source_lines)):
            line = self.source_lines[i]
            j = 0
            
            while j < len(line):
                # 'if'キーワードを探す（まだ見つかっていない場合）
                if not found_if:
                    # 'if' の後に '(' が続くパターンを探す
                    if line[j:j+2] == 'if' and (j == 0 or not line[j-1].isalnum()):
                        # 'if'の後に識別子文字が続かないことを確認
                        after_if = j + 2
                        if after_if >= len(line) or not line[after_if].isalnum():
                            found_if = True
                            j += 2
                            continue
                    j += 1
                    continue
                
                char = line[j]
                
                # コメントをスキップ
                if line[j:j+2] == '//':
                    break  # 行末まで無視
                if line[j:j+2] == '/*':
                    # ブロックコメントの終わりを探す
                    end_idx = line.find('*/', j + 2)
                    if end_idx != -1:
                        j = end_idx + 2
                        continue
                    else:
                        # この行の残りをスキップ
                        break
                
                if not started:
                    if char == '(':
                        started = True
                        paren_depth = 1
                        j += 1
                        continue
                    elif char.isspace():
                        j += 1
                        continue
                    else:
                        # 'if'の後に'('以外の非空白文字が来た
                        j += 1
                        continue
                else:
                    if char == '(':
                        paren_depth += 1
                        text += char
                    elif char == ')':
                        paren_depth -= 1
                        if paren_depth == 0:
                            # 条件式の終了
                            # 改行と余分な空白を正規化
                            result = ' '.join(text.split())
                            # v3.1: 条件式全体を括弧で囲んで返す（元の構造を維持）
                            return f"({result})"
                        text += char
                    else:
                        text += char
                
                j += 1
            
            # 次の行に続く場合はスペースを追加
            if started and paren_depth > 0:
                text += " "
        
        # 括弧が閉じられなかった場合
        return ""
    
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
