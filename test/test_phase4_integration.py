"""
Phase 4 統合テスト

C言語ファイル → 真偽表Excel → Unityテストコード
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser.c_code_parser import CCodeParser
from src.truth_table.truth_table_generator import TruthTableGenerator
from src.test_generator.unity_test_generator import UnityTestGenerator
from src.output.excel_writer import ExcelWriter


def test_phase4_integration():
    """Phase 4の統合テスト"""
    
    print("=" * 80)
    print("Phase 4 統合テスト: C言語ファイル → Unityテストコード")
    print("=" * 80)
    print()
    
    # テスト用サンプルコードを作成
    test_code = """
typedef unsigned char uint8_t;
typedef short int16_t;
typedef unsigned short uint16_t;

typedef enum {
    m46 = 0,
    m47,
    m48,
    mx2
} mx26;

uint16_t f4(void);
mx26 mx27(void);
void mx31(int param);

mx26 mx63;
uint16_t v9;
int16_t v10;

void f1(void) {
    if ((f4() & 223) != 0) {
        v9 = 7;
    }
    
    if ((mx63 == m47) || (mx63 == m46)) {
        mx63 = mx27();
        if ((mx63 == m48) || (mx63 == mx2)) {
            mx31(64);
        }
    }
    
    switch (v9) {
        case 0:
            v10 = 0;
            break;
        case 1:
            if (v10 > 30) {
                v9 = 2;
            }
            break;
        case 2:
            if (v10 < -30) {
                v9 = 3;
            }
            break;
        default:
            break;
    }
}
"""
    
    # テストファイルに書き込み
    test_file = "/tmp/test_phase4_integration.c"
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    print(f"【Step 1】テストファイルを作成: {test_file}")
    print()
    
    # Step 1: C言語ファイルを解析
    print("【Step 2】C言語ファイルを解析中...")
    parser = CCodeParser()
    parsed_data = parser.parse(test_file, target_function="f1")
    
    if not parsed_data:
        print("❌ 解析に失敗しました")
        return False
    
    print(f"   ✓ 解析完了")
    print(f"   - 関数名: {parsed_data.function_name}")
    print(f"   - 条件分岐数: {len(parsed_data.conditions)}")
    print(f"   - 外部関数: {parsed_data.external_functions}")
    print(f"   - グローバル変数: {parsed_data.global_variables}")
    print()
    
    # Step 2: 真偽表を生成
    print("【Step 3】MC/DC真偽表を生成中...")
    truth_gen = TruthTableGenerator()
    truth_table = truth_gen.generate(parsed_data)
    
    print(f"   ✓ 真偽表生成完了")
    print(f"   - 総テストケース数: {truth_table.total_tests}")
    print()
    
    # Excelに出力
    excel_file = "/tmp/truth_table_phase4.xlsx"
    writer = ExcelWriter()
    writer.write_truth_table(truth_table, excel_file)
    print(f"   ✓ Excel出力: {excel_file}")
    print()
    
    # Step 3: Unityテストコードを生成
    print("【Step 4】Unityテストコードを生成中...")
    test_gen = UnityTestGenerator()
    test_code = test_gen.generate(truth_table, parsed_data)
    
    print(f"   ✓ テストコード生成完了")
    print()
    
    # ファイルに保存
    test_output = "/tmp/test_f1_generated.c"
    test_code.save(test_output)
    
    # コード統計
    full_code = test_code.to_string()
    lines = full_code.split('\n')
    
    print("【Step 5】生成されたコードの統計")
    print(f"   - 総行数: {len(lines)}行")
    print(f"   - テスト関数数: {len(truth_table.test_cases)}個")
    print(f"   - モック関数数: {len(parsed_data.external_functions)}個")
    print()
    
    # コードの一部を表示
    print("【Step 6】生成されたコードのサンプル（最初の50行）")
    print("-" * 80)
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3d}: {line}")
    print(f"\n... 他 {len(lines) - 50} 行")
    print("-" * 80)
    print()
    
    # ファイルサイズ
    import os
    file_size = os.path.getsize(test_output)
    print(f"   ✓ テストファイル保存: {test_output}")
    print(f"   - ファイルサイズ: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print()
    
    # 統計サマリー
    print("=" * 80)
    print("【統計サマリー】")
    print("=" * 80)
    print()
    
    from collections import Counter
    
    # 条件タイプ別
    type_counts = Counter(cond.type.value for cond in parsed_data.conditions)
    print("条件タイプ別の分布:")
    for cond_type, count in sorted(type_counts.items()):
        print(f"  - {cond_type:20s}: {count:2d}個")
    print()
    
    # 真偽パターン別
    truth_counts = Counter(tc.truth for tc in truth_table.test_cases if tc.truth and tc.truth != '-')
    print("真偽パターン別の分布:")
    for truth, count in sorted(truth_counts.items()):
        print(f"  - {truth:3s}: {count:2d}個")
    print()
    
    print("=" * 80)
    print("✅ Phase 4 統合テスト完了！")
    print("=" * 80)
    print()
    print("生成されたファイル:")
    print(f"  1. 真偽表Excel: {excel_file}")
    print(f"  2. Unityテストコード: {test_output}")
    print()
    
    return True


if __name__ == "__main__":
    success = test_phase4_integration()
    sys.exit(0 if success else 1)
