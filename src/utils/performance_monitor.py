import psutil
import time
import threading
from collections import deque
import logging
import numpy as np
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta

class PerformanceMetrics:
    def __init__(self):
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.disk_usage = 0.0
        self.fps = 0.0
        self.frame_time = 0.0
        self.dropped_frames = 0
        self.encoding_speed = 0.0
        self.bitrate = 0.0
        self.audio_levels = {}
        self.gpu_usage = 0.0
        self.timestamp = datetime.now()

class PerformanceMonitor:
    def __init__(self, callback: Optional[Callable] = None):
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.metrics = PerformanceMetrics()
        
        # Initialize current_metrics instead of relying on a non-existent attribute
        self.current_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'fps': 0.0,
            'gpu_usage': 0.0,
            'disk_usage': 0.0
        }
        
        # Initialize histories
        self.history_length = 3600  # 1 hour at 1 sample/second
        self.histories = {
            'cpu': deque(maxlen=self.history_length),
            'memory': deque(maxlen=self.history_length),
            'fps': deque(maxlen=self.history_length),
            'frame_time': deque(maxlen=self.history_length),
            'bitrate': deque(maxlen=self.history_length),
            'gpu': deque(maxlen=self.history_length)
        }

    def start(self):
        """Start performance monitoring."""
        if self.monitoring:
            return
            
        self.monitoring = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def stop(self):
        """Stop performance monitoring."""
        self.monitoring = False

    def _monitor_loop(self):
        """Main monitoring loop."""
        last_time = time.time()
        last_disk_io = psutil.disk_io_counters()
        
        while self.monitoring:
            try:
                current_time = time.time()
                elapsed = current_time - last_time
                
                # Update current_metrics
                self.current_metrics['cpu_usage'] = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                self.current_metrics['memory_usage'] = memory.percent
                
                # You can add more metrics as needed
                self.current_metrics['fps'] = 0.0  # Update with actual FPS if available
                self.current_metrics['gpu_usage'] = 0.0  # Update with actual GPU usage if available
                
                # Store in history
                self._update_histories()
                
                # Update references
                last_time = current_time
                
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {e}")
                time.sleep(5.0)

    def _update_histories(self):
        """Update history deques with current metrics."""
        try:
            self.histories['cpu'].append(self.current_metrics['cpu_usage'])
            self.histories['memory'].append(self.current_metrics['memory_usage'])
            # Add more history updates as needed
        except Exception as e:
            self.logger.error(f"Error updating histories: {e}")

    def get_current_metrics(self) -> Dict:
        """Get current performance metrics."""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'fps': self.current_metrics.get('fps', 0),
            'gpu_usage': self.current_metrics.get('gpu_usage', 0)
        }

    def cleanup(self):
        """Clean up performance monitoring resources."""
        try:
            self.monitoring = False
            # Additional cleanup if needed
        except Exception as e:
            self.logger.error(f"Error during performance cleanup: {e}")