"""
Phase 3 統合テスト

C言語ファイルから真偽表Excelを生成
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser.c_code_parser import CCodeParser
from src.truth_table.truth_table_generator import TruthTableGenerator
from src.output.excel_writer import ExcelWriter


def test_phase3_integration():
    """Phase 3の統合テスト"""
    
    print("=" * 70)
    print("Phase 3 統合テスト: C言語ファイル → 真偽表Excel")
    print("=" * 70)
    print()
    
    # テスト用サンプルコードを作成
    test_code = """
typedef unsigned char uint8_t;
typedef short int16_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;

typedef enum {
    m46 = 0,
    m47,
    m48,
    mx2
} mx26;

typedef enum {
    m52 = 0
} mx42;

uint16_t f4(void);
mx26 mx27(void);
void mx31(int param);
mx42 mx52(void);
uint8_t f18(void);

mx26 mx63;
uint16_t v9;
uint32_t v7[2];
int16_t v10;

void f1(void) {
    /* 条件1: 単純なif文 */
    if ((f4() & 223) != 0) {
        v9 = 7;
    }
    
    /* 条件2: OR条件 */
    if ((mx63 == m47) || (mx63 == m46)) {
        mx63 = mx27();
        
        /* 条件3: ネストしたOR条件 */
        if ((mx63 == m48) || (mx63 == mx2)) {
            mx31(64);
        }
    }
    
    /* 条件4: switch文 */
    switch (v9) {
        case 0:
            break;
        case 1:
            /* 条件5: switch内のif文 */
            if (mx52() == m52) {
                /* 条件6: さらにネストしたif文 */
                if (v7[0] == 0) {
                    /* 条件7: 境界値テスト用 */
                    if (v10 < -30) {
                        v9 = 2;
                    }
                }
            }
            break;
        case 2:
            break;
        case 3:
            /* 条件8: 境界値テスト用 */
            if (v10 > 30) {
                v9 = 4;
            }
            break;
        case 4:
            /* 条件9: 単純条件 */
            if (f18() != 0) {
                v9 = 5;
            }
            break;
        default:
            break;
    }
}
"""
    
    # テストファイルに書き込み
    test_file = "/tmp/test_phase3_integration.c"
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    print(f"1. テストファイルを作成: {test_file}")
    print()
    
    # Step 1: C言語ファイルを解析
    print("2. C言語ファイルを解析中...")
    parser = CCodeParser()
    parsed_data = parser.parse(test_file, target_function="f1")
    
    if not parsed_data:
        print("❌ 解析に失敗しました")
        return False
    
    print(f"   ✓ 解析完了")
    print(f"   - 関数名: {parsed_data.function_name}")
    print(f"   - 条件分岐数: {len(parsed_data.conditions)}")
    print(f"   - 外部関数: {parsed_data.external_functions}")
    print()
    
    # 検出された条件を表示
    print("3. 検出された条件分岐:")
    for i, cond in enumerate(parsed_data.conditions, 1):
        print(f"   {i}. [{cond.type.value:15s}] {cond.expression}")
        if cond.operator:
            print(f"      左辺: {cond.left}")
            print(f"      右辺: {cond.right}")
        if cond.cases:
            print(f"      cases: {cond.cases}")
    print()
    
    # Step 2: 真偽表を生成
    print("4. 真偽表を生成中...")
    generator = TruthTableGenerator()
    truth_table = generator.generate(parsed_data)
    
    print(f"   ✓ 真偽表生成完了")
    print(f"   - 総テストケース数: {truth_table.total_tests}")
    print()
    
    # テストケースの一部を表示
    print("5. 生成されたテストケース（最初の10個）:")
    for tc in truth_table.test_cases[:10]:
        print(f"   {tc.no:2d}. [{tc.truth:3s}] {tc.condition[:60]}")
    if len(truth_table.test_cases) > 10:
        print(f"   ... 他 {len(truth_table.test_cases) - 10} 件")
    print()
    
    # Step 3: Excelファイルに出力
    print("6. Excelファイルに出力中...")
    output_file = "/tmp/truth_table_f1.xlsx"
    writer = ExcelWriter()
    writer.write_truth_table(truth_table, output_file)
    
    print(f"   ✓ Excel出力完了: {output_file}")
    print()
    
    # 統計情報を表示
    print("=" * 70)
    print("統計情報")
    print("=" * 70)
    
    # 条件タイプ別の集計
    from collections import Counter
    type_counts = Counter(cond.type.value for cond in parsed_data.conditions)
    
    print("\n条件タイプ別の分布:")
    for cond_type, count in type_counts.items():
        print(f"  - {cond_type:20s}: {count:2d}個")
    
    # 真偽パターン別の集計
    truth_counts = Counter(tc.truth for tc in truth_table.test_cases)
    print("\n真偽パターン別の分布:")
    for truth, count in sorted(truth_counts.items()):
        if truth and truth != '-':
            print(f"  - {truth:3s}: {count:2d}個")
    
    print("\n" + "=" * 70)
    print("✅ Phase 3 統合テスト完了！")
    print("=" * 70)
    print(f"\n生成されたファイル: {output_file}")
    
    return True


if __name__ == "__main__":
    success = test_phase3_integration()
    sys.exit(0 if success else 1)
