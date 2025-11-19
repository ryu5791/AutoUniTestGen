#!/usr/bin/env python3
"""
Phase 4修正の統合テスト

Phase 4で実装した以下の機能を検証:
1. モック戻り値の自動決定
2. アサーションの期待値自動生成
3. 外部関数検出の改善
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser.c_code_parser import CCodeParser
from src.test_generator.test_function_generator import TestFunctionGenerator
from src.data_structures import TestCase, ConditionType, Condition


def print_section(title):
    """セクションヘッダーを表示"""
    print(f"\n{'=' * 70}")
    print(f"TEST: {title}")
    print('=' * 70)


def print_success(message):
    """成功メッセージを表示"""
    print(f"  ✓ {message}")


def print_failure(message):
    """失敗メッセージを表示"""
    print(f"  ✗ {message}")
    

def test_mock_return_value_determination():
    """モック戻り値の自動決定をテスト"""
    print_section("モック戻り値の自動決定")
    
    generator = TestFunctionGenerator()
    
    # テストケース1: func() > 10 で T の場合
    test_case1 = TestCase(
        no=1,
        truth='T',
        condition='func() > 10'
    )
    
    from src.data_structures import ParsedData
    parsed_data = ParsedData(
        file_name='test.c',
        function_name='test_func',
        external_functions=['func']
    )
    
    value = generator._determine_mock_return_value('func', test_case1, parsed_data)
    assert value == '11', f"Expected '11', got '{value}'"
    print_success(f"func() > 10 で T: 戻り値 = {value}")
    
    # テストケース2: func() > 10 で F の場合
    test_case2 = TestCase(
        no=2,
        truth='F',
        condition='func() > 10'
    )
    
    value = generator._determine_mock_return_value('func', test_case2, parsed_data)
    assert value == '10', f"Expected '10', got '{value}'"
    print_success(f"func() > 10 で F: 戻り値 = {value}")
    
    # テストケース3: func() < 20 で T の場合
    test_case3 = TestCase(
        no=3,
        truth='T',
        condition='func() < 20'
    )
    
    value = generator._determine_mock_return_value('func', test_case3, parsed_data)
    assert value == '19', f"Expected '19', got '{value}'"
    print_success(f"func() < 20 で T: 戻り値 = {value}")
    
    # テストケース4: func() == 5 で T の場合
    test_case4 = TestCase(
        no=4,
        truth='T',
        condition='func() == 5'
    )
    
    value = generator._determine_mock_return_value('func', test_case4, parsed_data)
    assert value == '5', f"Expected '5', got '{value}'"
    print_success(f"func() == 5 で T: 戻り値 = {value}")
    
    # テストケース5: 単純な関数呼び出し（真偽値）
    test_case5 = TestCase(
        no=5,
        truth='T',
        condition='func()'
    )
    
    value = generator._determine_mock_return_value('func', test_case5, parsed_data)
    assert value == '1', f"Expected '1', got '{value}'"
    print_success(f"func() で T: 戻り値 = {value}")
    
    print_success("モック戻り値の自動決定が正常に動作")


def test_external_function_detection():
    """外部関数検出をテスト"""
    print_section("外部関数検出の改善")
    
    parser = CCodeParser()
    
    # sample_with_mock.c を解析
    parsed = parser.parse('sample_with_mock.c', 'evaluate_sensor')
    
    assert parsed is not None, "解析に失敗"
    print_success("sample_with_mock.c の解析成功")
    
    assert 'get_sensor_value' in parsed.external_functions, \
        "get_sensor_value が検出されていない"
    print_success("get_sensor_value を検出")
    
    assert 'calculate_threshold' in parsed.external_functions, \
        "calculate_threshold が検出されていない"
    print_success("calculate_threshold を検出")
    
    assert len(parsed.external_functions) == 2, \
        f"外部関数数が不正: {len(parsed.external_functions)}"
    print_success(f"外部関数を {len(parsed.external_functions)} 個検出")
    
    print_success("外部関数検出が正常に動作")


def test_return_type_extraction():
    """戻り値型の抽出をテスト"""
    print_section("戻り値型の抽出")
    
    parser = CCodeParser()
    
    # sample.c を解析
    parsed = parser.parse('sample.c', 'calculate')
    
    assert parsed is not None, "解析に失敗"
    assert parsed.function_info is not None, "関数情報が取得できない"
    print_success("sample.c の解析成功")
    
    assert parsed.function_info.return_type == 'int', \
        f"戻り値型が不正: {parsed.function_info.return_type}"
    print_success(f"戻り値型: {parsed.function_info.return_type}")
    
    assert len(parsed.function_info.parameters) == 3, \
        f"パラメータ数が不正: {len(parsed.function_info.parameters)}"
    print_success(f"パラメータ数: {len(parsed.function_info.parameters)}")
    
    for param in parsed.function_info.parameters:
        print_success(f"  - {param['name']}: {param['type']}")
    
    print_success("戻り値型の抽出が正常に動作")


def test_assertion_generation():
    """アサーション生成をテスト"""
    print_section("アサーションの期待値生成")
    
    generator = TestFunctionGenerator()
    
    from src.data_structures import ParsedData, FunctionInfo
    
    # int型の戻り値を持つ関数
    func_info = FunctionInfo(
        name='test_func',
        return_type='int',
        parameters=[{'name': 'a', 'type': 'int'}]
    )
    
    parsed_data = ParsedData(
        file_name='test.c',
        function_name='test_func',
        function_info=func_info
    )
    
    # 真の分岐のテストケース
    test_case_t = TestCase(
        no=1,
        truth='T',
        condition='a > 10'
    )
    
    assertions = generator._generate_assertions(test_case_t, parsed_data)
    assert 'TEST_ASSERT_EQUAL' in assertions, "アサーションが生成されていない"
    assert 'result' in assertions, "result変数がチェックされていない"
    print_success("真の分岐: アサーション生成")
    print(f"    生成コード:\n{assertions}")
    
    # 偽の分岐のテストケース
    test_case_f = TestCase(
        no=2,
        truth='F',
        condition='a > 10'
    )
    
    assertions = generator._generate_assertions(test_case_f, parsed_data)
    assert 'TEST_ASSERT_EQUAL' in assertions, "アサーションが生成されていない"
    print_success("偽の分岐: アサーション生成")
    
    print_success("アサーションの期待値生成が正常に動作")


def test_integrated_test_generation():
    """統合的なテスト生成をテスト"""
    print_section("統合テスト生成")
    
    from src.c_test_auto_generator import CTestAutoGenerator
    
    generator = CTestAutoGenerator()
    
    # sample.c のテスト生成
    result = generator.generate_all(
        c_file_path='sample.c',
        target_function='calculate',
        output_dir='test_output_phase4_integration'
    )
    
    assert result.success, f"テスト生成に失敗: {result.error_message}"
    print_success("sample.c のテスト生成成功")
    
    # 生成されたファイルの確認
    test_file = 'test_output_phase4_integration/test_sample_calculate.c'
    assert os.path.exists(test_file), f"テストファイルが生成されていない: {test_file}"
    print_success(f"テストファイル生成: {test_file}")
    
    # 生成されたコードの内容を確認
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 重要な要素がコードに含まれているか確認
    checks = [
        ('result = 0', 'result変数の初期化'),
        ('result = calculate(', '関数呼び出しでresult代入'),
        ('TEST_ASSERT_EQUAL(', 'アサーション生成'),
    ]
    
    for pattern, description in checks:
        assert pattern in content, f"{description}が見つからない"
        print_success(description)
    
    print_success("統合テスト生成が正常に動作")


def main():
    """メイン関数"""
    print("\n" + "=" * 70)
    print("Phase 4修正 統合テスト開始")
    print("=" * 70)
    
    tests = [
        ("モック戻り値の自動決定", test_mock_return_value_determination),
        ("外部関数検出の改善", test_external_function_detection),
        ("戻り値型の抽出", test_return_type_extraction),
        ("アサーションの期待値生成", test_assertion_generation),
        ("統合テスト生成", test_integrated_test_generation),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            test_func()
            results.append((name, True))
        except AssertionError as e:
            print_failure(f"{name}: {str(e)}")
            results.append((name, False))
        except Exception as e:
            print_failure(f"{name}: 予期しないエラー - {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 結果サマリー
    print("\n" + "=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\n合計: {passed}/{total} テスト成功")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("✅ すべてのテストが成功しました！")
        print("=" * 70)
        print("\nPhase 4の修正が完了しました:")
        print("  ✓ モック戻り値の自動決定")
        print("  ✓ アサーションの期待値自動生成")
        print("  ✓ 外部関数検出の改善")
        print("  ✓ 戻り値型の正確な抽出")
        print("  ✓ 統合テスト生成の検証")
        return 0
    else:
        print("\n❌ 一部のテストが失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
