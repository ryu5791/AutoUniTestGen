"""
Phase 5 統合テスト

C言語ファイル → 真偽表Excel → Unityテストコード → I/O表Excel
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser.c_code_parser import CCodeParser
from src.truth_table.truth_table_generator import TruthTableGenerator
from src.test_generator.unity_test_generator import UnityTestGenerator
from src.io_table.io_table_generator import IOTableGenerator
from src.output.excel_writer import ExcelWriter


def test_phase5_integration():
    """Phase 5の統合テスト"""
    
    print("=" * 80)
    print("Phase 5 統合テスト: C言語ファイル → I/O表Excel")
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
    test_file = "/tmp/test_phase5_integration.c"
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    print(f"【Step 1】テストファイルを作成: {test_file}")
    print()
    
    try:
        # Step 2: C言語ファイルを解析
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
        print(f"   - enum値: {parsed_data.enum_values}")
        print()
        
        # Step 3: 真偽表を生成
        print("【Step 3】MC/DC真偽表を生成中...")
        truth_gen = TruthTableGenerator()
        truth_table = truth_gen.generate(parsed_data)
        
        print(f"   ✓ 真偽表生成完了")
        print(f"   - 総テストケース数: {truth_table.total_tests}")
        print()
        
        # Step 4: Unityテストコードを生成
        print("【Step 4】Unityテストコードを生成中...")
        test_gen = UnityTestGenerator()
        test_code = test_gen.generate(truth_table, parsed_data)
        
        print(f"   ✓ テストコード生成完了")
        print()
        
        # Step 5: I/O表を生成 (Phase 5の主要機能)
        print("【Step 5】I/O表を生成中...")
        io_gen = IOTableGenerator()
        io_table = io_gen.generate(test_code, truth_table)
        
        print(f"   ✓ I/O表生成完了")
        print(f"   - 入力変数数: {len(io_table.input_variables)}")
        print(f"   - 出力変数数: {len(io_table.output_variables)}")
        print(f"   - テストデータ数: {len(io_table.test_data)}")
        print()
        
        # Step 6: I/O表をExcelに出力
        print("【Step 6】I/O表をExcelに出力中...")
        output_file = "/tmp/io_table_phase5_bugfix_test.xlsx"
        writer = ExcelWriter()
        writer.write_io_table(io_table, output_file)
        
        print(f"   ✓ Excel出力完了: {output_file}")
        print()
        
        # Step 7: I/O表の内容を確認
        print("【Step 7】I/O表の内容確認")
        print(f"   入力変数: {io_table.input_variables}")
        print(f"   出力変数: {io_table.output_variables}")
        print()
        
        if io_table.test_data:
            print("   最初のテストデータ:")
            first_test = io_table.test_data[0]
            print(f"     テスト名: {first_test.get('test_name', 'N/A')}")
            print(f"     入力値: {first_test.get('inputs', {})}")
            print(f"     出力値: {first_test.get('outputs', {})}")
        print()
        
        print("=" * 80)
        print("✅ Phase 5 統合テスト完了！")
        print("=" * 80)
        print()
        print("生成されたファイル:")
        print(f"  1. I/O表Excel: {output_file}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_phase5_integration()
    sys.exit(0 if success else 1)
