"""
IOTableGenerator - I/O表データの生成

生成されたテストコードと真偽表から、I/O一覧表を生成する。
各テストケースの入力変数と出力変数の値を抽出し、
Excel形式の表を作成する。
"""

import logging
from typing import List, Dict, Any, Set
import sys
import os

# パスを追加（親ディレクトリのモジュールをインポートするため）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.data_structures import IOTableData, TruthTableData, TestCode
from src.io_table.variable_extractor import VariableExtractor


class IOTableGenerator:
    """I/O表を生成するクラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.var_extractor = VariableExtractor()
    
    def generate(self, test_code: TestCode, truth_table: TruthTableData) -> IOTableData:
        """
        I/O表を生成
        
        Args:
            test_code: 生成されたテストコード
            truth_table: 真偽表データ
            
        Returns:
            I/O表データ
        """
        self.logger.info(f"I/O表を生成: {truth_table.function_name}")
        
        # テストコード全体を文字列として取得
        full_code = test_code.to_string()
        
        # 全テストケースの入出力変数を収集
        input_vars, output_vars = self._collect_all_variables(full_code)
        
        # テストデータを生成
        test_data = self._generate_test_data(full_code, truth_table.test_cases)
        
        # I/O表データを構築
        io_table = IOTableData(
            input_variables=sorted(input_vars),   # ソートして順序を安定化
            output_variables=sorted(output_vars),
            test_data=test_data
        )
        
        self.logger.info(
            f"I/O表生成完了: "
            f"入力変数={len(input_vars)}, "
            f"出力変数={len(output_vars)}, "
            f"テスト={len(test_data)}"
        )
        
        return io_table
    
    def _collect_all_variables(self, test_code: str) -> tuple:
        """
        テストコード全体から入出力変数を収集
        
        Args:
            test_code: 完全なテストコード
            
        Returns:
            (入力変数セット, 出力変数セット)
        """
        self.logger.debug("全テストから変数を収集")
        
        input_vars, output_vars = self.var_extractor.extract_all_variables_from_code(test_code)
        
        # モック変数を除外
        input_vars = {v for v in input_vars if not v.startswith('mock_')}
        output_vars = {v for v in output_vars if not v.startswith('mock_')}
        
        return input_vars, output_vars
    
    def _generate_test_data(self, test_code: str, test_cases: List) -> List[Dict[str, Any]]:
        """
        各テストケースのデータを生成
        
        Args:
            test_code: テストコード
            test_cases: 真偽表のテストケースリスト
            
        Returns:
            テストデータのリスト
        """
        test_data = []
        
        # テスト関数を分割
        test_functions = self.var_extractor._split_test_functions(test_code)
        
        # 各テスト関数から変数を抽出
        for test_func in test_functions:
            data = self.var_extractor.extract_from_test_function(test_func)
            
            # テスト名が取得できた場合のみ追加
            if data['test_name']:
                test_data.append(data)
        
        # テストケース番号を追加（真偽表との対応）
        for i, td in enumerate(test_data):
            if i < len(test_cases):
                td['test_case_no'] = test_cases[i].no
        
        return test_data
    
    def _fill_missing_values(
        self,
        test_data: List[Dict[str, Any]],
        all_input_vars: Set[str],
        all_output_vars: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        各テストデータで未使用の変数に "-" を埋める
        
        Args:
            test_data: テストデータリスト
            all_input_vars: 全入力変数
            all_output_vars: 全出力変数
            
        Returns:
            "-" で埋められたテストデータ
        """
        for td in test_data:
            # 入力変数で未定義のものに "-" を設定
            for var in all_input_vars:
                if var not in td['inputs']:
                    td['inputs'][var] = '-'
            
            # 出力変数で未定義のものに "-" を設定
            for var in all_output_vars:
                if var not in td['outputs']:
                    td['outputs'][var] = '-'
        
        return test_data


if __name__ == "__main__":
    # IOTableGeneratorのテスト
    print("=== IOTableGenerator のテスト ===\n")
    
    from src.data_structures import TestCase
    
    # サンプルテストコード
    sample_code = """
void test_01_v10_gt_30_T(void) {
    // 変数を初期化
    v10 = 31;
    mx63 = m47;

    // モックを設定
    mock_f4_return_value = 1;

    // 対象関数を実行
    f1();

    // 結果を確認
    TEST_ASSERT_EQUAL(7, v9);
    TEST_ASSERT_EQUAL(1, status);

    // 呼び出し回数を確認
    TEST_ASSERT_EQUAL(1, mock_f4_call_count);
}

void test_02_v10_gt_30_F(void) {
    // 変数を初期化
    v10 = 30;
    mx63 = m46;

    // モックを設定
    mock_f4_return_value = 0;

    // 対象関数を実行
    f1();

    // 結果を確認
    TEST_ASSERT_EQUAL(0, v9);
    TEST_ASSERT_EQUAL(/* 期待値 */, status);

    // 呼び出し回数を確認
    TEST_ASSERT_EQUAL(0, mock_f4_call_count);
}
"""
    
    # TestCodeオブジェクトを作成
    test_code = TestCode(
        test_functions=sample_code
    )
    
    # TruthTableDataを作成
    truth_table = TruthTableData(
        function_name="f1",
        test_cases=[
            TestCase(no=1, truth="T", condition="if (v10 > 30)", expected="v10が31"),
            TestCase(no=2, truth="F", condition="if (v10 > 30)", expected="v10が30"),
        ],
        total_tests=2
    )
    
    # I/O表を生成
    generator = IOTableGenerator()
    io_table = generator.generate(test_code, truth_table)
    
    print("生成されたI/O表:")
    print(f"  入力変数: {io_table.input_variables}")
    print(f"  出力変数: {io_table.output_variables}")
    print(f"  テストデータ数: {len(io_table.test_data)}")
    print()
    
    print("テストデータ:")
    for i, td in enumerate(io_table.test_data, 1):
        print(f"\n  テスト{i}: {td['test_name']}")
        print(f"    入力: {td['inputs']}")
        print(f"    出力: {td['outputs']}")
    
    print("\n✓ IOTableGeneratorが正常に動作しました")
