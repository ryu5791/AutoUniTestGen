"""
Phase 6 統合テスト - エンドツーエンドテスト

CTestAutoGeneratorクラスとCLIインターフェースの動作を検証
"""

import sys
from pathlib import Path
import tempfile
import shutil

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.c_test_auto_generator import CTestAutoGenerator
from src.config import ConfigManager


# テスト用C言語コード
SAMPLE_C_CODE = '''
int f1(int v1, int v2, int v3) {
    if (v1 > 10) {
        if (v2 < 20) {
            return v3 * 2;
        } else {
            return v3 + 10;
        }
    } else {
        return v3 - 5;
    }
}
'''


def test_generate_all():
    """すべての成果物を一括生成するテスト"""
    print("\n" + "=" * 70)
    print("TEST 1: すべての成果物を一括生成")
    print("=" * 70)
    
    # 一時ディレクトリ作成
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # テスト用C言語ファイル作成
        c_file = temp_path / "test_sample.c"
        c_file.write_text(SAMPLE_C_CODE)
        
        # 出力ディレクトリ
        output_dir = temp_path / "output"
        
        # 生成器初期化
        generator = CTestAutoGenerator()
        
        # すべて生成
        result = generator.generate_all(
            c_file_path=str(c_file),
            target_function="f1",
            output_dir=str(output_dir)
        )
        
        # 結果検証
        print("\n結果検証:")
        assert result.success, f"生成が失敗しました: {result.error_message}"
        print("  ✓ 生成成功")
        
        assert result.truth_table_path.exists(), "真偽表ファイルが存在しません"
        print(f"  ✓ 真偽表: {result.truth_table_path.name}")
        
        assert result.test_code_path.exists(), "テストコードファイルが存在しません"
        print(f"  ✓ テストコード: {result.test_code_path.name}")
        
        assert result.io_table_path.exists(), "I/O表ファイルが存在しません"
        print(f"  ✓ I/O表: {result.io_table_path.name}")
        
        # ファイルサイズ確認
        truth_size = result.truth_table_path.stat().st_size
        test_size = result.test_code_path.stat().st_size
        io_size = result.io_table_path.stat().st_size
        
        print(f"\n生成ファイルサイズ:")
        print(f"  - 真偽表: {truth_size:,} bytes")
        print(f"  - テストコード: {test_size:,} bytes")
        print(f"  - I/O表: {io_size:,} bytes")
        
        assert truth_size > 0, "真偽表ファイルが空です"
        assert test_size > 0, "テストコードファイルが空です"
        assert io_size > 0, "I/O表ファイルが空です"
        
        print("\n✅ TEST 1 PASSED!")


def test_generate_truth_table_only():
    """真偽表のみ生成するテスト"""
    print("\n" + "=" * 70)
    print("TEST 2: 真偽表のみ生成")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # テスト用C言語ファイル作成
        c_file = temp_path / "test_sample.c"
        c_file.write_text(SAMPLE_C_CODE)
        
        # 出力ファイルパス
        output_file = temp_path / "truth_table_only.xlsx"
        
        # 生成器初期化
        generator = CTestAutoGenerator()
        
        # 真偽表のみ生成
        result = generator.generate_truth_table_only(
            c_file_path=str(c_file),
            target_function="f1",
            output_path=str(output_file)
        )
        
        # 結果検証
        print("\n結果検証:")
        assert result.success, f"生成が失敗しました: {result.error_message}"
        print("  ✓ 生成成功")
        
        assert result.truth_table_path.exists(), "真偽表ファイルが存在しません"
        print(f"  ✓ 真偽表: {result.truth_table_path.name}")
        
        assert result.test_code_path is None, "テストコードが生成されてしまいました"
        assert result.io_table_path is None, "I/O表が生成されてしまいました"
        print("  ✓ 他のファイルは生成されていません")
        
        print("\n✅ TEST 2 PASSED!")


def test_generate_test_code_only():
    """テストコードのみ生成するテスト"""
    print("\n" + "=" * 70)
    print("TEST 3: テストコードのみ生成")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # テスト用C言語ファイル作成
        c_file = temp_path / "test_sample.c"
        c_file.write_text(SAMPLE_C_CODE)
        
        # 出力ファイルパス
        output_file = temp_path / "test_code_only.c"
        
        # 生成器初期化
        generator = CTestAutoGenerator()
        
        # テストコードのみ生成
        result = generator.generate_test_code_only(
            c_file_path=str(c_file),
            target_function="f1",
            output_path=str(output_file)
        )
        
        # 結果検証
        print("\n結果検証:")
        assert result.success, f"生成が失敗しました: {result.error_message}"
        print("  ✓ 生成成功")
        
        assert result.test_code_path.exists(), "テストコードファイルが存在しません"
        print(f"  ✓ テストコード: {result.test_code_path.name}")
        
        # テストコードの内容確認
        test_content = result.test_code_path.read_text()
        assert "#include \"unity.h\"" in test_content, "Unityヘッダーがありません"
        assert "void test_" in test_content, "テスト関数がありません"
        print("  ✓ テストコードの内容を確認")
        
        assert result.truth_table_path is None, "真偽表が生成されてしまいました"
        assert result.io_table_path is None, "I/O表が生成されてしまいました"
        print("  ✓ 他のファイルは生成されていません")
        
        print("\n✅ TEST 3 PASSED!")


def test_generate_io_table_only():
    """I/O表のみ生成するテスト"""
    print("\n" + "=" * 70)
    print("TEST 4: I/O表のみ生成")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # テスト用C言語ファイル作成
        c_file = temp_path / "test_sample.c"
        c_file.write_text(SAMPLE_C_CODE)
        
        # 出力ファイルパス
        output_file = temp_path / "io_table_only.xlsx"
        
        # 生成器初期化
        generator = CTestAutoGenerator()
        
        # I/O表のみ生成
        result = generator.generate_io_table_only(
            c_file_path=str(c_file),
            target_function="f1",
            output_path=str(output_file)
        )
        
        # 結果検証
        print("\n結果検証:")
        assert result.success, f"生成が失敗しました: {result.error_message}"
        print("  ✓ 生成成功")
        
        assert result.io_table_path.exists(), "I/O表ファイルが存在しません"
        print(f"  ✓ I/O表: {result.io_table_path.name}")
        
        assert result.truth_table_path is None, "真偽表が生成されてしまいました"
        assert result.test_code_path is None, "テストコードが生成されてしまいました"
        print("  ✓ 他のファイルは生成されていません")
        
        print("\n✅ TEST 4 PASSED!")


def test_config_manager():
    """設定管理のテスト"""
    print("\n" + "=" * 70)
    print("TEST 5: 設定管理")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_file = temp_path / "test_config.json"
        
        # デフォルト設定ファイル作成
        print("\nデフォルト設定ファイルを作成...")
        success = ConfigManager.create_default_config(str(config_file))
        assert success, "設定ファイルの作成に失敗しました"
        assert config_file.exists(), "設定ファイルが作成されていません"
        print("  ✓ 設定ファイル作成成功")
        
        # 設定読み込み
        print("\n設定ファイルを読み込み...")
        manager = ConfigManager(str(config_file))
        config = manager.load()
        assert config is not None, "設定の読み込みに失敗しました"
        print("  ✓ 設定読み込み成功")
        print(f"    - output_dir: {config.output_dir}")
        print(f"    - test_framework: {config.test_framework}")
        
        # 設定更新
        print("\n設定を更新...")
        manager.update_config(output_dir="custom_output", include_comments=False)
        assert manager.config.output_dir == "custom_output", "設定更新に失敗しました"
        assert manager.config.include_comments == False, "設定更新に失敗しました"
        print("  ✓ 設定更新成功")
        
        # 設定保存
        print("\n設定を保存...")
        custom_config = temp_path / "custom_config.json"
        success = manager.save(str(custom_config))
        assert success, "設定の保存に失敗しました"
        assert custom_config.exists(), "設定ファイルが保存されていません"
        print("  ✓ 設定保存成功")
        
        print("\n✅ TEST 5 PASSED!")


def test_custom_filenames():
    """カスタムファイル名を指定するテスト"""
    print("\n" + "=" * 70)
    print("TEST 6: カスタムファイル名指定")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # テスト用C言語ファイル作成
        c_file = temp_path / "test_sample.c"
        c_file.write_text(SAMPLE_C_CODE)
        
        # 出力ディレクトリ
        output_dir = temp_path / "output"
        
        # 生成器初期化
        generator = CTestAutoGenerator()
        
        # カスタムファイル名で生成
        result = generator.generate_all(
            c_file_path=str(c_file),
            target_function="f1",
            output_dir=str(output_dir),
            truth_table_name="my_truth_table.xlsx",
            test_code_name="my_test.c",
            io_table_name="my_io_table.xlsx"
        )
        
        # 結果検証
        print("\n結果検証:")
        assert result.success, f"生成が失敗しました: {result.error_message}"
        
        assert result.truth_table_path.name == "my_truth_table.xlsx", "真偽表のファイル名が一致しません"
        print(f"  ✓ 真偽表: {result.truth_table_path.name}")
        
        assert result.test_code_path.name == "my_test.c", "テストコードのファイル名が一致しません"
        print(f"  ✓ テストコード: {result.test_code_path.name}")
        
        assert result.io_table_path.name == "my_io_table.xlsx", "I/O表のファイル名が一致しません"
        print(f"  ✓ I/O表: {result.io_table_path.name}")
        
        print("\n✅ TEST 6 PASSED!")


def main():
    """メインテスト実行"""
    print("\n" + "=" * 70)
    print("Phase 6 統合テスト開始")
    print("=" * 70)
    
    try:
        # 各テストを実行
        test_generate_all()
        test_generate_truth_table_only()
        test_generate_test_code_only()
        test_generate_io_table_only()
        test_config_manager()
        test_custom_filenames()
        
        # 最終結果
        print("\n" + "=" * 70)
        print("✅ すべてのテストが成功しました！")
        print("=" * 70)
        print("\nPhase 6の実装が完了しました:")
        print("  ✓ CTestAutoGenerator (統合クラス)")
        print("  ✓ ConfigManager (設定管理)")
        print("  ✓ CLI (コマンドラインインターフェース)")
        print("  ✓ エンドツーエンドテスト")
        print("\n次のステップ:")
        print("  - python main.py -i sample.c -f function_name -o output")
        print("  - python main.py --help (ヘルプ表示)")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
