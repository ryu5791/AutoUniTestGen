"""
パフォーマンス最適化モジュール

大規模ファイルの処理最適化、メモリ管理、キャッシング機能を提供します。
"""

import time
import hashlib
import pickle
from pathlib import Path
from typing import Any, Optional, Dict, Callable
from functools import wraps
import psutil
import gc


class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.start_times: Dict[str, float] = {}
    
    def start_operation(self, operation_name: str):
        """操作の開始を記録"""
        self.start_times[operation_name] = time.time()
    
    def end_operation(self, operation_name: str) -> float:
        """
        操作の終了を記録
        
        Returns:
            実行時間（秒）
        """
        if operation_name not in self.start_times:
            return 0.0
        
        elapsed = time.time() - self.start_times[operation_name]
        
        if operation_name not in self.metrics:
            self.metrics[operation_name] = {
                'count': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0
            }
        
        metrics = self.metrics[operation_name]
        metrics['count'] += 1
        metrics['total_time'] += elapsed
        metrics['min_time'] = min(metrics['min_time'], elapsed)
        metrics['max_time'] = max(metrics['max_time'], elapsed)
        
        del self.start_times[operation_name]
        return elapsed
    
    def get_metrics(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """操作のメトリクスを取得"""
        if operation_name not in self.metrics:
            return None
        
        metrics = self.metrics[operation_name].copy()
        if metrics['count'] > 0:
            metrics['avg_time'] = metrics['total_time'] / metrics['count']
        
        return metrics
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """すべてのメトリクスを取得"""
        result = {}
        for name in self.metrics:
            result[name] = self.get_metrics(name)
        return result
    
    def print_summary(self):
        """メトリクスサマリーを表示"""
        print("\n" + "="*70)
        print("パフォーマンスメトリクス")
        print("="*70)
        
        for operation_name, metrics in self.get_all_metrics().items():
            print(f"\n{operation_name}:")
            print(f"  実行回数: {metrics['count']}")
            print(f"  合計時間: {metrics['total_time']:.3f}秒")
            print(f"  平均時間: {metrics['avg_time']:.3f}秒")
            print(f"  最小時間: {metrics['min_time']:.3f}秒")
            print(f"  最大時間: {metrics['max_time']:.3f}秒")
        
        print("="*70)
    
    def reset(self):
        """メトリクスをリセット"""
        self.metrics.clear()
        self.start_times.clear()


class MemoryMonitor:
    """メモリ監視クラス"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage()
    
    def get_memory_usage(self) -> float:
        """
        現在のメモリ使用量を取得（MB単位）
        
        Returns:
            メモリ使用量（MB）
        """
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_memory_increase(self) -> float:
        """
        初期状態からのメモリ増加量を取得（MB単位）
        
        Returns:
            メモリ増加量（MB）
        """
        return self.get_memory_usage() - self.initial_memory
    
    def print_memory_status(self):
        """メモリ状態を表示"""
        current = self.get_memory_usage()
        increase = self.get_memory_increase()
        
        print(f"\nメモリ使用状況:")
        print(f"  現在: {current:.2f} MB")
        print(f"  増加量: {increase:.2f} MB")
        print(f"  初期: {self.initial_memory:.2f} MB")
    
    def check_memory_limit(self, limit_mb: float) -> bool:
        """
        メモリ使用量が制限を超えているか確認
        
        Args:
            limit_mb: メモリ制限（MB）
        
        Returns:
            制限を超えている場合True
        """
        return self.get_memory_usage() > limit_mb
    
    def force_garbage_collection(self):
        """強制的にガベージコレクションを実行"""
        gc.collect()


class ResultCache:
    """結果キャッシュクラス"""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.enabled = True
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """キャッシュキーを生成"""
        key_data = str((args, sorted(kwargs.items())))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """キャッシュファイルパスを取得"""
        return self.cache_dir / f"{cache_key}.cache"
    
    def get(self, *args, **kwargs) -> Optional[Any]:
        """キャッシュから取得"""
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(*args, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                # キャッシュの読み込みに失敗した場合は削除
                cache_path.unlink(missing_ok=True)
        
        return None
    
    def set(self, result: Any, *args, **kwargs):
        """キャッシュに保存"""
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(*args, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(result, f)
        except Exception:
            # キャッシュの保存に失敗しても継続
            pass
    
    def clear(self):
        """キャッシュをクリア"""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink(missing_ok=True)
    
    def disable(self):
        """キャッシュを無効化"""
        self.enabled = False
    
    def enable(self):
        """キャッシュを有効化"""
        self.enabled = True


def monitor_performance(operation_name: str):
    """
    パフォーマンス監視デコレーター
    
    Args:
        operation_name: 操作名
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # パフォーマンスモニターを取得（第一引数がselfの場合）
            monitor = None
            if args and hasattr(args[0], 'performance_monitor'):
                monitor = args[0].performance_monitor
            
            if monitor:
                monitor.start_operation(operation_name)
            
            result = func(*args, **kwargs)
            
            if monitor:
                elapsed = monitor.end_operation(operation_name)
                print(f"  ⏱️  {operation_name}: {elapsed:.3f}秒")
            
            return result
        
        return wrapper
    
    return decorator


def check_memory(limit_mb: float = 1000):
    """
    メモリチェックデコレーター
    
    Args:
        limit_mb: メモリ制限（MB）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # メモリモニターを取得
            monitor = None
            if args and hasattr(args[0], 'memory_monitor'):
                monitor = args[0].memory_monitor
            
            if monitor and monitor.check_memory_limit(limit_mb):
                print(f"⚠️  メモリ制限に近づいています: {monitor.get_memory_usage():.2f} MB")
                monitor.force_garbage_collection()
            
            result = func(*args, **kwargs)
            
            return result
        
        return wrapper
    
    return decorator


def cache_result(cache: Optional[ResultCache] = None):
    """
    結果キャッシュデコレーター
    
    Args:
        cache: キャッシュインスタンス
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # キャッシュを取得
            result_cache = cache
            if result_cache is None and args and hasattr(args[0], 'result_cache'):
                result_cache = args[0].result_cache
            
            if result_cache:
                # キャッシュから取得を試みる
                cached = result_cache.get(*args, **kwargs)
                if cached is not None:
                    print(f"  💾 キャッシュヒット: {func.__name__}")
                    return cached
            
            # 実際の処理を実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュに保存
            if result_cache:
                result_cache.set(result, *args, **kwargs)
            
            return result
        
        return wrapper
    
    return decorator


class ChunkedFileReader:
    """大規模ファイルをチャンク単位で読み込むクラス"""
    
    def __init__(self, chunk_size: int = 1024 * 1024):
        """
        初期化
        
        Args:
            chunk_size: チャンクサイズ（バイト、デフォルト1MB）
        """
        self.chunk_size = chunk_size
    
    def read_chunks(self, file_path: str):
        """
        ファイルをチャンク単位で読み込む
        
        Args:
            file_path: ファイルパス
        
        Yields:
            チャンク（文字列）
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk
    
    def process_large_file(
        self,
        file_path: str,
        processor: Callable[[str], Any],
        combine: Callable[[list], Any]
    ) -> Any:
        """
        大規模ファイルをチャンク単位で処理
        
        Args:
            file_path: ファイルパス
            processor: チャンク処理関数
            combine: 結果統合関数
        
        Returns:
            処理結果
        """
        results = []
        
        for chunk in self.read_chunks(file_path):
            result = processor(chunk)
            results.append(result)
        
        return combine(results)


class OptimizationConfig:
    """最適化設定"""
    
    def __init__(
        self,
        enable_cache: bool = True,
        enable_parallel: bool = True,
        max_workers: int = 4,
        memory_limit_mb: float = 1000,
        chunk_size: int = 1024 * 1024
    ):
        self.enable_cache = enable_cache
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self.memory_limit_mb = memory_limit_mb
        self.chunk_size = chunk_size
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return {
            'enable_cache': self.enable_cache,
            'enable_parallel': self.enable_parallel,
            'max_workers': self.max_workers,
            'memory_limit_mb': self.memory_limit_mb,
            'chunk_size': self.chunk_size
        }


# グローバルインスタンス
_global_performance_monitor: Optional[PerformanceMonitor] = None
_global_memory_monitor: Optional[MemoryMonitor] = None
_global_result_cache: Optional[ResultCache] = None


def get_performance_monitor() -> PerformanceMonitor:
    """グローバルパフォーマンスモニターを取得"""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor


def get_memory_monitor() -> MemoryMonitor:
    """グローバルメモリモニターを取得"""
    global _global_memory_monitor
    if _global_memory_monitor is None:
        _global_memory_monitor = MemoryMonitor()
    return _global_memory_monitor


def get_result_cache() -> ResultCache:
    """グローバル結果キャッシュを取得"""
    global _global_result_cache
    if _global_result_cache is None:
        _global_result_cache = ResultCache()
    return _global_result_cache
