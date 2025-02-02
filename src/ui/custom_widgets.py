# src/ui/custom_widgets.py
import tkinter as tk
import ttkbootstrap as ttkbs

class ToolBar(ttkbs.Frame):
    """Custom toolbar widget."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.buttons = []

    def add_button(self, text, command, **kwargs):
        """Add button to toolbar."""
        btn = ttkbs.Button(self, text=text, command=command, **kwargs)
        btn.pack(side='left', padx=2)
        self.buttons.append(btn)
        return btn

    def add_spacer(self):
        """Add flexible space."""
        spacer = ttkbs.Frame(self)
        spacer.pack(side='left', fill='x', expand=True)

class ScenesList(ttkbs.LabelFrame):
    """Scenes list widget."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, text="Scenes", **kwargs)
        self.setup_ui()

    def setup_ui(self):
        # Toolbar
        toolbar = ttkbs.Frame(self)
        toolbar.pack(fill='x', pady=2)
        
        ttkbs.Button(toolbar, text="+", width=3,
                    command=self.add_scene).pack(side='left', padx=2)
        ttkbs.Button(toolbar, text="-", width=3,
                    command=self.remove_scene).pack(side='left', padx=2)
        
        # Scenes listbox
        self.listbox = tk.Listbox(self, bg='#2b2b2b', fg='white')
        self.listbox.pack(fill='both', expand=True)

    def add_scene(self):
        """Add new scene."""
        pass

    def remove_scene(self):
        """Remove selected scene."""
        pass

class SourcesList(ttkbs.LabelFrame):
    """Sources list widget."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, text="Sources", **kwargs)
        self.setup_ui()

    def setup_ui(self):
        # Toolbar
        toolbar = ttkbs.Frame(self)
        toolbar.pack(fill='x', pady=2)
        
        ttkbs.Button(toolbar, text="+", width=3,
                    command=self.add_source).pack(side='left', padx=2)
        ttkbs.Button(toolbar, text="-", width=3,
                    command=self.remove_source).pack(side='left', padx=2)
        
        # Sources listbox
        self.listbox = tk.Listbox(self, bg='#2b2b2b', fg='white')
        self.listbox.pack(fill='both', expand=True)

    def add_source(self):
        """Add new source."""
        pass

    def remove_source(self):
        """Remove selected source."""
        pass

class PreviewMonitor(ttkbs.LabelFrame):
    """Preview monitor widget."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, text="Preview", **kwargs)
        self.setup_ui()

    def setup_ui(self):
        self.canvas = ttkbs.Label(self, background='black')
        self.canvas.pack(fill='both', expand=True, padx=5, pady=5)

    def update_preview(self, image):
        """Update preview image."""
        self.canvas.configure(image=image)
        self.canvas.image = image

class RecordingControls(ttkbs.Frame):
    """Recording controls widget."""
    
    def __init__(self, master, callback_handler, **kwargs):
        super().__init__(master, **kwargs)
        self.callback_handler = callback_handler
        self.recording_time = 0
        self.timer_running = False
        self.setup_ui()

    def setup_ui(self):
        # Time display
        self.time_label = ttkbs.Label(
            self,
            text="00:00:00",
            font=('Helvetica', 24)
        )
        self.time_label.pack(pady=5)

        # Controls
        controls = ttkbs.Frame(self)
        controls.pack(fill='x')
        
        self.record_button = ttkbs.Button(
            controls,
            text="⏺",
            width=3,
            command=self.toggle_recording
        )
        self.record_button.pack(side='left', padx=2)
        
        self.pause_button = ttkbs.Button(
            controls,
            text="⏸",
            width=3,
            command=self.toggle_pause,
            state='disabled'
        )
        self.pause_button.pack(side='left', padx=2)

    def toggle_recording(self):
        """Toggle recording state."""
        if not self.timer_running:
            self.start_timer()
        else:
            self.stop_timer()
        self.callback_handler.toggle_recording()

    def toggle_pause(self):
        """Toggle pause state."""
        if self.timer_running:
            self.pause_timer()
        else:
            self.resume_timer()
        self.callback_handler.toggle_pause()

    def start_timer(self):
        """Start the recording timer."""
        self.timer_running = True
        self.recording_time = 0
        self.update_timer()
        self.pause_button.configure(state='normal')

    def stop_timer(self):
        """Stop the recording timer."""
        self.timer_running = False
        self.recording_time = 0
        self.time_label.configure(text="00:00:00")
        self.pause_button.configure(state='disabled')

    def pause_timer(self):
        """Pause the recording timer."""
        self.timer_running = False

    def resume_timer(self):
        """Resume the recording timer."""
        self.timer_running = True
        self.update_timer()

    def update_timer(self):
        """Update the timer display."""
        if self.timer_running:
            hours = self.recording_time // 3600
            minutes = (self.recording_time % 3600) // 60
            seconds = self.recording_time % 60
            
            self.time_label.configure(
                text=f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            )
            
            self.recording_time += 1
            self.after(1000, self.update_timer)
class StatusBar(ttkbs.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.status_label = ttkbs.Label(self, text="Ready")
        self.status_label.pack(side='left', padx=5)
        
        self.fps_label = ttkbs.Label(self, text="FPS: 0")
        self.fps_label.pack(side='right', padx=5)
        
        # Add new labels for CPU and memory
        self.cpu_label = ttkbs.Label(self, text="CPU: 0%")
        self.cpu_label.pack(side='right', padx=5)
        
        self.memory_label = ttkbs.Label(self, text="RAM: 0MB")
        self.memory_label.pack(side='right', padx=5)

    def set_status(self, text):
        """Update status text."""
        self.status_label.configure(text=text)

    def set_fps(self, fps):
        """Update FPS display."""
        self.fps_label.configure(text=f"FPS: {fps}")
    
    # Add these new methods
    def set_cpu(self, cpu_text):
        """Update CPU usage display."""
        self.cpu_label.configure(text=cpu_text)

    def set_memory(self, memory_text):
        """Update memory usage display."""
        self.memory_label.configure(text=memory_text)
__all__ = [
    'ToolBar',
    'ScenesList',
    'SourcesList',
    'PreviewMonitor',
    'RecordingControls',
    'StatusBar'
]