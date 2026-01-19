"""
C言語単体テスト自動生成ツール - 統合クラス

すべてのコンポーネントを統合し、C言語ソースファイルから以下を自動生成:
1. MC/DC真偽表 (Excel)
2. Unityテストコード (.c)
3. I/O一覧表 (Excel)
"""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .parser.c_code_parser import CCodeParser
from .truth_table.truth_table_generator import TruthTableGenerator
from .test_generator.unity_test_generator import UnityTestGenerator
from .io_table.io_table_generator import IOTableGenerator
from .output.excel_writer import ExcelWriter


# ===== エンコーディングユーティリティ関数 =====

def read_source_file(file_path: str) -> Tuple[Optional[str], str]:
    """
    ソースファイルを読み込む（エンコーディング自動検出）
    
    UTF-8で読み込みを試み、失敗した場合はShift-JISで読み込む。
    
    Args:
        file_path: ファイルパス
    
    Returns:
        Tuple[コンテンツ or None, 検出されたエンコーディング]
    """
    # まずUTF-8で試行
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), 'utf-8'
    except UnicodeDecodeError:
        pass
    
    # UTF-8で失敗した場合、Shift-JISで試行
    try:
        with open(file_path, 'r', encoding='shift_jis') as f:
            return f.read(), 'shift_jis'
    except UnicodeDecodeError:
        pass
    except Exception:
        pass
    
    # 両方失敗した場合
    return None, 'unknown'


def write_source_file(file_path: str, content: str, encoding: str = 'shift_jis') -> bool:
    """
    ソースファイルを書き込む
    
    Args:
        file_path: ファイルパス
        content: 書き込む内容
        encoding: エンコーディング（デフォルト: shift_jis）
    
    Returns:
        成功した場合True
    """
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"   ⚠ ファイル書き込みエラー: {e}")
        return False


# 出力ディレクトリ管理をインライン関数として定義
def get_unique_output_dir(base_dir: str) -> Path:
    """
    ユニークな出力ディレクトリパスを取得
    既存のディレクトリがある場合、(1), (2), ... と番号を付加
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        return base_path
    
    counter = 1
    while True:
        new_path = Path(f"{base_dir}({counter})")
        if not new_path.exists():
            return new_path
        counter += 1
        
        if counter > 1000:
            raise RuntimeError(f"出力ディレクトリの番号が1000を超えました: {base_dir}")


@dataclass
class GenerationResult:
    """生成結果を格納するデータクラス"""
    truth_table_path: Optional[Path] = None
    test_code_path: Optional[Path] = None
    io_table_path: Optional[Path] = None
    success: bool = False
    error_message: Optional[str] = None
    
    def __str__(self) -> str:
        if not self.success:
            return f"❌ 生成失敗: {self.error_message}"
        
        result = "✅ 生成成功\n"
        if self.truth_table_path:
            result += f"  - 真偽表: {self.truth_table_path}\n"
        if self.test_code_path:
            result += f"  - テストコード: {self.test_code_path}\n"
        if self.io_table_path:
            result += f"  - I/O表: {self.io_table_path}\n"
        return result


class CTestAutoGenerator:
    """
    C言語単体テスト自動生成ツールのメインクラス
    
    使用例:
        generator = CTestAutoGenerator()
        result = generator.generate_all(
            c_file_path="sample.c",
            target_function="calculate",
            output_dir="output"
        )
        print(result)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定情報（オプション）
        """
        self.config = config or {}
        self.no_overwrite = False  # 上書き禁止フラグ
        self.standalone_mode = self.config.get('standalone_mode', True)  # v2.4.3: デフォルトでスタンドアロンモード
        self._init_components()
    
    def _init_components(self):
        """各コンポーネントを初期化"""
        # configからdefinesを取得
        defines = self.config.get('defines', {})
        
        # configからinclude関連の設定を取得
        include_paths = self.config.get('include_paths', [])
        # v4.8.2: デフォルトでインクルード展開を有効化
        enable_includes = self.config.get('enable_includes', True)
        
        # v2.2: テスト対象関数本体をテストコードに含めるかの設定
        include_target_function = self.config.get('include_target_function', True)
        
        # v4.8.2: パーサー初期化時にinclude_pathsを渡す（ファイル解析時に更新）
        self._base_include_paths = include_paths.copy() if include_paths else []
        self._enable_includes = enable_includes
        
        self.parser = CCodeParser(
            defines=defines,
            include_paths=include_paths,
            enable_includes=enable_includes
        )
        self.truth_table_generator = TruthTableGenerator()
        self.test_generator = UnityTestGenerator(include_target_function=include_target_function)
        self.io_table_generator = IOTableGenerator()
        self.excel_writer = ExcelWriter()
    
    def generate_all(
        self,
        c_file_path: str,
        target_function: str,
        output_dir: str = "output",
        truth_table_name: Optional[str] = None,
        test_code_name: Optional[str] = None,
        io_table_name: Optional[str] = None
    ) -> GenerationResult:
        """
        すべての成果物を一括生成
        
        Args:
            c_file_path: C言語ソースファイルパス
            target_function: テスト対象関数名
            output_dir: 出力ディレクトリ
            truth_table_name: 真偽表ファイル名（省略時は自動生成）
            test_code_name: テストコードファイル名（省略時は自動生成）
            io_table_name: I/O表ファイル名（省略時は自動生成）
        
        Returns:
            GenerationResult: 生成結果
        """
        result = GenerationResult()
        
        try:
            # 出力ディレクトリ作成（CLIで既にユニーク化済み）
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # v4.8.2: 入力ファイルのディレクトリをinclude_pathsに追加
            input_dir = str(Path(c_file_path).parent.absolute())
            if input_dir not in self.parser.preprocessor.include_paths:
                self.parser.preprocessor.include_paths.insert(0, input_dir)
                print(f"[INFO] v4.8.2: インクルードパスを追加: {input_dir}")
            
            # ファイル名のデフォルト設定
            base_name = Path(c_file_path).stem
            truth_table_name = truth_table_name or f"{base_name}_{target_function}_truth_table.xlsx"
            test_code_name = test_code_name or f"test_{base_name}_{target_function}.c"
            io_table_name = io_table_name or f"{base_name}_{target_function}_io_table.xlsx"
            
            # 出力ファイルパスの準備
            truth_table_path = output_path / truth_table_name
            test_code_path = output_path / test_code_name
            io_table_path = output_path / io_table_name
            
            # no_overwriteフラグがある場合、既存ファイルをチェック
            if self.no_overwrite:
                for file_path, file_type in [
                    (truth_table_path, "真偽表"),
                    (test_code_path, "テストコード"),
                    (io_table_path, "I/O表")
                ]:
                    if file_path.exists():
                        raise Exception(
                            f"❌ 既存の{file_type}ファイルが存在します: {file_path}\n"
                            f"   --no-overwrite オプションが指定されているため、処理を中断します。\n"
                            f"   対処方法:\n"
                            f"   1. 既存ファイルを削除または移動する\n"
                            f"   2. 別の出力ディレクトリを指定する (-o オプション)\n"
                            f"   3. --overwrite オプションで強制上書きする"
                        )
            
            # 1. C言語ファイルを解析
            print(f"🔍 Step 1/4: C言語ファイルを解析中... ({c_file_path})")
            parsed_data = self.parser.parse(c_file_path, target_function=target_function)
            
            # パース失敗チェック
            if parsed_data is None:
                raise Exception(
                    f"❌ C言語ファイルの解析に失敗しました\n"
                    f"   ファイル: {c_file_path}\n"
                    f"   関数: {target_function}\n"
                    f"   対処方法:\n"
                    f"   1. ファイルの構文エラーを確認してください\n"
                    f"   2. 関数名が正しいか確認してください\n"
                    f"   3. --log-level DEBUG でデバッグログを確認してください\n"
                    f"   4. ビットフィールドや複雑な構文がある場合、standard_types.h を確認してください"
                )
            
            print(f"   ✓ 解析完了: {len(parsed_data.conditions)}個の条件を検出")
            
            # v2.2: ソースコードを読み込み（関数本体抽出用）
            # v4.0: エンコーディング自動検出
            source_code, detected_encoding = read_source_file(c_file_path)
            if source_code is None:
                print(f"   ⚠ ソースコード読み込みエラー（関数本体は含まれません）")
            
            # 2. 真偽表を生成
            print(f"📊 Step 2/4: MC/DC真偽表を生成中...")
            truth_table = self.truth_table_generator.generate(parsed_data)
            self.excel_writer.write_truth_table(truth_table, str(truth_table_path))
            result.truth_table_path = truth_table_path
            print(f"   ✓ 真偽表生成完了: {len(truth_table.test_cases)}個のテストケース")
            
            # 3. Unityテストコードを生成
            print(f"🧪 Step 3/4: Unityテストコードを生成中...")
            
            # まず通常のTestCodeオブジェクトを生成（I/O表生成用）
            test_code = self.test_generator.generate(truth_table, parsed_data, source_code)
            
            # v2.4.3: スタンドアロンモードの場合は別途スタンドアロン版も生成
            if self.standalone_mode and source_code:
                print(f"   💡 スタンドアロンモード: 元のソースファイルにテストコードを追加します")
                standalone_code = self.test_generator.generate_standalone(
                    truth_table, parsed_data, source_code
                )
                # v4.0: Shift-JISで出力
                if write_source_file(str(test_code_path), standalone_code, encoding='shift_jis'):
                    result.test_code_path = test_code_path
                    print(f"   ✓ スタンドアロン版テストコード生成完了（Shift-JIS）")
                else:
                    raise Exception("テストコードの書き込みに失敗しました")
            else:
                # 従来の方式（v2.2: source_codeを渡す）
                # v4.0: Shift-JISで出力
                if write_source_file(str(test_code_path), test_code.to_string(), encoding='shift_jis'):
                    result.test_code_path = test_code_path
                    print(f"   ✓ テストコード生成完了: {len(test_code.test_functions)}個のテスト関数（Shift-JIS）")
                else:
                    raise Exception("テストコードの書き込みに失敗しました")
            
            # 4. I/O表を生成
            print(f"📝 Step 4/4: I/O一覧表を生成中...")
            io_table = self.io_table_generator.generate(test_code, truth_table)
            self.excel_writer.write_io_table(io_table, str(io_table_path))
            result.io_table_path = io_table_path
            print(f"   ✓ I/O表生成完了: {len(io_table.test_data)}個のテストケース")
            
            result.success = True
            print(f"\n✅ すべての生成処理が完了しました！")
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            print(f"\n❌ エラーが発生しました: {e}")
            raise
        
        return result
    
    def generate_truth_table_only(
        self,
        c_file_path: str,
        target_function: str,
        output_path: str
    ) -> GenerationResult:
        """
        真偽表のみを生成
        
        Args:
            c_file_path: C言語ソースファイルパス
            target_function: テスト対象関数名
            output_path: 出力ファイルパス
        
        Returns:
            GenerationResult: 生成結果
        """
        result = GenerationResult()
        
        try:
            print(f"🔍 C言語ファイルを解析中... ({c_file_path})")
            parsed_data = self.parser.parse(c_file_path, target_function=target_function)
            
            print(f"📊 MC/DC真偽表を生成中...")
            truth_table = self.truth_table_generator.generate(parsed_data)
            self.excel_writer.write_truth_table(truth_table, output_path)
            
            result.truth_table_path = Path(output_path)
            result.success = True
            print(f"✅ 真偽表の生成が完了しました: {output_path}")
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            print(f"❌ エラーが発生しました: {e}")
        
        return result
    
    def generate_test_code_only(
        self,
        c_file_path: str,
        target_function: str,
        output_path: str
    ) -> GenerationResult:
        """
        テストコードのみを生成
        
        Args:
            c_file_path: C言語ソースファイルパス
            target_function: テスト対象関数名
            output_path: 出力ファイルパス
        
        Returns:
            GenerationResult: 生成結果
        """
        result = GenerationResult()
        
        try:
            print(f"🔍 C言語ファイルを解析中... ({c_file_path})")
            parsed_data = self.parser.parse(c_file_path, target_function=target_function)
            
            # v4.0: エンコーディング自動検出
            source_code, detected_encoding = read_source_file(c_file_path)
            
            print(f"📊 MC/DC真偽表を生成中...")
            truth_table = self.truth_table_generator.generate(parsed_data)
            
            print(f"🧪 Unityテストコードを生成中...")
            test_code = self.test_generator.generate(truth_table, parsed_data, source_code)
            
            # v4.0: Shift-JISで出力
            if write_source_file(output_path, test_code.to_string(), encoding='shift_jis'):
                result.test_code_path = Path(output_path)
                result.success = True
                print(f"✅ テストコードの生成が完了しました: {output_path}（Shift-JIS）")
            else:
                raise Exception("テストコードの書き込みに失敗しました")
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            print(f"❌ エラーが発生しました: {e}")
        
        return result
    
    def generate_io_table_only(
        self,
        c_file_path: str,
        target_function: str,
        output_path: str
    ) -> GenerationResult:
        """
        I/O表のみを生成
        
        Args:
            c_file_path: C言語ソースファイルパス
            target_function: テスト対象関数名
            output_path: 出力ファイルパス
        
        Returns:
            GenerationResult: 生成結果
        """
        result = GenerationResult()
        
        try:
            print(f"🔍 C言語ファイルを解析中... ({c_file_path})")
            parsed_data = self.parser.parse(c_file_path, target_function=target_function)
            
            # v4.0: エンコーディング自動検出
            source_code, detected_encoding = read_source_file(c_file_path)
            
            print(f"📊 MC/DC真偽表を生成中...")
            truth_table = self.truth_table_generator.generate(parsed_data)
            
            print(f"🧪 Unityテストコードを生成中...")
            test_code = self.test_generator.generate(truth_table, parsed_data, source_code)
            
            print(f"📝 I/O一覧表を生成中...")
            io_table = self.io_table_generator.generate(test_code, truth_table)
            self.excel_writer.write_io_table(io_table, output_path)
            
            result.io_table_path = Path(output_path)
            result.success = True
            print(f"✅ I/O表の生成が完了しました: {output_path}")
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            print(f"❌ エラーが発生しました: {e}")
        
        return result
