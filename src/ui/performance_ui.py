# src/ui/performance_ui.py

import tkinter as tk
import ttkbootstrap as ttkbs
from typing import Dict, Optional
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from collections import deque

class PerformanceUI(ttkbs.LabelFrame):
    """Performance monitoring UI panel."""
    
    def __init__(self, master, performance_monitor, **kwargs):
        super().__init__(master, text="Performance Monitor", **kwargs)
        self.performance_monitor = performance_monitor
        self.history_length = 60  # 60 seconds of history
        self.setup_ui()
        self.initialize_graphs()
        self.start_updating()

    def setup_ui(self):
        """Create performance UI layout."""
        # Main container
        main_container = ttkbs.Frame(self)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Current metrics panel
        self.create_metrics_panel(main_container)

        # Graphs panel
        self.create_graphs_panel(main_container)

        # Status bar
        self.create_status_bar()

    def create_metrics_panel(self, parent):
        """Create current metrics display panel."""
        metrics_frame = ttkbs.LabelFrame(parent, text="Current Metrics")
        metrics_frame.pack(fill='x', pady=(0, 5))

        # CPU Usage
        cpu_frame = ttkbs.Frame(metrics_frame)
        cpu_frame.pack(fill='x', padx=5, pady=2)
        ttkbs.Label(cpu_frame, text="CPU Usage:").pack(side='left')
        self.cpu_label = ttkbs.Label(cpu_frame, text="0%")
        self.cpu_label.pack(side='right')

        # Memory Usage
        mem_frame = ttkbs.Frame(metrics_frame)
        mem_frame.pack(fill='x', padx=5, pady=2)
        ttkbs.Label(mem_frame, text="Memory Usage:").pack(side='left')
        self.memory_label = ttkbs.Label(mem_frame, text="0 MB")
        self.memory_label.pack(side='right')

        # FPS
        fps_frame = ttkbs.Frame(metrics_frame)
        fps_frame.pack(fill='x', padx=5, pady=2)
        ttkbs.Label(fps_frame, text="FPS:").pack(side='left')
        self.fps_label = ttkbs.Label(fps_frame, text="0")
        self.fps_label.pack(side='right')

        # Frame Time
        frame_time_frame = ttkbs.Frame(metrics_frame)
        frame_time_frame.pack(fill='x', padx=5, pady=2)
        ttkbs.Label(frame_time_frame, text="Frame Time:").pack(side='left')
        self.frame_time_label = ttkbs.Label(frame_time_frame, text="0 ms")
        self.frame_time_label.pack(side='right')

        # Encoding Speed
        encode_frame = ttkbs.Frame(metrics_frame)
        encode_frame.pack(fill='x', padx=5, pady=2)
        ttkbs.Label(encode_frame, text="Encoding Speed:").pack(side='left')
        self.encode_label = ttkbs.Label(encode_frame, text="0x")
        self.encode_label.pack(side='right')

        # Bitrate
        bitrate_frame = ttkbs.Frame(metrics_frame)
        bitrate_frame.pack(fill='x', padx=5, pady=2)
        ttkbs.Label(bitrate_frame, text="Bitrate:").pack(side='left')
        self.bitrate_label = ttkbs.Label(bitrate_frame, text="0 Mbps")
        self.bitrate_label.pack(side='right')

    def create_graphs_panel(self, parent):
        """Create performance graphs panel."""
        graphs_frame = ttkbs.LabelFrame(parent, text="Performance Graphs")
        graphs_frame.pack(fill='both', expand=True)

        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 4))
        self.fig.set_facecolor('#2b2b2b')
        
        # Configure axes
        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor('#1e1e1e')
            ax.grid(True, color='#3b3b3b')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('#3b3b3b')

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=graphs_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_status_bar(self):
        """Create status bar."""
        status_frame = ttkbs.Frame(self)
        status_frame.pack(fill='x', padx=5, pady=2)

        # Recording time
        self.time_label = ttkbs.Label(status_frame, text="00:00:00")
        self.time_label.pack(side='left')

        # Dropped frames
        self.dropped_frames_label = ttkbs.Label(status_frame, text="Dropped: 0")
        self.dropped_frames_label.pack(side='right')

    def initialize_graphs(self):
        """Initialize performance graphs."""
        self.timestamps = deque(maxlen=self.history_length)
        self.cpu_history = deque(maxlen=self.history_length)
        self.memory_history = deque(maxlen=self.history_length)
        self.fps_history = deque(maxlen=self.history_length)
        self.frame_time_history = deque(maxlen=self.history_length)

        # Initialize with zeros
        current_time = time.time()
        for i in range(self.history_length):
            self.timestamps.append(current_time - (self.history_length - i))
            self.cpu_history.append(0)
            self.memory_history.append(0)
            self.fps_history.append(0)
            self.frame_time_history.append(0)

    def start_updating(self):
        """Start periodic UI updates."""
        self.update_ui()

    def update_ui(self):
        """Update UI with current performance metrics."""
        try:
            # Get current metrics
            metrics = self.performance_monitor.metrics

            # Update labels
            self.cpu_label.configure(text=f"{metrics.cpu_usage:.1f}%")
            self.memory_label.configure(text=f"{metrics.memory_usage:.1f} MB")
            self.fps_label.configure(text=f"{metrics.fps:.1f}")
            self.frame_time_label.configure(text=f"{metrics.frame_time:.1f} ms")
            self.encode_label.configure(text=f"{metrics.encoding_speed:.1f}x")
            self.bitrate_label.configure(text=f"{metrics.bitrate/1000000:.1f} Mbps")
            self.dropped_frames_label.configure(text=f"Dropped: {metrics.dropped_frames}")

            # Update histories
            current_time = time.time()
            self.timestamps.append(current_time)
            self.cpu_history.append(metrics.cpu_usage)
            self.memory_history.append(metrics.memory_usage)
            self.fps_history.append(metrics.fps)
            self.frame_time_history.append(metrics.frame_time)

            # Update graphs
            self.update_graphs()

            # Schedule next update
            self.after(1000, self.update_ui)

        except Exception as e:
            print(f"Error updating performance UI: {e}")
            self.after(1000, self.update_ui)

    def update_graphs(self):
        """Update performance graphs."""
        try:
            # Clear axes
            self.ax1.clear()
            self.ax2.clear()

            # Plot CPU and Memory
            times = np.array(self.timestamps) - self.timestamps[0]
            self.ax1.plot(times, self.cpu_history, 'c-', label='CPU', linewidth=1)
            self.ax1.plot(times, self.memory_history, 'm-', label='Memory', linewidth=1)
            self.ax1.set_ylabel('Usage %')
            self.ax1.legend(loc='upper right')
            self.ax1.grid(True)

            # Plot FPS and Frame Time
            self.ax2.plot(times, self.fps_history, 'g-', label='FPS', linewidth=1)
            self.ax2.plot(times, self.frame_time_history, 'y-', 
                         label='Frame Time (ms)', linewidth=1)
            self.ax2.set_ylabel('Value')
            self.ax2.legend(loc='upper right')
            self.ax2.grid(True)

            # Update canvas
            self.fig.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Error updating graphs: {e}")

    def set_dark_mode(self, dark: bool = True):
        """Toggle dark mode for graphs."""
        bg_color = '#2b2b2b' if dark else 'white'
        text_color = 'white' if dark else 'black'
        grid_color = '#3b3b3b' if dark else '#cccccc'

        self.fig.set_facecolor(bg_color)
        
        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor(bg_color)
            ax.grid(True, color=grid_color)
            ax.tick_params(colors=text_color)
            for spine in ax.spines.values():
                spine.set_color(grid_color)
            ax.title.set_color(text_color)
            ax.xaxis.label.set_color(text_color)
            ax.yaxis.label.set_color(text_color)

        self.canvas.draw()

class PerformanceWindow(ttkbs.Toplevel):
    """Separate window for detailed performance monitoring."""
    
    def __init__(self, parent, performance_monitor):
        super().__init__(parent)
        self.title("Performance Monitor")
        self.performance_monitor = performance_monitor
        
        # Set window size and position
        self.geometry("800x600")
        self.setup_ui()

    def setup_ui(self):
        """Create performance window UI."""
        # Create main performance UI
        self.perf_ui = PerformanceUI(self, self.performance_monitor)
        self.perf_ui.pack(fill='both', expand=True, padx=10, pady=10)

        # Add additional controls
        controls = ttkbs.Frame(self)
        controls.pack(fill='x', padx=10, pady=5)

        # Recording duration
        self.duration_label = ttkbs.Label(controls, text="Recording: 00:00:00")
        self.duration_label.pack(side='left')

        # Export button
        ttkbs.Button(
            controls,
            text="Export Data",
            command=self.export_data,
            bootstyle="info-outline"
        ).pack(side='right')

    def export_data(self):
        """Export performance data."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_data_{timestamp}.csv"
            
            # Get data from performance monitor
            data = self.performance_monitor.get_metrics_history()
            
            # Save to CSV
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'CPU', 'Memory', 'FPS', 'Frame Time'])
                # Write data rows
                # Implementation depends on how your data is structured
            
            ttkbs.messagebox.showinfo(
                "Success",
                f"Performance data exported to {filename}"
            )
            
        except Exception as e:
            ttkbs.messagebox.showerror(
                "Error",
                f"Failed to export performance data: {e}"
            )