#!/usr/bin/env python3
"""
Performance Optimizer for Phase 6C Learning System

Provides performance profiling, optimization, and monitoring
capabilities for learning components.
"""

import cProfile
import functools
import logging
import time
import tracemalloc
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from collections import defaultdict, deque
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import gc

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """Profile performance of learning operations."""
    
    def __init__(self, max_samples: int = 1000):
        """Initialize performance profiler."""
        self.max_samples = max_samples
        self.performance_data = defaultdict(lambda: deque(maxlen=max_samples))
        self.active_profiles = {}
        self.memory_snapshots = deque(maxlen=100)
        self._lock = threading.Lock()
    
    def profile_function(self, func_name: str = None):
        """Decorator to profile function performance."""
        def decorator(func: Callable) -> Callable:
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self._profile_execution(name, func, *args, **kwargs)
            return wrapper
        return decorator
    
    def _profile_execution(self, name: str, func: Callable, *args, **kwargs):
        """Execute function with performance profiling."""
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
            raise
        finally:
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            with self._lock:
                self.performance_data[name].append({
                    'timestamp': datetime.now().isoformat(),
                    'execution_time': execution_time,
                    'memory_delta': memory_delta,
                    'memory_peak': end_memory,
                    'success': success,
                    'error': error,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                })
        
        return result
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def start_memory_monitoring(self):
        """Start monitoring memory usage."""
        tracemalloc.start()
    
    def get_memory_snapshot(self) -> Dict[str, Any]:
        """Get current memory snapshot."""
        if not tracemalloc.is_tracing():
            return {}
        
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        total_memory = sum(stat.size for stat in top_stats)
        top_10 = [
            {
                'filename': stat.traceback.format()[0],
                'size_mb': stat.size / 1024 / 1024,
                'count': stat.count
            }
            for stat in top_stats[:10]
        ]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_memory_mb': total_memory / 1024 / 1024,
            'top_allocations': top_10
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        with self._lock:
            report = {
                'timestamp': datetime.now().isoformat(),
                'function_metrics': {},
                'system_metrics': self._get_system_metrics(),
                'recommendations': []
            }
            
            for func_name, samples in self.performance_data.items():
                if not samples:
                    continue
                
                execution_times = [s['execution_time'] for s in samples if s['success']]
                memory_deltas = [s['memory_delta'] for s in samples]
                
                if execution_times:
                    avg_time = sum(execution_times) / len(execution_times)
                    max_time = max(execution_times)
                    min_time = min(execution_times)
                    
                    # Calculate percentiles
                    sorted_times = sorted(execution_times)
                    p95_time = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
                    
                    # Error rate
                    total_calls = len(samples)
                    error_count = sum(1 for s in samples if not s['success'])
                    error_rate = error_count / total_calls if total_calls > 0 else 0
                    
                    metrics = {
                        'total_calls': total_calls,
                        'avg_execution_time': avg_time,
                        'min_execution_time': min_time,
                        'max_execution_time': max_time,
                        'p95_execution_time': p95_time,
                        'avg_memory_delta': sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0,
                        'error_rate': error_rate,
                        'calls_per_minute': self._calculate_call_rate(samples)
                    }
                    
                    report['function_metrics'][func_name] = metrics
                    
                    # Generate recommendations
                    if avg_time > 5.0:
                        report['recommendations'].append({
                            'function': func_name,
                            'issue': 'slow_execution',
                            'message': f'Average execution time {avg_time:.2f}s is high',
                            'suggestion': 'Consider optimization or async processing'
                        })
                    
                    if error_rate > 0.1:
                        report['recommendations'].append({
                            'function': func_name,
                            'issue': 'high_error_rate',
                            'message': f'Error rate {error_rate:.1%} is high',
                            'suggestion': 'Investigate error causes and improve error handling'
                        })
            
            return report
    
    def _calculate_call_rate(self, samples: List[Dict]) -> float:
        """Calculate calls per minute for recent samples."""
        now = datetime.now()
        recent_samples = [
            s for s in samples 
            if (now - datetime.fromisoformat(s['timestamp'])).total_seconds() < 300  # Last 5 minutes
        ]
        return len(recent_samples) * 12  # Extrapolate to per minute
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level performance metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / 1024 / 1024 / 1024,
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / 1024 / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}


class BatchProcessor:
    """Optimized batch processing for learning operations."""
    
    def __init__(self, max_workers: int = None, batch_size: int = 50):
        """Initialize batch processor."""
        self.max_workers = max_workers or min(4, multiprocessing.cpu_count())
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    def process_corrections_batch(self, corrections: List[Dict], processor_func: Callable) -> List[Any]:
        """Process corrections in optimized batches."""
        if not corrections:
            return []
        
        # Split into batches
        batches = [
            corrections[i:i + self.batch_size]
            for i in range(0, len(corrections), self.batch_size)
        ]
        
        # Process batches concurrently
        futures = [
            self.executor.submit(processor_func, batch)
            for batch in batches
        ]
        
        results = []
        for future in as_completed(futures):
            try:
                batch_result = future.result()
                if isinstance(batch_result, list):
                    results.extend(batch_result)
                else:
                    results.append(batch_result)
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
        
        return results
    
    def process_patterns_parallel(self, data_groups: Dict[str, List], pattern_func: Callable) -> Dict[str, Any]:
        """Process pattern analysis in parallel for different data groups."""
        if not data_groups:
            return {}
        
        # Submit pattern analysis tasks
        futures = {
            group_name: self.executor.submit(pattern_func, group_data)
            for group_name, group_data in data_groups.items()
        }
        
        results = {}
        for group_name, future in futures.items():
            try:
                results[group_name] = future.result()
            except Exception as e:
                logger.error(f"Pattern processing error for {group_name}: {e}")
                results[group_name] = {}
        
        return results
    
    def __del__(self):
        """Cleanup executor."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


class CacheManager:
    """Optimized caching for learning components."""
    
    def __init__(self, max_cache_size: int = 1000):
        """Initialize cache manager."""
        self.max_cache_size = max_cache_size
        self.cache = {}
        self.access_times = {}
        self.cache_stats = defaultdict(int)
        self._lock = threading.Lock()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get item from cache."""
        with self._lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                self.cache_stats['hits'] += 1
                return self.cache[key]
            else:
                self.cache_stats['misses'] += 1
                return default
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set item in cache with optional TTL."""
        with self._lock:
            # Evict old items if cache is full
            if len(self.cache) >= self.max_cache_size:
                self._evict_lru()
            
            self.cache[key] = {
                'value': value,
                'created_at': time.time(),
                'ttl': ttl
            }
            self.access_times[key] = time.time()
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def cleanup_expired(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, item in self.cache.items():
                if item.get('ttl') and (current_time - item['created_at']) > item['ttl']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                del self.access_times[key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        with self._lock:
            total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
            hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_cache_size,
                'hit_rate': hit_rate,
                'total_hits': self.cache_stats['hits'],
                'total_misses': self.cache_stats['misses']
            }


class MemoryOptimizer:
    """Memory optimization utilities."""
    
    @staticmethod
    def optimize_dataframes(df_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize pandas DataFrames memory usage."""
        try:
            import pandas as pd
            
            for key, df in df_dict.items():
                if isinstance(df, pd.DataFrame):
                    # Optimize dtypes
                    for col in df.select_dtypes(include=['int64']).columns:
                        df[col] = pd.to_numeric(df[col], downcast='integer')
                    
                    for col in df.select_dtypes(include=['float64']).columns:
                        df[col] = pd.to_numeric(df[col], downcast='float')
                    
                    # Convert object columns to categories if appropriate
                    for col in df.select_dtypes(include=['object']).columns:
                        if df[col].nunique() < len(df) * 0.5:  # Less than 50% unique values
                            df[col] = df[col].astype('category')
        
        except ImportError:
            logger.warning("Pandas not available for DataFrame optimization")
        
        return df_dict
    
    @staticmethod
    def force_garbage_collection():
        """Force garbage collection and return memory stats."""
        collected = gc.collect()
        return {
            'objects_collected': collected,
            'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024
        }
    
    @staticmethod
    def get_memory_usage_by_type() -> Dict[str, int]:
        """Get memory usage breakdown by object type."""
        import sys
        from collections import Counter
        
        # Count objects by type
        type_counts = Counter()
        for obj in gc.get_objects():
            type_counts[type(obj).__name__] += 1
        
        return dict(type_counts.most_common(20))


# Global instances
profiler = PerformanceProfiler()
cache_manager = CacheManager()
batch_processor = BatchProcessor()

# Decorator for easy profiling
def profile_performance(func_name: str = None):
    """Easy-to-use performance profiling decorator."""
    return profiler.profile_function(func_name)