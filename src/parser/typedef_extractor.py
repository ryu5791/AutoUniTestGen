"""
TypedefExtractorモジュール

C言語ソースファイルから型定義(typedef)を抽出する
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
class TypedefInfo:
    """型定義情報"""
    name: str
    typedef_type: str  # 'struct', 'union', 'enum', 'basic'
    definition: str
    dependencies: List[str]
    line_number: int


class TypedefExtractor:
    """型定義抽出器"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.typedefs: List[TypedefInfo] = []
        self.source_lines: List[str] = []
        self.standard_types = self._load_standard_types()
    
    def _load_standard_types(self) -> Set[str]:
        """
        standard_types.hから標準型を読み込む
        
        Returns:
            標準型名のセット
        """
        # パスの構築: src/parser/typedef_extractor.py -> ../../standard_types.h
        base_path = os.path.dirname(os.path.abspath(__file__))
        std_types_path = os.path.join(base_path, '../../standard_types.h')
        
        standard_types = set()
        
        try:
            with open(std_types_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # typedef ... type_name; の形式から型名を抽出
                    match = re.search(r'typedef\s+.*\s+(\w+)\s*;', line)
                    if match:
                        type_name = match.group(1)
                        standard_types.add(type_name)
            
            self.logger.info(f"standard_types.hから{len(standard_types)}個の標準型を読み込みました")
            
        except FileNotFoundError:
            self.logger.warning(f"standard_types.h not found at {std_types_path}, using fallback")
            # フォールバック: 最小限の標準型
            standard_types = {
                'int8_t', 'uint8_t', 'int16_t', 'uint16_t',
                'int32_t', 'uint32_t', 'int64_t', 'uint64_t',
                'int_least8_t', 'int_least16_t', 'int_least32_t', 'int_least64_t',
                'uint_least8_t', 'uint_least16_t', 'uint_least32_t', 'uint_least64_t',
                'int_fast8_t', 'int_fast16_t', 'int_fast32_t', 'int_fast64_t',
                'uint_fast8_t', 'uint_fast16_t', 'uint_fast32_t', 'uint_fast64_t',
                'intmax_t', 'uintmax_t', 'intptr_t', 'uintptr_t',
                'size_t', 'ssize_t', 'ptrdiff_t', 'wchar_t', 'wint_t',
                'bool', 'true', 'false'
            }
        except Exception as e:
            self.logger.error(f"standard_types.h読み込み中にエラー: {e}")
            # フォールバック
            standard_types = {
                'int8_t', 'uint8_t', 'int16_t', 'uint16_t',
                'int32_t', 'uint32_t', 'int64_t', 'uint64_t',
                'size_t', 'bool'
            }
        
        return standard_types
    
    def extract_typedefs(self, ast, source_code: str) -> List[TypedefInfo]:
        """
        ASTから型定義を抽出
        
        Args:
            ast: pycparserのAST
            source_code: 元のソースコード
        
        Returns:
            List[TypedefInfo]: 型定義情報のリスト
        """
        self.typedefs = []
        self.source_lines = source_code.split('\n')
        
        if ast is None or c_ast is None:
            self.logger.warning("AST is None または pycparser not available")
            return self._extract_typedefs_by_regex(source_code)
        
        # ASTを巡回してtypedefを抽出
        self._visit_ast(ast)
        
        # 正規表現でも抽出（ASTで取れないものをカバー）
        regex_typedefs = self._extract_typedefs_by_regex(source_code)
        
        # 重複を除去してマージ
        existing_names = {td.name for td in self.typedefs}
        for td in regex_typedefs:
            if td.name not in existing_names:
                self.typedefs.append(td)
        
        # 標準型定義をフィルタリング
        self.typedefs = self._filter_standard_typedefs(self.typedefs)
        
        self.logger.info(f"{len(self.typedefs)}個の型定義を抽出しました")
        return self.typedefs
    
    def _filter_standard_typedefs(self, typedefs: List[TypedefInfo]) -> List[TypedefInfo]:
        """
        標準型定義をフィルタリング
        
        Args:
            typedefs: 型定義のリスト
        
        Returns:
            フィルタリング後の型定義のリスト
        """
        # 標準ヘッダーで定義される型（除外対象）
        standard_types = {
            'int8_t', 'int16_t', 'int32_t', 'int64_t',
            'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
            'int_least8_t', 'int_least16_t', 'int_least32_t', 'int_least64_t',
            'uint_least8_t', 'uint_least16_t', 'uint_least32_t', 'uint_least64_t',
            'int_fast8_t', 'int_fast16_t', 'int_fast32_t', 'int_fast64_t',
            'uint_fast8_t', 'uint_fast16_t', 'uint_fast32_t', 'uint_fast64_t',
            'intmax_t', 'uintmax_t', 'intptr_t', 'uintptr_t',
            'size_t', 'ssize_t', 'ptrdiff_t', 'wchar_t', 'wint_t',
            'bool', 'true', 'false'
        }
        
        filtered = []
        for td in typedefs:
            if td.name not in standard_types:
                filtered.append(td)
        
        return filtered
    
    def _visit_ast(self, node, depth=0):
        """
        ASTを再帰的に訪問してtypedefを抽出
        
        Args:
            node: ASTノード
            depth: 再帰の深さ
        """
        if depth > 100:  # 無限再帰防止
            return
        
        if c_ast is None:
            return
        
        # Typedefノードを処理
        if isinstance(node, c_ast.Typedef):
            typedef_info = self._process_typedef_node(node)
            if typedef_info:
                self.typedefs.append(typedef_info)
        
        # 子ノードを再帰的に訪問
        for child_name, child in node.children():
            self._visit_ast(child, depth + 1)
    
    def _process_typedef_node(self, node) -> Optional[TypedefInfo]:
        """
        TypedefノードからTypedefInfoを生成
        
        Args:
            node: pycparser の Typedef ノード
        
        Returns:
            TypedefInfo または None
        """
        if c_ast is None:
            return None
        
        try:
            name = node.name
            
            # 型の種類を判定
            typedef_type = 'basic'
            if isinstance(node.type, c_ast.TypeDecl):
                if isinstance(node.type.type, (c_ast.Struct, c_ast.Union, c_ast.Enum)):
                    type_node = node.type.type
                    if isinstance(type_node, c_ast.Struct):
                        typedef_type = 'struct'
                    elif isinstance(type_node, c_ast.Union):
                        typedef_type = 'union'
                    elif isinstance(type_node, c_ast.Enum):
                        typedef_type = 'enum'
            
            # ソースコードから定義を抽出
            definition = self._extract_definition_from_source(name, typedef_type)
            
            # 依存関係を検出
            dependencies = self._find_dependencies(definition)
            
            # 行番号を取得
            line_number = node.coord.line if hasattr(node, 'coord') and node.coord else 0
            
            return TypedefInfo(
                name=name,
                typedef_type=typedef_type,
                definition=definition,
                dependencies=dependencies,
                line_number=line_number
            )
        
        except Exception as e:
            self.logger.warning(f"typedef処理中にエラー: {e}")
            return None
    
    def _extract_definition_from_source(self, name: str, typedef_type: str) -> str:
        """
        ソースコードから型定義の完全な定義を抽出
        
        Args:
            name: typedef名
            typedef_type: 型の種類
        
        Returns:
            完全な定義文字列
        """
        # 標準型の場合は警告を出さずに簡易定義を返す
        if name in self.standard_types:
            return f"typedef /* standard type */ {name};"
        
        source_code = '\n'.join(self.source_lines)
        
        # 方法1: typedef名の直前を検索し、波括弧のバランスを取りながら抽出
        typedef_with_name = rf'\s+{re.escape(name)}\s*;'
        matches = list(re.finditer(typedef_with_name, source_code))
        
        for match in matches:
            end_pos = match.end()
            # typedefの開始位置を逆方向に検索
            start_pos = self._find_typedef_start(source_code, end_pos)
            if start_pos >= 0:
                definition = source_code[start_pos:end_pos].strip()
                # typedefで始まることを確認
                if definition.startswith('typedef'):
                    return definition
        
        # 方法2: より寛容な正規表現パターン
        # struct/union/enum の場合
        if typedef_type in ['struct', 'union', 'enum']:
            definition = self._extract_struct_union_enum_typedef(source_code, name, typedef_type)
            if definition:
                return definition
        
        # 方法3: 基本型のtypedefの場合（単純なパターン）
        pattern = rf'typedef\s+[^;{{]+\s+{re.escape(name)}\s*;'
        match = re.search(pattern, source_code)
        if match:
            return match.group(0)
        
        # 見つからない場合
        self.logger.warning(f"型定義 '{name}' の完全な定義を抽出できませんでした")
        return f"typedef /* unknown */ {name};"
    
    def _find_typedef_start(self, source_code: str, end_pos: int) -> int:
        """
        typedef名の位置から、typedefキーワードの開始位置を逆方向に検索
        
        Args:
            source_code: ソースコード
            end_pos: typedef名の終了位置
        
        Returns:
            typedefの開始位置（見つからない場合は-1）
        """
        # 逆方向に検索（最大5000文字まで）
        search_start = max(0, end_pos - 5000)
        search_text = source_code[search_start:end_pos]
        
        # typedefキーワードを検索
        typedef_matches = list(re.finditer(r'\btypedef\b', search_text))
        
        if not typedef_matches:
            return -1
        
        # 最後のtypedefを使用
        last_typedef = typedef_matches[-1]
        typedef_start = search_start + last_typedef.start()
        
        # 波括弧のバランスを確認
        text_between = source_code[typedef_start:end_pos]
        if self._check_brace_balance(text_between):
            return typedef_start
        
        return -1
    
    def _check_brace_balance(self, text: str) -> bool:
        """
        波括弧のバランスをチェック
        
        Args:
            text: チェックするテキスト
        
        Returns:
            バランスが取れている場合True
        """
        balance = 0
        for char in text:
            if char == '{':
                balance += 1
            elif char == '}':
                balance -= 1
        return balance == 0
    
    def _extract_struct_union_enum_typedef(self, source_code: str, name: str, typedef_type: str) -> Optional[str]:
        """
        struct/union/enum型のtypedefを抽出
        
        Args:
            source_code: ソースコード
            name: typedef名
            typedef_type: 型の種類
        
        Returns:
            定義文字列 または None
        """
        # typedefキーワードから始まり、目的の名前で終わるパターンを検索
        # ネストした波括弧に対応
        
        # まず、typedef ... name; のパターンを見つける
        pattern = rf'typedef\s+{typedef_type}\s*{{.*?}}\s*{re.escape(name)}\s*;'
        
        # DotAllフラグで改行を含めて検索
        # ただし、ネストした波括弧には単純な正規表現では対応できない
        # 代わりに、手動で波括弧をカウントする方法を使用
        
        typedef_keyword = f'typedef {typedef_type}'
        typedef_positions = [m.start() for m in re.finditer(re.escape(typedef_keyword), source_code)]
        
        for start_pos in typedef_positions:
            # この位置から波括弧のバランスを取りながら終了位置を探す
            end_pos = self._find_typedef_end(source_code, start_pos, name)
            if end_pos > start_pos:
                definition = source_code[start_pos:end_pos].strip()
                # 名前で終わることを確認
                if re.search(rf'\s+{re.escape(name)}\s*;\s*$', definition):
                    return definition
        
        return None
    
    def _find_typedef_end(self, source_code: str, start_pos: int, target_name: str) -> int:
        """
        typedefの終了位置を検索（波括弧のバランスを考慮）
        
        Args:
            source_code: ソースコード
            start_pos: typedefの開始位置
            target_name: 探している型名
        
        Returns:
            終了位置（見つからない場合は-1）
        """
        pos = start_pos
        brace_depth = 0
        in_struct_union = False
        max_search = min(len(source_code), start_pos + 10000)
        
        while pos < max_search:
            char = source_code[pos]
            
            if char == '{':
                brace_depth += 1
                in_struct_union = True
            elif char == '}':
                brace_depth -= 1
            elif char == ';' and brace_depth == 0 and in_struct_union:
                # セミコロンが見つかり、波括弧が閉じている
                # この位置の前に目的の名前があるか確認
                segment = source_code[start_pos:pos+1]
                if re.search(rf'\s+{re.escape(target_name)}\s*;\s*$', segment):
                    return pos + 1
            
            pos += 1
        
        return -1
    
    def _extract_typedefs_by_regex(self, source_code: str) -> List[TypedefInfo]:
        """
        正規表現でtypedefを抽出（バックアップ手法）
        
        Args:
            source_code: ソースコード
        
        Returns:
            List[TypedefInfo]: 型定義情報のリスト
        """
        typedefs = []
        
        # typedef struct/union/enum の抽出
        # 改善: 波括弧のバランスを考慮した抽出
        for typedef_type in ['struct', 'union', 'enum']:
            typedef_keyword = f'typedef {typedef_type}'
            typedef_positions = [m.start() for m in re.finditer(re.escape(typedef_keyword), source_code)]
            
            for start_pos in typedef_positions:
                # 波括弧のバランスを取りながら終了位置を探す
                end_pos = self._find_generic_typedef_end(source_code, start_pos)
                if end_pos > start_pos:
                    definition = source_code[start_pos:end_pos].strip()
                    
                    # typedef名を抽出
                    name_match = re.search(r'\s+([A-Za-z_][A-Za-z0-9_]*)\s*;\s*$', definition)
                    if name_match:
                        name = name_match.group(1)
                        
                        # 依存関係を検出
                        dependencies = self._find_dependencies(definition)
                        
                        # 行番号を計算
                        line_number = source_code[:start_pos].count('\n') + 1
                        
                        typedefs.append(TypedefInfo(
                            name=name,
                            typedef_type=typedef_type,
                            definition=definition,
                            dependencies=dependencies,
                            line_number=line_number
                        ))
        
        # 基本型のtypedef
        pattern = r'typedef\s+([^;{]+?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;'
        
        for match in re.finditer(pattern, source_code):
            base_type = match.group(1).strip()
            name = match.group(2)
            
            # struct/union/enumは既に処理済みなのでスキップ
            if any(keyword in base_type for keyword in ['struct', 'union', 'enum']):
                continue
            
            definition = match.group(0)
            dependencies = self._find_dependencies(definition)
            line_number = source_code[:match.start()].count('\n') + 1
            
            typedefs.append(TypedefInfo(
                name=name,
                typedef_type='basic',
                definition=definition,
                dependencies=dependencies,
                line_number=line_number
            ))
        
        return typedefs
    
    def _find_generic_typedef_end(self, source_code: str, start_pos: int) -> int:
        """
        typedefの終了位置を検索（汎用版）
        
        Args:
            source_code: ソースコード
            start_pos: typedefの開始位置
        
        Returns:
            終了位置（見つからない場合は-1）
        """
        pos = start_pos
        brace_depth = 0
        found_open_brace = False
        max_search = min(len(source_code), start_pos + 10000)
        
        while pos < max_search:
            char = source_code[pos]
            
            if char == '{':
                brace_depth += 1
                found_open_brace = True
            elif char == '}':
                brace_depth -= 1
            elif char == ';' and brace_depth == 0 and found_open_brace:
                # セミコロンが見つかり、波括弧が全て閉じている
                return pos + 1
            
            pos += 1
        
        return -1
    
    def _find_dependencies(self, definition: str) -> List[str]:
        """
        型定義内の依存関係を検出
        
        Args:
            definition: 型定義の文字列
        
        Returns:
            依存する型名のリスト
        """
        dependencies = []
        
        # typedef名のパターン（通常は大文字で始まる、またはUtxなどのプレフィックス）
        # C言語の型名パターンを検出
        type_patterns = [
            r'\b([A-Z][A-Za-z0-9_]*)\b',  # 大文字で始まる型名
            r'\b(Ut[xm][0-9]+)\b',  # Utx, Utmで始まる型名
        ]
        
        for pattern in type_patterns:
            matches = re.findall(pattern, definition)
            dependencies.extend(matches)
        
        # 重複を除去
        dependencies = list(set(dependencies))
        
        # 標準型や予約語を除外
        standard_types = {
            'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
            'int8_t', 'int16_t', 'int32_t', 'int64_t',
            'size_t', 'bool', 'true', 'false',
            'void', 'char', 'short', 'int', 'long', 'float', 'double',
            'unsigned', 'signed', 'const', 'static', 'extern',
            'struct', 'union', 'enum', 'typedef'
        }
        
        dependencies = [dep for dep in dependencies if dep not in standard_types]
        
        return dependencies
    
    def get_typedef_by_name(self, name: str) -> Optional[TypedefInfo]:
        """
        名前で型定義を取得
        
        Args:
            name: typedef名
        
        Returns:
            TypedefInfo または None
        """
        for typedef in self.typedefs:
            if typedef.name == name:
                return typedef
        return None
    
    def get_all_typedef_names(self) -> Set[str]:
        """
        すべてのtypedef名を取得
        
        Returns:
            typedef名の集合
        """
        return {td.name for td in self.typedefs}
