"""
VariableExtractor - テスト関数から入出力変数を抽出

テストコードから:
- 入力変数（初期化されている変数）
- 出力変数（検証されている変数）
- 各変数の値
を抽出する
"""

import re
import logging
from typing import Dict, List, Any, Set, Tuple


class VariableExtractor:
    """テスト関数から変数を抽出するクラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_from_test_function(self, test_function: str) -> Dict[str, Any]:
        """
        テスト関数から入出力変数を抽出
        
        Args:
            test_function: テスト関数のソースコード文字列
            
        Returns:
            {
                'test_name': テスト関数名,
                'inputs': {変数名: 値},
                'outputs': {変数名: 値}
            }
        """
        result = {
            'test_name': '',
            'inputs': {},
            'outputs': {}
        }
        
        # テスト関数名を抽出
        result['test_name'] = self._extract_function_name(test_function)
        
        # 入力変数を抽出（初期化されている変数）
        result['inputs'] = self._extract_input_variables(test_function)
        
        # 出力変数を抽出（TEST_ASSERT_EQUALで検証されている変数）
        result['outputs'] = self._extract_output_variables(test_function)
        
        return result
    
    def _extract_function_name(self, test_function: str) -> str:
        """
        テスト関数名を抽出
        
        Args:
            test_function: テスト関数のソースコード
            
        Returns:
            関数名
        """
        # void test_XX_...() の形式から関数名を抽出
        match = re.search(r'void\s+(test_\w+)\s*\(', test_function)
        if match:
            return match.group(1)
        
        return ""
    
    def _extract_input_variables(self, test_function: str) -> Dict[str, Any]:
        """
        入力変数を抽出（初期化されている変数）
        
        Args:
            test_function: テスト関数のソースコード
            
        Returns:
            {変数名: 値}の辞書
        """
        inputs = {}
        
        # "// 変数を初期化" セクションから値を抽出
        # パターン: 変数名 = 値;
        pattern = r'(\w+)\s*=\s*([^;]+);'
        
        # 初期化セクションを抽出（"// 変数を初期化" から "// モックを設定" まで）
        init_section_match = re.search(
            r'//\s*変数を初期化.*?//\s*モックを設定',
            test_function,
            re.DOTALL
        )
        
        if init_section_match:
            init_section = init_section_match.group(0)
            
            # 変数初期化を抽出
            for match in re.finditer(pattern, init_section):
                var_name = match.group(1).strip()
                value = match.group(2).strip()
                
                # モック変数は除外
                if not var_name.startswith('mock_'):
                    inputs[var_name] = self._parse_value(value)
        
        return inputs
    
    def _extract_output_variables(self, test_function: str) -> Dict[str, Any]:
        """
        出力変数を抽出（TEST_ASSERT_EQUALで検証されている変数）
        
        Args:
            test_function: テスト関数のソースコード
            
        Returns:
            {変数名: 期待値}の辞書
        """
        outputs = {}
        
        # TEST_ASSERT_EQUALのパターン
        # TEST_ASSERT_EQUAL(期待値, 実際値);
        pattern = r'TEST_ASSERT_EQUAL\s*\(\s*([^,]+)\s*,\s*(\w+)\s*\)'
        
        for match in re.finditer(pattern, test_function):
            expected_value = match.group(1).strip()
            actual_var = match.group(2).strip()
            
            # モック変数のチェックは除外
            if not actual_var.endswith('_call_count'):
                # 期待値が /* */ コメントなら "-" に変換
                if expected_value.startswith('/*') and expected_value.endswith('*/'):
                    outputs[actual_var] = '-'
                else:
                    outputs[actual_var] = self._parse_value(expected_value)
        
        return outputs
    
    def _parse_value(self, value_str: str) -> Any:
        """
        値の文字列をパースして適切な型に変換
        
        Args:
            value_str: 値の文字列
            
        Returns:
            パースされた値
        """
        value_str = value_str.strip()
        
        # TODOコメントが含まれている場合
        if 'TODO' in value_str or '/*' in value_str:
            return '-'
        
        # 数値（整数）
        if re.match(r'^-?\d+$', value_str):
            return int(value_str)
        
        # 数値（浮動小数点）
        if re.match(r'^-?\d+\.\d+$', value_str):
            return float(value_str)
        
        # 16進数
        if value_str.startswith('0x') or value_str.startswith('0X'):
            try:
                return int(value_str, 16)
            except ValueError:
                return value_str
        
        # 文字列リテラル
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        
        # その他（識別子、enum値など）はそのまま
        return value_str
    
    def extract_all_variables_from_code(self, test_code: str) -> Tuple[Set[str], Set[str]]:
        """
        テストコード全体から入力変数と出力変数のリストを抽出
        
        Args:
            test_code: 完全なテストコード
            
        Returns:
            (入力変数セット, 出力変数セット)
        """
        input_vars = set()
        output_vars = set()
        
        # 各テスト関数を分割
        test_functions = self._split_test_functions(test_code)
        
        for test_func in test_functions:
            data = self.extract_from_test_function(test_func)
            input_vars.update(data['inputs'].keys())
            output_vars.update(data['outputs'].keys())
        
        return input_vars, output_vars
    
    def _split_test_functions(self, test_code: str) -> List[str]:
        """
        テストコードを各テスト関数に分割
        
        Args:
            test_code: 完全なテストコード
            
        Returns:
            テスト関数のリスト
        """
        functions = []
        
        # void test_で始まる関数を抽出
        # 関数の開始から次の関数の開始まで、または終了まで
        pattern = r'(void\s+test_\w+\s*\([^)]*\)\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\})'
        
        for match in re.finditer(pattern, test_code, re.DOTALL):
            functions.append(match.group(1))
        
        return functions


if __name__ == "__main__":
    # VariableExtractorのテスト
    print("=== VariableExtractor のテスト ===\n")
    
    # サンプルテスト関数
    sample_test = """
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
    TEST_ASSERT_EQUAL(/* 期待値 */, status);

    // 呼び出し回数を確認
    TEST_ASSERT_EQUAL(1, mock_f4_call_count);
}
"""
    
    extractor = VariableExtractor()
    result = extractor.extract_from_test_function(sample_test)
    
    print(f"テスト関数名: {result['test_name']}")
    print(f"\n入力変数:")
    for var, val in result['inputs'].items():
        print(f"  {var} = {val}")
    
    print(f"\n出力変数:")
    for var, val in result['outputs'].items():
        print(f"  {var} = {val}")
    
    print("\n✓ VariableExtractorが正常に動作しました")
