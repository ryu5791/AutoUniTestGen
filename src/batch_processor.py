"""
バッチ処理モジュール

複数のC言語ファイルをバッチ処理する機能を提供します。
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .error_handler import ErrorHandler, GeneratorError, ErrorCode, ErrorContext


@dataclass
class BatchItem:
    """バッチ処理アイテム"""
    input_file: str
    function_name: str
    output_dir: Optional[str] = None
    truth_table_file: Optional[str] = None
    test_code_file: Optional[str] = None
    io_table_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchItem':
        """辞書から作成"""
        return cls(**data)


@dataclass
class BatchResult:
    """バッチ処理結果"""
    item: BatchItem
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    generated_files: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        result = {
            'input_file': self.item.input_file,
            'function_name': self.item.function_name,
            'success': self.success,
            'execution_time': self.execution_time,
        }
        if self.error_message:
            result['error_message'] = self.error_message
        if self.generated_files:
            result['generated_files'] = self.generated_files
        return result


class BatchProcessor:
    """バッチ処理クラス"""
    
    def __init__(
        self,
        generator,
        error_handler: Optional[ErrorHandler] = None,
        max_workers: int = 4,
        continue_on_error: bool = True
    ):
        """
        初期化
        
        Args:
            generator: CTestAutoGeneratorのインスタンス
            error_handler: エラーハンドラー
            max_workers: 並列処理の最大ワーカー数
            continue_on_error: エラー発生時も処理を継続するか
        """
        self.generator = generator
        self.error_handler = error_handler or ErrorHandler()
        self.max_workers = max_workers
        self.continue_on_error = continue_on_error
        self.results: List[BatchResult] = []
    
    def process_batch(
        self,
        items: List[BatchItem],
        parallel: bool = False
    ) -> List[BatchResult]:
        """
        バッチ処理を実行
        
        Args:
            items: 処理するアイテムのリスト
            parallel: 並列処理を有効にするか
        
        Returns:
            処理結果のリスト
        """
        self.results = []
        total = len(items)
        
        self.error_handler.info(f"バッチ処理開始: {total}個のアイテム")
        self.error_handler.info(f"並列処理: {'有効' if parallel else '無効'}")
        
        start_time = time.time()
        
        if parallel and total > 1:
            self.results = self._process_parallel(items)
        else:
            self.results = self._process_sequential(items)
        
        elapsed_time = time.time() - start_time
        
        # サマリーを出力
        self._print_summary(elapsed_time)
        
        return self.results
    
    def _process_sequential(self, items: List[BatchItem]) -> List[BatchResult]:
        """シーケンシャル処理"""
        results = []
        
        for i, item in enumerate(items, 1):
            self.error_handler.info(f"\n処理中 ({i}/{len(items)}): {item.input_file} - {item.function_name}")
            result = self._process_single_item(item)
            results.append(result)
            
            if not result.success and not self.continue_on_error:
                self.error_handler.error("エラーが発生したため、バッチ処理を中止します")
                break
        
        return results
    
    def _process_parallel(self, items: List[BatchItem]) -> List[BatchResult]:
        """並列処理"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # すべてのタスクを投入
            future_to_item = {
                executor.submit(self._process_single_item, item): (i, item)
                for i, item in enumerate(items, 1)
            }
            
            # 完了したタスクから結果を取得
            for future in as_completed(future_to_item):
                i, item = future_to_item[future]
                self.error_handler.info(f"完了 ({i}/{len(items)}): {item.input_file} - {item.function_name}")
                
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.error_handler.error(f"並列処理中にエラーが発生: {str(e)}")
                    results.append(BatchResult(
                        item=item,
                        success=False,
                        execution_time=0,
                        error_message=str(e)
                    ))
        
        # 元の順序でソート
        results.sort(key=lambda r: items.index(r.item))
        return results
    
    def _process_single_item(self, item: BatchItem) -> BatchResult:
        """単一アイテムの処理"""
        start_time = time.time()
        
        try:
            # 出力ディレクトリの設定
            output_dir = item.output_dir or "output"
            
            # 生成処理を実行
            result = self.generator.generate_all(
                c_file_path=item.input_file,
                target_function=item.function_name,
                output_dir=output_dir,
                truth_table_file=item.truth_table_file,
                test_code_file=item.test_code_file,
                io_table_file=item.io_table_file
            )
            
            execution_time = time.time() - start_time
            
            # 生成されたファイルのリストを作成
            generated_files = []
            if result.truth_table_path:
                generated_files.append(str(result.truth_table_path))
            if result.test_code_path:
                generated_files.append(str(result.test_code_path))
            if result.io_table_path:
                generated_files.append(str(result.io_table_path))
            
            return BatchResult(
                item=item,
                success=True,
                execution_time=execution_time,
                generated_files=generated_files
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            self.error_handler.error(f"処理失敗: {item.input_file} - {error_msg}")
            
            return BatchResult(
                item=item,
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
    
    def _print_summary(self, total_time: float):
        """処理サマリーを出力"""
        success_count = sum(1 for r in self.results if r.success)
        fail_count = len(self.results) - success_count
        
        print("\n" + "="*70)
        print("バッチ処理完了")
        print("="*70)
        print(f"合計処理数: {len(self.results)}")
        print(f"成功: {success_count}")
        print(f"失敗: {fail_count}")
        print(f"総実行時間: {total_time:.2f}秒")
        
        if self.results:
            avg_time = sum(r.execution_time for r in self.results) / len(self.results)
            print(f"平均実行時間: {avg_time:.2f}秒/アイテム")
        
        # 失敗したアイテムの詳細
        if fail_count > 0:
            print("\n失敗したアイテム:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.item.input_file} ({result.item.function_name})")
                    print(f"    エラー: {result.error_message}")
        
        print("="*70)
    
    def load_batch_config(self, config_file: str) -> List[BatchItem]:
        """
        バッチ設定ファイルを読み込む
        
        Args:
            config_file: 設定ファイルパス（JSON形式）
        
        Returns:
            バッチアイテムのリスト
        
        Raises:
            GeneratorError: ファイル読み込みエラー
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items = []
            if isinstance(data, list):
                # リスト形式
                for item_data in data:
                    items.append(BatchItem.from_dict(item_data))
            elif isinstance(data, dict) and 'items' in data:
                # オブジェクト形式
                for item_data in data['items']:
                    items.append(BatchItem.from_dict(item_data))
            else:
                raise ValueError("無効な設定ファイル形式です")
            
            self.error_handler.info(f"バッチ設定ファイル読み込み成功: {len(items)}個のアイテム")
            return items
        
        except FileNotFoundError:
            raise GeneratorError(
                f"バッチ設定ファイルが見つかりません: {config_file}",
                ErrorCode.FILE_NOT_FOUND,
                ErrorContext(file_path=config_file)
            )
        except json.JSONDecodeError as e:
            raise GeneratorError(
                f"バッチ設定ファイルのJSON解析に失敗: {str(e)}",
                ErrorCode.INVALID_FILE_FORMAT,
                ErrorContext(file_path=config_file),
                original_error=e
            )
        except Exception as e:
            raise GeneratorError(
                f"バッチ設定ファイルの読み込みに失敗: {str(e)}",
                ErrorCode.PARSE_ERROR,
                ErrorContext(file_path=config_file),
                original_error=e
            )
    
    def save_results(self, output_file: str):
        """
        処理結果をファイルに保存
        
        Args:
            output_file: 出力ファイルパス（JSON形式）
        """
        try:
            results_data = {
                'total': len(self.results),
                'success': sum(1 for r in self.results if r.success),
                'failed': sum(1 for r in self.results if not r.success),
                'results': [r.to_dict() for r in self.results]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            self.error_handler.info(f"処理結果を保存しました: {output_file}")
        
        except Exception as e:
            self.error_handler.error(f"処理結果の保存に失敗: {str(e)}")
    
    @staticmethod
    def create_batch_config_template(output_file: str = "batch_config.json"):
        """
        バッチ設定ファイルのテンプレートを作成
        
        Args:
            output_file: 出力ファイルパス
        """
        template = {
            "items": [
                {
                    "input_file": "sample1.c",
                    "function_name": "function1",
                    "output_dir": "output/sample1"
                },
                {
                    "input_file": "sample2.c",
                    "function_name": "function2",
                    "output_dir": "output/sample2",
                    "truth_table_file": "custom_truth_table.xlsx",
                    "test_code_file": "custom_test.c",
                    "io_table_file": "custom_io_table.xlsx"
                }
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"バッチ設定ファイルのテンプレートを作成しました: {output_file}")
    
    def process_directory(
        self,
        directory: str,
        pattern: str = "*.c",
        output_base_dir: str = "output",
        parallel: bool = False
    ) -> List[BatchResult]:
        """
        ディレクトリ内のすべてのファイルをバッチ処理
        
        Args:
            directory: 処理するディレクトリ
            pattern: ファイルパターン（glob形式）
            output_base_dir: 出力ベースディレクトリ
            parallel: 並列処理を有効にするか
        
        Returns:
            処理結果のリスト
        
        Note:
            この関数は各ファイルの最初の関数を自動検出して処理します。
        """
        path = Path(directory)
        
        if not path.exists() or not path.is_dir():
            raise GeneratorError(
                f"ディレクトリが見つかりません: {directory}",
                ErrorCode.FILE_NOT_FOUND,
                ErrorContext(file_path=directory)
            )
        
        # ファイルを検索
        files = list(path.glob(pattern))
        self.error_handler.info(f"ディレクトリスキャン: {len(files)}個のファイルを検出")
        
        if not files:
            self.error_handler.warning(f"パターン '{pattern}' に一致するファイルが見つかりません")
            return []
        
        # バッチアイテムを作成
        items = []
        for file_path in files:
            # 最初の関数を検出（簡易実装）
            function_name = self._detect_first_function(file_path)
            
            if function_name:
                # 出力ディレクトリをファイル名ごとに分ける
                output_dir = Path(output_base_dir) / file_path.stem
                
                items.append(BatchItem(
                    input_file=str(file_path),
                    function_name=function_name,
                    output_dir=str(output_dir)
                ))
        
        self.error_handler.info(f"処理対象: {len(items)}個の関数")
        
        # バッチ処理を実行
        return self.process_batch(items, parallel=parallel)
    
    def _detect_first_function(self, file_path: Path) -> Optional[str]:
        """
        ファイル内の最初の関数を検出（簡易実装）
        
        Args:
            file_path: ファイルパス
        
        Returns:
            関数名、検出できない場合はNone
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 簡易的な正規表現で関数定義を検出
            import re
            # returnType functionName(parameters) の形式を検出
            pattern = r'\b(?:int|void|char|float|double|long|short|unsigned)\s+(\w+)\s*\([^)]*\)\s*\{'
            match = re.search(pattern, content)
            
            if match:
                return match.group(1)
            
            return None
        
        except Exception as e:
            self.error_handler.warning(f"関数検出失敗: {file_path} - {str(e)}")
            return None
