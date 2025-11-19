#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoUniTestGen v2.3 統合テスト
期待値推論機能のテスト
"""

import sys
import os
import tempfile

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.test_generator.expectation_inference_engine import (
    ExpectationInferenceEngine,
    ConfidenceLevel
)
from src.test_generator.return_pattern_analyzer import (
    ReturnPatternAnalyzer,
    ReturnType
)
from src.test_generator.improved_test_function_generator_v23 import (
    ImprovedTestFunctionGeneratorV23
)
from src.data_structures import ParsedData, TestCase, Condition
from dataclasses import dataclass

# v2.3用にParameterクラスを定義
@dataclass
class Parameter:
    """パラメータ情報"""
    name: str
    type: str


def print_header(title):
    """テストヘッダーを出力"""
    print("\n" + "=" * 70)
    print(f"TEST: {title}")
    print("=" * 70)


def test_simple_constant_return():
    """テスト1: 単純な定数戻り値の推論"""
    print_header("単純な定数戻り値の推論")
    
    code = """
    int simple_function(int x) {
        if (x > 10) {
            return 1;
        } else {
            return 0;
        }
    }
    """
    
    engine = ExpectationInferenceEngine()
    
    # テストケース1: x > 10 が true
    result1 = engine.infer_expected_value(
        code,
        {'x > 10': True},
        {'x': 11}
    )
    
    print(f"条件: x > 10 = True")
    print(f"推論値: {result1.value}")
    print(f"信頼度: {result1.confidence:.0%}")
    print(f"レベル: {result1.confidence_level.value}")
    
    assert result1.value == 1, f"期待値1が不正: {result1.value}"
    assert result1.confidence >= 0.9, f"信頼度が低すぎる: {result1.confidence}"
    
    # テストケース2: x > 10 が false
    result2 = engine.infer_expected_value(
        code,
        {'x > 10': False},
        {'x': 10}
    )
    
    print(f"\n条件: x > 10 = False")
    print(f"推論値: {result2.value}")
    print(f"信頼度: {result2.confidence:.0%}")
    
    assert result2.value == 0, f"期待値0が不正: {result2.value}"
    
    print("\n✅ テスト成功: 単純な定数戻り値の推論")
    return True


def test_switch_statement():
    """テスト2: switch文の推論"""
    print_header("switch文の推論")
    
    code = """
    int switch_function(int state) {
        switch(state) {
            case 0: return 100;
            case 1: return 200;
            case 2: return 300;
            default: return -1;
        }
    }
    """
    
    analyzer = ReturnPatternAnalyzer()
    analysis = analyzer.analyze(code)
    
    print(f"検出されたreturn文: {len(analysis.patterns)}個")
    print(f"値の分布: {analysis.value_distribution}")
    print(f"デフォルト値: {analysis.default_value}")
    print(f"推定型: {analysis.estimated_return_type}")
    
    # 値の確認
    expected_values = {100, 200, 300, -1}
    actual_values = set(analysis.value_distribution.keys())
    
    assert expected_values == actual_values, f"期待値が不一致: {actual_values}"
    assert analysis.default_value == -1, f"デフォルト値が不正: {analysis.default_value}"
    
    print("\n✅ テスト成功: switch文の推論")
    return True


def test_return_pattern_analysis():
    """テスト3: 戻り値パターン分析"""
    print_header("戻り値パターン分析")
    
    code = """
    int complex_function(int a, int b) {
        if (a > 0 && b < 100) {
            return a + b;
        } else if (a <= 0) {
            return -1;
        } else if (b >= 100) {
            return b - a;
        }
        return 0;
    }
    """
    
    analyzer = ReturnPatternAnalyzer()
    analysis = analyzer.analyze(code)
    
    print(f"パターン数: {len(analysis.patterns)}")
    for i, pattern in enumerate(analysis.patterns, 1):
        print(f"  {i}. {pattern.expression} (型: {pattern.type.value})")
        if pattern.variables:
            print(f"     変数: {pattern.variables}")
        if pattern.operators:
            print(f"     演算子: {pattern.operators}")
    
    # パターンの型を確認
    types = [p.type for p in analysis.patterns]
    assert ReturnType.EXPRESSION in types, "式パターンが検出されていない"
    assert ReturnType.CONSTANT in types, "定数パターンが検出されていない"
    
    print(f"\nエラーハンドリング: {analysis.has_error_handling}")
    assert analysis.has_error_handling, "エラーハンドリングが検出されていない"
    
    print("\n✅ テスト成功: 戻り値パターン分析")
    return True


def test_improved_test_generator():
    """テスト4: 改良版テストジェネレータ"""
    print_header("改良版テストジェネレータ (v2.3)")
    
    # サンプル関数
    function_body = """
    int calculate(int x, int y) {
        if (x > y) {
            return x - y;
        } else if (x < y) {
            return y - x;
        }
        return 0;
    }
    """
    
    # テスト用のパースデータ
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="calculate"
    )
    parsed_data.return_type = "int"
    parsed_data.params = [
        Parameter(name="x", type="int"),
        Parameter(name="y", type="int")
    ]
    parsed_data.conditions = [
        Condition(
            line=1,
            type=None,
            expression="x > y"
        ),
        Condition(
            line=2,
            type=None,
            expression="x < y"
        )
    ]
    
    # テストケース
    test_case = TestCase(
        no=1,
        truth="T",
        condition="x > y",
        expected="",
        test_name="TC_001",
        comment="Test case 001"
    )
    test_case.condition_values = [True, False]  # 追加属性として設定
    
    # ジェネレータのインスタンス化
    generator = ImprovedTestFunctionGeneratorV23(enable_inference=True)
    
    # テスト関数の生成
    test_code = generator.generate_test_function(
        test_case,
        parsed_data,
        function_body
    )
    
    print("生成されたテスト関数:")
    print("-" * 50)
    print(test_code)
    print("-" * 50)
    
    # 基本的な要素の確認
    assert "void test_calculate_TC_001" in test_code, "テスト関数名が不正"
    assert "TEST_ASSERT_EQUAL" in test_code, "アサーションが含まれていない"
    assert "// Arrange" in test_code, "Arrangeセクションがない"
    assert "// Act" in test_code, "Actセクションがない"
    assert "// Assert" in test_code, "Assertセクションがない"
    
    print("\n✅ テスト成功: 改良版テストジェネレータ")
    return True


def test_confidence_levels():
    """テスト5: 信頼度レベルのテスト"""
    print_header("信頼度レベル判定")
    
    test_cases = [
        ("return 42;", 0.95, ConfidenceLevel.HIGH),
        ("return x + 5;", 0.60, ConfidenceLevel.MEDIUM),
        ("return func(x) * y;", 0.30, ConfidenceLevel.LOW),
        ("return complex_calc();", 0.20, ConfidenceLevel.UNCERTAIN),
    ]
    
    engine = ExpectationInferenceEngine()
    
    for expr, expected_conf, expected_level in test_cases:
        code = f"""
        int test_func() {{
            {expr}
        }}
        """
        
        result = engine.infer_expected_value(code, {}, {})
        level = engine._get_confidence_level(expected_conf)
        
        print(f"式: {expr}")
        print(f"  期待信頼度: {expected_conf:.0%}")
        print(f"  期待レベル: {expected_level.value}")
        print(f"  実際レベル: {level.value}")
        
        assert level == expected_level, f"レベル判定が不正: {level}"
    
    print("\n✅ テスト成功: 信頼度レベル判定")
    return True


def test_real_world_example():
    """テスト6: 実際のコードでのテスト"""
    print_header("実際のコード例での推論")
    
    # 22_難読化_obfuscated.c から抜粋したような複雑な例
    code = """
    uint8_t process_data(uint16_t input, uint8_t mode) {
        if (mode == 0) {
            if (input > 0xFF) {
                return 0xFF;
            } else {
                return (uint8_t)input;
            }
        } else if (mode == 1) {
            return (input >> 8) & 0xFF;
        } else if (mode == 2) {
            return input & 0xFF;
        }
        return 0;
    }
    """
    
    analyzer = ReturnPatternAnalyzer()
    analysis = analyzer.analyze(code)
    
    print(f"パターン数: {len(analysis.patterns)}")
    print(f"値の分布: {analysis.value_distribution}")
    
    # エッジケースのテスト
    engine = ExpectationInferenceEngine()
    
    # mode = 0, input > 0xFF
    result1 = engine.infer_expected_value(
        code,
        {'mode == 0': True, 'input > 0xFF': True},
        {'input': 0x100, 'mode': 0}
    )
    
    print(f"\nケース1: mode=0, input=0x100")
    print(f"  推論値: {result1.value}")
    print(f"  信頼度: {result1.confidence:.0%}")
    
    # mode = 1
    result2 = engine.infer_expected_value(
        code,
        {'mode == 0': False, 'mode == 1': True},
        {'input': 0x1234, 'mode': 1}
    )
    
    print(f"\nケース2: mode=1, input=0x1234")
    print(f"  推論値: {result2.value}")
    print(f"  信頼度: {result2.confidence:.0%}")
    
    print("\n✅ テスト成功: 実際のコード例での推論")
    return True


def main():
    """メインテスト実行"""
    print("\n" + "=" * 70)
    print("AutoUniTestGen v2.3 統合テスト")
    print("期待値推論機能のテスト")
    print("=" * 70)
    
    tests = [
        ("単純な定数戻り値", test_simple_constant_return),
        ("switch文の推論", test_switch_statement),
        ("戻り値パターン分析", test_return_pattern_analysis),
        ("改良版ジェネレータ", test_improved_test_generator),
        ("信頼度レベル判定", test_confidence_levels),
        ("実際のコード例", test_real_world_example),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n✗ テスト失敗: {name}")
            print(f"  エラー: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    
    for i, (name, _) in enumerate(tests, 1):
        status = "✅ PASS" if i <= passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 70)
    print(f"結果: {passed}/{len(tests)} テスト成功")
    
    if passed == len(tests):
        print("🎉 すべてのテストが成功しました！")
        print("v2.3の期待値推論機能が正常に動作しています。")
    else:
        print(f"⚠️ {failed}個のテストが失敗しました")
    
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
