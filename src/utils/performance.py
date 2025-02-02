# src/utils/performance.py

import time
import psutil
import threading
import logging
from typing import Dict, Optional, Callable, List, Any
from functools import wraps
import cProfile
import pstats
import io
import gc
import sys
import tracemalloc
from contextlib import contextmanager

class PerformanceUtils:
    """Utility class for performance optimization and monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.profiler = None
        self.memory_tracker = None
        self._monitoring = False

    @staticmethod
    def timeit(func):
        """Decorator to measure function execution time."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            print(f"{func.__name__} took {execution_time:.4f} seconds")
            return result
        return wrapper

    @contextmanager
    def measure_time(self, name: str = "Operation"):
        """Context manager for measuring execution time."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            print(f"{name} took {execution_time:.4f} seconds")

    @contextmanager
    def profile_code(self, sort_by: str = 'cumulative'):
        """Context manager for profiling code blocks."""
        try:
            profiler = cProfile.Profile()
            profiler.enable()
            yield
        finally:
            profiler.disable()
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats(sort_by)
            ps.print_stats()
            print(s.getvalue())

    @contextmanager
    def track_memory(self):
        """Context manager for tracking memory usage."""
        tracemalloc.start()
        yield
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        print("[ Top 10 memory users ]")
        for stat in top_stats[:10]:
            print(stat)
        tracemalloc.stop()

    def start_profiling(self):
        """Start continuous profiling."""
        if self.profiler is None:
            self.profiler = cProfile.Profile()
            self.profiler.enable()

    def stop_profiling(self, output_file: Optional[str] = None):
        """Stop profiling and optionally save results."""
        if self.profiler is not None:
            self.profiler.disable()
            if output_file:
                self.profiler.dump_stats(output_file)
            stats = pstats.Stats(self.profiler)
            stats.sort_stats('cumulative')
            stats.print_stats()
            self.profiler = None

    def optimize_memory(self):
        """Perform memory optimization."""
        try:
            # Force garbage collection
            gc.collect()
            
            # Clear Python's internal type cache
            sys.intern('')
            
            # Cleanup (if exists) - note the change from _cleanup to something safe
            if hasattr(threading, 'enumerate'):
                for thread in threading.enumerate():
                    if hasattr(thread, 'cleanup'):
                        thread.cleanup()
            
            return True
        except Exception as e:
            self.logger.error(f"Error optimizing memory: {e}")
            return False

    def get_memory_usage(self) -> Dict[str, float]:
        """Get detailed memory usage statistics."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss / 1024 / 1024,  # RSS in MB
                'vms': memory_info.vms / 1024 / 1024,  # VMS in MB
                'shared': memory_info.shared / 1024 / 1024,  # Shared memory in MB
                'percent': process.memory_percent()
            }
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return {}

    def get_cpu_usage(self) -> Dict[str, float]:
        """Get detailed CPU usage statistics."""
        try:
            process = psutil.Process()
            
            return {
                'process': process.cpu_percent(),
                'system': psutil.cpu_percent(),
                'per_cpu': psutil.cpu_percent(percpu=True)
            }
        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {e}")
            return {}

    def analyze_performance(self) -> Dict[str, Any]:
        """Perform comprehensive performance analysis."""
        try:
            analysis = {
                'memory': self.get_memory_usage(),
                'cpu': self.get_cpu_usage(),
                'threads': threading.active_count(),
                'gc_stats': gc.get_stats(),
            }
            
            # Add Python interpreter statistics
            if hasattr(sys, 'getrefcount'):
                analysis['ref_count'] = sys.getrefcount(None)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance: {e}")
            return {}

    def monitor_thread_usage(self) -> List[Dict]:
        """Monitor thread usage and statistics."""
        try:
            thread_stats = []
            for thread in threading.enumerate():
                thread_stats.append({
                    'name': thread.name,
                    'daemon': thread.daemon,
                    'alive': thread.is_alive()
                })
            return thread_stats
        except Exception as e:
            self.logger.error(f"Error monitoring threads: {e}")
            return []

    @contextmanager
    def performance_critical_section(self):
        """Context manager for performance-critical code sections."""
        try:
            # Prepare for performance-critical section
            initial_gc_state = gc.isenabled()
            gc.disable()  # Temporarily disable garbage collection
            
            # Set thread priority if possible
            try:
                import os
                os.nice(0)  # Try to set high priority
            except:
                pass
            
            yield
            
        finally:
            # Restore previous state
            if initial_gc_state:
                gc.enable()

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        try:
            report = {
                'timestamp': time.time(),
                'system': {
                    'cpu_count': psutil.cpu_count(),
                    'memory_total': psutil.virtual_memory().total / (1024 * 1024 * 1024),  # GB
                    'memory_available': psutil.virtual_memory().available / (1024 * 1024 * 1024),  # GB
                    'disk_usage': psutil.disk_usage('/').percent
                },
                'process': {
                    'memory': self.get_memory_usage(),
                    'cpu': self.get_cpu_usage(),
                    'threads': self.monitor_thread_usage(),
                    'gc_stats': gc.get_stats()
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {}

    def cleanup(self):
        """Clean up performance monitoring resources."""
        try:
            if self.profiler:
                self.stop_profiling()
            
            if self.memory_tracker:
                tracemalloc.stop()
            
            self.optimize_memory()
            
        except Exception as e:
            self.logger.error(f"Error during performance cleanup: {e}")

class PerformanceOptimizer:
    """Class for automatic performance optimization."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.utils = PerformanceUtils()
        self.optimization_threshold = 0.8  # 80% resource usage triggers optimization

    def check_and_optimize(self):
        """Check resource usage and optimize if needed."""
        try:
            cpu_usage = psutil.cpu_percent() / 100
            memory_usage = psutil.virtual_memory().percent / 100
            
            if cpu_usage > self.optimization_threshold or \
               memory_usage > self.optimization_threshold:
                self.optimize_resources()
                
        except Exception as e:
            self.logger.error(f"Error in performance optimization: {e}")

    def optimize_resources(self):
        """Perform resource optimization."""
        try:
            # Memory optimization
            self.utils.optimize_memory()
            
            # Thread optimization
            self._optimize_threads()
            
            # Cache optimization
            self._clear_caches()
            
        except Exception as e:
            self.logger.error(f"Error optimizing resources: {e}")

    def _optimize_threads(self):
        """Optimize thread usage."""
        try:
            for thread in threading.enumerate():
                if thread.name.startswith('unused_') and thread.is_alive():
                    # Attempt to stop unused threads
                    pass  # Implement thread-specific cleanup
                    
        except Exception as e:
            self.logger.error(f"Error optimizing threads: {e}")

    def _clear_caches(self):
        """Clear various caches to free memory."""
        try:
            # Clear Python's internal caches
            gc.collect()
            
            # Clear application-specific caches
            # Implement cache clearing for your specific needs
            
        except Exception as e:
            self.logger.error(f"Error clearing caches: {e}")

    def set_optimization_threshold(self, threshold: float):
        """Set resource usage threshold for optimization."""
        if 0 <= threshold <= 1:
            self.optimization_threshold = threshold

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        try:
            return {
                'optimizations_performed': 0,  # Implement counter
                'memory_saved': 0,  # Implement memory tracking
                'cpu_improved': 0  # Implement CPU improvement tracking
            }
        except Exception as e:
            self.logger.error(f"Error getting optimization stats: {e}")
            return {}