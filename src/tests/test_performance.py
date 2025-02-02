# tests/test_performance.py
from src.utils.performance_monitor import PerformanceMonitor
import time

class TestPerformance:
    def test_performance_monitoring(self):
        """Test performance monitoring."""
        monitor = PerformanceMonitor()
        monitor.start()
        
        # Simulate some work
        for _ in range(30):
            monitor.update_frame_metrics()
            time.sleep(0.033)  # Simulate 30 FPS
            
        metrics = monitor.get_metrics()
        assert metrics['fps'] > 0
        assert metrics['cpu_usage'] >= 0
        assert metrics['memory_usage'] > 0
        
        monitor.stop()

    def test_performance_history(self):
        """Test performance history tracking."""
        monitor = PerformanceMonitor(history_size=10)
        monitor.start()
        
        # Generate some history
        for _ in range(15):
            monitor.update_frame_metrics()
            time.sleep(0.1)
            
        history = monitor.get_history()
        assert len(history['fps']) <= 10  # Should respect history size
        assert len(history['cpu']) <= 10
        
        monitor.stop()