"""
DependencyResolverモジュール

型定義の依存関係を解決し、正しい順序で並べる
"""

import sys
import os
from typing import List, Dict, Set, Optional
from collections import deque

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class CircularDependencyError(Exception):
    """循環依存エラー"""
    pass


class DependencyResolver:
    """依存関係解決器"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def resolve_order(self, typedefs: List) -> List:
        """
        型定義を依存関係に基づいてソート
        
        Args:
            typedefs: List[TypedefInfo]
        
        Returns:
            List[TypedefInfo]: ソート済みの型定義リスト
        
        Raises:
            CircularDependencyError: 循環依存が検出された場合
        """
        if not typedefs:
            return []
        
        # 型名をキーとした辞書を作成
        typedef_dict = {td.name: td for td in typedefs}
        
        # 依存関係グラフを構築
        dependencies = self._build_dependency_graph(typedefs, typedef_dict)
        
        # 循環依存をチェック
        if self._has_circular_dependency(dependencies):
            self.logger.warning("循環依存が検出されました")
            # 循環依存がある場合は元の順序を保持
            return typedefs
        
        # トポロジカルソート
        sorted_names = self._topological_sort(dependencies)
        
        # ソートされた順序でTypedefInfoを並べる
        result = []
        for name in sorted_names:
            if name in typedef_dict:
                result.append(typedef_dict[name])
        
        # ソートに含まれていない型定義を追加
        sorted_set = set(sorted_names)
        for td in typedefs:
            if td.name not in sorted_set:
                result.append(td)
        
        self.logger.info(f"{len(result)}個の型定義を依存順序でソートしました")
        return result
    
    def _build_dependency_graph(self, typedefs: List, typedef_dict: Dict) -> Dict[str, Set[str]]:
        """
        依存関係グラフを構築
        
        Args:
            typedefs: 型定義のリスト
            typedef_dict: 型名をキーとした辞書
        
        Returns:
            依存関係グラフ {型名: {依存する型名の集合}}
        """
        graph = {}
        typedef_names = set(typedef_dict.keys())
        
        for td in typedefs:
            # この型が依存している他の型を抽出
            deps = set()
            for dep_name in td.dependencies:
                # typedef内に存在する型名のみを依存関係に含める
                if dep_name in typedef_names and dep_name != td.name:
                    deps.add(dep_name)
            
            graph[td.name] = deps
        
        return graph
    
    def _topological_sort(self, dependencies: Dict[str, Set[str]]) -> List[str]:
        """
        トポロジカルソート（Kahn's algorithm）
        
        Args:
            dependencies: 依存関係グラフ {ノード: {このノードが依存している型の集合}}
        
        Returns:
            ソートされたノードのリスト（依存される型が先、依存する型が後）
        """
        # 逆方向のグラフを構築（被依存関係）
        # A depends on B → B is depended by A
        reverse_graph = {node: set() for node in dependencies}
        in_degree = {node: 0 for node in dependencies}
        
        for node, deps in dependencies.items():
            for dep in deps:
                if dep in reverse_graph:
                    reverse_graph[dep].add(node)
                    in_degree[node] += 1
        
        # 入次数0のノードをキューに追加
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            # キューから取り出し
            node = queue.popleft()
            result.append(node)
            
            # このノードに依存しているノードの入次数を減らす
            for dependent in reverse_graph[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # すべてのノードが処理されたかチェック
        if len(result) != len(dependencies):
            self.logger.warning(f"トポロジカルソートが完全に実行できませんでした: {len(result)}/{len(dependencies)}")
        
        return result
    
    def _has_circular_dependency(self, dependencies: Dict[str, Set[str]]) -> bool:
        """
        循環依存の検出（深さ優先探索）
        
        Args:
            dependencies: 依存関係グラフ
        
        Returns:
            循環依存がある場合True
        """
        # 訪問状態: 0=未訪問, 1=訪問中, 2=訪問済み
        visited = {node: 0 for node in dependencies}
        
        def dfs(node: str) -> bool:
            """深さ優先探索で循環を検出"""
            if visited[node] == 1:  # 訪問中のノードに再訪 → 循環
                return True
            if visited[node] == 2:  # 訪問済み
                return False
            
            visited[node] = 1  # 訪問中
            
            # 依存先を探索
            for dep in dependencies.get(node, []):
                if dep in visited and dfs(dep):
                    return True
            
            visited[node] = 2  # 訪問済み
            return False
        
        # すべてのノードから探索
        for node in dependencies:
            if visited[node] == 0:
                if dfs(node):
                    self.logger.warning(f"循環依存を検出: {node} が関与しています")
                    return True
        
        return False
    
    def get_dependency_chain(self, typedef_name: str, typedefs: List) -> List[str]:
        """
        特定の型定義の依存チェーンを取得
        
        Args:
            typedef_name: 型名
            typedefs: 型定義のリスト
        
        Returns:
            依存チェーン（この型が依存している型のリスト）
        """
        typedef_dict = {td.name: td for td in typedefs}
        
        if typedef_name not in typedef_dict:
            return []
        
        visited = set()
        chain = []
        
        def collect_deps(name: str):
            """再帰的に依存を収集"""
            if name in visited:
                return
            visited.add(name)
            
            if name not in typedef_dict:
                return
            
            td = typedef_dict[name]
            for dep in td.dependencies:
                if dep in typedef_dict:
                    collect_deps(dep)
                    if dep not in chain:
                        chain.append(dep)
        
        collect_deps(typedef_name)
        return chain
    
    def validate_dependencies(self, typedefs: List) -> Dict[str, List[str]]:
        """
        依存関係の検証
        
        Args:
            typedefs: 型定義のリスト
        
        Returns:
            検証結果 {型名: [エラーメッセージのリスト]}
        """
        typedef_names = {td.name for td in typedefs}
        errors = {}
        
        for td in typedefs:
            td_errors = []
            
            # 未定義の型への依存をチェック
            for dep in td.dependencies:
                if dep not in typedef_names:
                    # 標準型かどうかチェック
                    if not self._is_standard_type(dep):
                        td_errors.append(f"未定義の型 '{dep}' に依存しています")
            
            if td_errors:
                errors[td.name] = td_errors
        
        return errors
    
    def _is_standard_type(self, type_name: str) -> bool:
        """
        標準型かどうかチェック
        
        Args:
            type_name: 型名
        
        Returns:
            標準型の場合True
        """
        standard_types = {
            'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
            'int8_t', 'int16_t', 'int32_t', 'int64_t',
            'size_t', 'bool', 'void', 'char', 'short', 'int', 'long',
            'float', 'double', 'unsigned', 'signed'
        }
        
        return type_name in standard_types
