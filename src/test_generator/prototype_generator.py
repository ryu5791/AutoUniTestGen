"""
PrototypeGeneratorモジュール

プロトタイプ宣言を生成
"""

import sys
import os
from typing import List, Set

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import ParsedData, TruthTableData


class PrototypeGenerator:
    """プロトタイプジェネレータ"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def generate_prototypes(self, truth_table: TruthTableData, parsed_data: ParsedData) -> str:
        """
        プロトタイプ宣言を生成
        
        Args:
            truth_table: 真偽表データ
            parsed_data: 解析済みデータ
        
        Returns:
            プロトタイプ宣言のコード
        """
        self.logger.info("プロトタイプ宣言の生成を開始")
        
        lines = []
        lines.append("// ===== プロトタイプ宣言 =====")
        lines.append("")
        
        # 1. モック/スタブ関数のプロトタイプ
        lines.append("// モック・スタブ関数")
        mock_protos = self._generate_mock_prototypes(parsed_data)
        lines.extend(mock_protos)
        lines.append("")
        
        # 2. テスト関数のプロトタイプ
        lines.append("// テスト関数")
        test_protos = self._generate_test_prototypes(truth_table)
        lines.extend(test_protos)
        lines.append("")
        
        # 3. ヘルパー関数のプロトタイプ
        lines.append("// ヘルパー関数")
        helper_protos = self._generate_helper_prototypes()
        lines.extend(helper_protos)
        
        self.logger.info("プロトタイプ宣言の生成が完了")
        
        return '\n'.join(lines)
    
    def _generate_mock_prototypes(self, parsed_data: ParsedData) -> List[str]:
        """
        モック関数のプロトタイプを生成
        
        Args:
            parsed_data: 解析済みデータ
        
        Returns:
            プロトタイプのリスト
        """
        protos = []
        
        for func_name in parsed_data.external_functions:
            # 戻り値の型を推定（簡易実装）
            return_type = self._guess_return_type(func_name)
            protos.append(f"static {return_type} mock_{func_name}(void);")
        
        # リセット関数
        protos.append("static void reset_all_mocks(void);")
        
        return protos
    
    def _generate_test_prototypes(self, truth_table: TruthTableData) -> List[str]:
        """
        テスト関数のプロトタイプを生成
        
        Args:
            truth_table: 真偽表データ
        
        Returns:
            プロトタイプのリスト
        """
        protos = []
        
        # テスト関数名を生成（TestFunctionGeneratorと同じロジック）
        from src.test_generator.test_function_generator import TestFunctionGenerator
        gen = TestFunctionGenerator()
        
        # 仮のParsedDataを作成（関数名の生成のみに使用）
        temp_parsed_data = ParsedData(
            file_name="temp.c",
            function_name=truth_table.function_name
        )
        
        for test_case in truth_table.test_cases:
            func_name = gen._generate_test_name(test_case, temp_parsed_data)
            protos.append(f"static void {func_name}(void);")
        
        return protos
    
    def _generate_helper_prototypes(self) -> List[str]:
        """
        ヘルパー関数のプロトタイプを生成
        
        Returns:
            プロトタイプのリスト
        """
        protos = []
        
        # setUp/tearDown
        protos.append("static void setUp(void);")
        protos.append("static void tearDown(void);")
        
        return protos
    
    def _guess_return_type(self, func_name: str) -> str:
        """
        関数名から戻り値の型を推定
        
        Args:
            func_name: 関数名
        
        Returns:
            型名
        """
        # 簡易的な型推定
        if func_name.startswith('f'):
            return 'uint16_t'
        elif func_name.startswith('mx'):
            return 'mx26'
        else:
            return 'int'


if __name__ == "__main__":
    # PrototypeGeneratorのテスト
    print("=" * 70)
    print("PrototypeGenerator のテスト")
    print("=" * 70)
    print()
    
    from src.data_structures import ParsedData, TruthTableData, TestCase
    
    # テスト用データ
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="test_func",
        external_functions=['f4', 'mx27', 'mx52']
    )
    
    truth_table = TruthTableData(
        function_name="test_func",
        test_cases=[
            TestCase(no=1, truth="T", condition="if (v10 > 30)", expected="真"),
            TestCase(no=2, truth="F", condition="if (v10 > 30)", expected="偽"),
            TestCase(no=3, truth="TF", condition="if ((a || b))", expected="左真"),
        ],
        total_tests=3
    )
    
    # プロトタイプを生成
    generator = PrototypeGenerator()
    prototypes = generator.generate_prototypes(truth_table, parsed_data)
    
    print("生成されたプロトタイプ宣言:")
    print("=" * 70)
    print(prototypes)
    print("=" * 70)
    print()
    
    print("✓ PrototypeGeneratorが正常に動作しました")
