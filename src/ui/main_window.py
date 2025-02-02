import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttkbs
import shutil
import logging
import threading
from typing import Optional, Dict, Any
import time
import mss
from PIL import Image, ImageTk

# Local imports
from src.constants import *
from src.utils.error_handler import ErrorHandler
from src.utils.performance_monitor import PerformanceMonitor
from src.utils.video_manager import VideoManager
from src.utils.audio_manager import AudioManager
from src.features.recording import RecordingManager
from src.features.effects import EffectsManager
from src.features.audio_mixer import AudioMixer
from src.features.recording_scheduler import RecordingScheduler

# Import UI components
from src.ui.custom_widgets import (
    ToolBar, ScenesList, SourcesList, 
    PreviewMonitor, RecordingControls, StatusBar
)
from src.clipper import Clipper
from src.ui.settings_window import SettingsWindow
from src.ui.audio_mixer_widget import AudioMixerWidget
from src.ui.effects_panel import EffectsPanel

class MainWindow:
    def __init__(self, root: ttkbs.Window, config: Dict):
        self.root = root
        self.config = config
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)
        
        # Initialize managers
        self.init_managers()
        
        # Initialize recording
        self.initialize_recording()
        
        # Setup UI
        self.setup_ui()
        
        # Setup bindings
        self.setup_bindings()
        
        # Start monitoring
        self.start_monitoring()
        
        # Start preview
        self.start_preview()

    def init_managers(self):
        """Initialize all managers."""
        try:
            # Core managers
            self.video_manager = VideoManager()
            self.audio_manager = AudioManager()
            self.recording_manager = RecordingManager(self.config)
            
            # Feature managers
            self.effects_manager = EffectsManager()
            self.audio_mixer = AudioMixer(self.config)
            self.recording_scheduler = RecordingScheduler(
                self.recording_manager.start_recording
            )
            
            # Performance monitoring
            self.performance_monitor = PerformanceMonitor()
            
            # Initialize clipper
            self.clipper = Clipper(
                buffer_duration=self.config.get("clipping.duration", DEFAULT_CLIP_DURATION),
                output_folder=self.config.get("clipping.save_path", DEFAULT_CLIPS_FOLDER),
                format=self.config.get("clipping.format", DEFAULT_CLIP_FORMAT)
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Initializing managers")
            raise

    def initialize_recording(self):
        """Initialize recording components."""
        try:
            # Start required managers
            self.video_manager.start_capture()
            self.audio_mixer.start_monitoring()
            
            # Initialize clipper with managers
            self.clipper.set_managers(
                self.video_manager,
                self.audio_mixer
            )
            
            # Start recording scheduler
            self.recording_scheduler.start()
            
            self.logger.info("Recording components initialized")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Initializing recording")

    def setup_ui(self):
        """Create main UI layout."""
        try:
            # Main container
            self.main_container = ttkbs.Frame(self.root, padding=10)
            self.main_container.pack(fill=tk.BOTH, expand=True)

            # Create layout sections
            self.create_toolbar()
            self.create_main_content()
            self.create_status_bar()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Setting up UI")
            raise

    def create_toolbar(self):
        """Create top toolbar."""
        self.toolbar = ToolBar(self.main_container)
        self.toolbar.pack(fill='x', pady=(0, 10))

        # Recording controls
        self.record_button = self.toolbar.add_button(
            "⏺ Record",
            self.toggle_recording,
            bootstyle="danger"
        )
        
        self.pause_button = self.toolbar.add_button(
            "⏸ Pause",
            self.toggle_pause,
            bootstyle="warning",
            state='disabled'
        )

        # Settings and tools
        self.toolbar.add_spacer()
        
        self.settings_button = self.toolbar.add_button(
            "⚙ Settings",
            self.open_settings,
            bootstyle="info"
        )

    def create_main_content(self):
        """Create main content area."""
        # Content container
        content = ttkbs.PanedWindow(self.main_container, orient='horizontal')
        content.pack(fill=tk.BOTH, expand=True)

        # Left sidebar (Scenes/Sources)
        self.create_left_sidebar(content)

        # Center area (Preview)
        self.create_preview_area(content)

        # Right sidebar (Audio/Effects)
        self.create_right_sidebar(content)

    def create_left_sidebar(self, parent):
        """Create left sidebar."""
        left_sidebar = ttkbs.Frame(parent, width=250)
        parent.add(left_sidebar, weight=1)

        # Scenes list
        self.scenes_list = ScenesList(left_sidebar)
        self.scenes_list.pack(fill='both', expand=True, pady=(0, 10))

        # Sources list
        self.sources_list = SourcesList(left_sidebar)
        self.sources_list.pack(fill='both', expand=True)

    def create_preview_area(self, parent):
        """Create preview area."""
        preview_frame = ttkbs.Frame(parent)
        parent.add(preview_frame, weight=3)

        # Add size constraints to preview
        preview_frame.configure(width=640, height=360)  # 16:9 ratio
        preview_frame.pack_propagate(False)  # Prevent automatic resizing

        # Preview monitor
        self.preview = PreviewMonitor(preview_frame)
        self.preview.pack(fill='both', expand=True, pady=(0, 10))

        # Recording controls
        self.recording_controls = RecordingControls(preview_frame, self)
        self.recording_controls.pack(fill='x', pady=(0, 10))

    def create_right_sidebar(self, parent):
        """Create right sidebar."""
        right_sidebar = ttkbs.Frame(parent, width=300)
        parent.add(right_sidebar, weight=1)

        # Audio mixer
        self.mixer = AudioMixerWidget(right_sidebar, self.audio_mixer)
        self.mixer.pack(fill='both', expand=True, pady=(0, 10))

        # Effects panel
        self.effects = EffectsPanel(right_sidebar, self.effects_manager)
        self.effects.pack(fill='both', expand=True)

    def create_status_bar(self):
        """Create status bar."""
        self.status_bar = StatusBar(self.main_container)
        self.status_bar.pack(fill='x')

    def setup_bindings(self):
        """Setup keyboard shortcuts and event bindings."""
        try:
            # Keyboard shortcuts
            self.root.bind('<Control-r>', lambda e: self.toggle_recording())
            self.root.bind('<Control-p>', lambda e: self.toggle_pause())
            self.root.bind('<Control-s>', lambda e: self.open_settings())
            self.root.bind('<Control-q>', lambda e: self.quit_app())
            self.root.bind('<Control-c>', lambda e: self.create_clip())
            
            # Window events
            self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
            
            # Performance update timer
            self.root.after(1000, self.update_performance)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Setting up bindings")

    def start_monitoring(self):
        """Start performance and preview monitoring."""
        try:
            # Start performance monitoring
            self.performance_monitor.start()
            
            # Start preview update
            self.preview_active = True
            self.update_preview()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Starting monitoring")

    def start_preview(self):
        """Start preview display."""
        try:
            if not self.video_manager.is_capturing:
                self.video_manager.start_capture()
                
            # Update preview
            self.update_preview()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Starting preview")

    def update_preview(self):
        """Update preview display."""
        if not self.preview_active:
            return
            
        try:
            # Get frame from video manager
            frame = self.video_manager.get_frame()
            
            if frame is not None:
                # Apply effects
                frame = self.effects_manager.process_frame(frame)
                
                # Convert to PhotoImage
                image = Image.fromarray(frame.data)
                photo = ImageTk.PhotoImage(image)
                
                # Update preview
                self.preview.update_preview(photo)
            
            # Schedule next update
            self.root.after(33, self.update_preview)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Updating preview")
            self.root.after(1000, self.update_preview)

    def update_performance(self):
        """Update performance display."""
        try:
            stats = self.performance_monitor.get_current_metrics()
            
            # Update status bar
            self.status_bar.set_fps(stats.get('fps', 0))
            self.status_bar.set_cpu(f"CPU: {stats.get('cpu_usage', 0):.1f}%")
            self.status_bar.set_memory(f"RAM: {stats.get('memory_usage', 0):.1f}%")
            
            # Update recording time if recording
            if hasattr(self.recording_manager, 'state') and self.recording_manager.state.is_recording:
                duration = self.recording_manager.get_recording_duration()
                self.update_time(duration)
            
            # Schedule next update
            self.root.after(1000, self.update_performance)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Updating performance")
            self.root.after(1000, self.update_performance)

    def update_time(self, duration: float):
        """Update recording time display."""
        try:
            if hasattr(self, 'recording_controls'):
                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                seconds = int(duration % 60)
                
                time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.recording_controls.time_label.configure(text=time_text)
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Updating time display")

    def toggle_recording(self):
        """Toggle recording state."""
        try:
            if not self.recording_manager.state.is_recording:
                self.start_recording()
            else:
                self.stop_recording()
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Toggling recording")

    def start_recording(self):
        """Start recording."""
        try:
            # Validate settings
            if not self.validate_recording_settings():
                return
            
            # Start video and audio capture if not already started
            if not self.video_manager.is_capturing:
                self.video_manager.start_capture()
            if not self.audio_manager.is_capturing:
                self.audio_manager.start_capture()
                
            # Update UI
            self.record_button.configure(
                text="⏹ Stop",
                bootstyle="danger"
            )
            self.pause_button.configure(state='normal')
            
            # Start recording
            if self.recording_manager.start_recording():
                self.status_bar.set_status("Recording...")
                self.recording_controls.start_timer()
            else:
                raise Exception("Failed to start recording")
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Starting recording")
            self.reset_recording_ui()

    def stop_recording(self):
        """Stop recording."""
        try:
            # Stop recording
            if self.recording_manager.stop_recording():
                # Update UI
                self.reset_recording_ui()
                self.status_bar.set_status("Ready")
                self.recording_controls.stop_timer()
            else:
                raise Exception("Failed to stop recording")
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Stopping recording")

    def toggle_pause(self):
        """Toggle pause state."""
        try:
            if self.recording_manager.toggle_pause():
                # Update UI
                is_paused = self.recording_manager.state.is_paused
                self.pause_button.configure(
                    text="▶ Resume" if is_paused else "⏸ Pause"
                )
                self.status_bar.set_status(
                    "Paused" if is_paused else "Recording..."
                )
                
                if is_paused:
                    self.recording_controls.pause_timer()
                else:
                    self.recording_controls.resume_timer()
                    
        except Exception as e:
            self.error_handler.handle_error(e, context="Toggling pause")

    def create_clip(self):
        """Create a clip from recent footage."""
        try:
            if self.clipper.save_clip():
                self.status_bar.set_status("Clip created!")
                self.root.after(2000, lambda: self.status_bar.set_status("Ready"))
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Creating clip")

    def handle_hotkey(self, hotkey: str):
        """Handle global hotkey press."""
        try:
            if hotkey == "record":
                self.toggle_recording()
            elif hotkey == "clip":
                self.create_clip()
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Handling hotkey")

    def open_settings(self):
        """Open settings window."""
        try:
            settings_window = SettingsWindow(self.root, self.config)
            settings_window.wait_window()
            
            # Apply new settings if needed
            if settings_window.settings_changed:
                self.apply_settings()
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Opening settings")

    def apply_settings(self):
        """Apply updated settings."""
        try:
            # Update video settings
            self.video_manager.update_settings({
                "resolution": self.config.get("video.resolution", BASE_CANVAS_RESOLUTION),
                "fps": self.config.get("video.fps", DEFAULT_FPS),
                "quality": self.config.get("video.quality", "High")
            })
            
            # Update audio settings
            self.audio_mixer.update_settings({
                "mic_device": self.config.get("audio.mic_device", "Default"),
                "desktop_device": self.config.get("audio.desktop_device", "Default"),
                "mic_volume": self.config.get("audio.mic_volume", DEFAULT_MIC_VOLUME),
                "desktop_volume": self.config.get("audio.desktop_volume", DEFAULT_DESKTOP_VOLUME)
            })
            
            # Update recording settings
            self.recording_manager.update_settings({
                "format": self.config.get("recording.format", DEFAULT_FILE_EXTENSION),
                "save_path": self.config.get("recording.save_path", DEFAULT_RECORDINGS_FOLDER)
            })
            
            # Update clipper settings
            self.clipper.update_settings({
                "duration": self.config.get("clipping.duration", DEFAULT_CLIP_DURATION),
                "format": self.config.get("clipping.format", DEFAULT_CLIP_FORMAT),
                "save_path": self.config.get("clipping.save_path", DEFAULT_CLIPS_FOLDER)
            })
            
            # Update UI theme
            new_theme = self.config.get("general.theme", UI_THEME)
            if new_theme in VALID_THEMES:
                self.root.style.theme_use(new_theme)
                
            self.logger.info("Settings applied successfully")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Applying settings")

    def validate_recording_settings(self) -> bool:
        """Validate recording settings."""
        try:
            # Check save path
            save_path = Path(self.config.get("recording.save_path", DEFAULT_RECORDINGS_FOLDER))
            if not save_path.exists():
                save_path.mkdir(parents=True, exist_ok=True)
            
            # Check disk space
            free_space = shutil.disk_usage(str(save_path)).free
            if free_space < 1024 * 1024 * 1024:  # 1 GB
                messagebox.showerror("Error", ERROR_MESSAGES["no_disk_space"])
                return False
            
            # Validate video device
            if not self.video_manager.current_device:
                messagebox.showerror("Error", ERROR_MESSAGES["no_video_devices"])
                return False
            
            # Validate audio devices
            if not self.audio_mixer.devices:
                messagebox.showerror("Error", ERROR_MESSAGES["no_audio_devices"])
                return False
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Validating settings")
            return False

    def reset_recording_ui(self):
        """Reset recording UI elements."""
        self.record_button.configure(
            text="⏺ Record",
            bootstyle="danger"
        )
        self.pause_button.configure(
            text="⏸ Pause",
            state='disabled'
        )

    def quit_app(self):
        """Quit application."""
        try:
            # Check if recording
            if self.recording_manager.state.is_recording:
                if not messagebox.askyesno(
                    "Quit",
                    "Recording is in progress. Are you sure you want to quit?"
                ):
                    return
            
            # Stop monitoring
            self.preview_active = False
            self.performance_monitor.stop()
            
            # Cleanup resources
            self.cleanup()
            
            # Quit
            self.root.quit()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Quitting application")
            self.root.quit()

    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop recording if active
            if self.recording_manager.is_recording:
                self.recording_manager.stop_recording()
            
            # Clean up managers
            self.video_manager.cleanup()
            self.audio_manager.cleanup()
            self.recording_manager.cleanup()
            self.audio_mixer.cleanup()
            self.performance_monitor.cleanup()
            
            # Clean up clipper
            self.clipper.cleanup()
            
            # Stop recording scheduler
            self.recording_scheduler.stop()
            
            # Save configuration
            self.config.save()
            
            self.logger.info("Cleanup completed successfully")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Cleanup")

                