# src/app.py

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttkbs
import logging
from typing import Optional
import threading

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import components
from src.ui.main_window import MainWindow
from src.ui.settings_window import SettingsWindow
from src.utils.platform_utils import PlatformManager
from src.utils.config_manager import ConfigManager
from src.utils.error_handler import ErrorHandler
from src.utils.performance_monitor import PerformanceMonitor
from src.utils.performance import PerformanceUtils, PerformanceOptimizer
from src.utils.resource_manager import ResourceManager
from src.utils.device_manager import DeviceManager
from src.utils.video_manager import VideoManager

from src.features.recording import RecordingManager
from src.features.audio_mixer import AudioMixer
from src.features.effects import EffectsManager
from src.features.recording_scheduler import RecordingScheduler
from src.features.transitions import TransitionManager
from src.clipper import Clipper
from src.constants import *

class VoiceClips:
    """Main application class."""
    
    def __init__(self):
        self.logger = None
        self.setup_logging()
        self.logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

        # Initialize managers
        self.init_managers()
        
        # Create main window
        self.create_main_window()
        
        # Setup error handling
        self.setup_error_handling()
        
        self.logger.info("Application initialized successfully")

    def setup_logging(self):
        """Initialize logging system."""
        try:
            # Create logs directory
            log_dir = Path(DEFAULT_LOGS_PATH)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Setup logging configuration
            logging.basicConfig(
                level=logging.INFO,
                format=LOG_FORMAT,
                datefmt=LOG_DATE_FORMAT,
                handlers=[
                    logging.FileHandler(log_dir / "app.log"),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")
            sys.exit(1)

    def init_managers(self):
        """Initialize all manager components."""
        try:
            # Platform utilities
            self.platform = PlatformManager()
            
            # Check dependencies
            if not self.platform.check_dependencies():
                messagebox.showerror("Error", ERROR_MESSAGES["ffmpeg_not_found"])
                sys.exit(1)

            # Configuration
            self.config = ConfigManager(DEFAULT_CONFIG_PATH)
            
            # Error handling
            self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)
            
            # Resource management
            self.resource_manager = ResourceManager(
                os.path.join(project_root, "resources")
            )
            
            # Device management
            self.device_manager = DeviceManager()
            
            # Performance monitoring
            self.performance_monitor = PerformanceMonitor()
            self.performance_utils = PerformanceUtils()
            self.performance_optimizer = PerformanceOptimizer()
            
            # Audio/Video components
            self.video_manager = VideoManager()
            self.video_manager.start_capture()
            self.audio_mixer = AudioMixer(self.config)
            self.effects_manager = EffectsManager()
            self.recording_manager = RecordingManager(self.config)
            
            # Recording features
            self.recording_scheduler = RecordingScheduler(
                self.recording_manager.start_recording
            )
            self.transition_manager = TransitionManager()
            
            # Clipper
            self.clipper = Clipper(
                buffer_duration=self.config.get("clipping.duration", DEFAULT_CLIP_DURATION),
                output_folder=self.config.get("clipping.save_path", DEFAULT_CLIPS_FOLDER),
                format=self.config.get("clipping.format", DEFAULT_CLIP_FORMAT)
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize managers: {e}")
            messagebox.showerror("Error", f"Failed to initialize application: {e}")
            sys.exit(1)
    def initialize_recording(self):
        """Initialize recording components."""
        try:
            # Start required managers
            self.recording_scheduler.start()
            self.audio_mixer.start_monitoring()
            self.performance_monitor.start()
            
            # Initialize clipper with audio/video managers
            self.clipper.set_managers(
                self.video_manager,
                self.audio_mixer
            )
            
            self.logger.info("Recording components initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing recording: {e}")

    def create_main_window(self):
        """Create main application window."""
        try:
            # Get theme
            theme = self.config.get("general.theme", UI_THEME)
            if theme not in VALID_THEMES:
                theme = UI_THEME
            
            # Create root window
            self.root = ttkbs.Window(
                title=APP_NAME,
                themename=theme
            )
            
            # Set window size and position
            width, height = map(int, UI_DEFAULT_SIZE.split('x'))
            min_width, min_height = map(int, UI_MIN_SIZE.split('x'))
            
            self.root.geometry(f"{width}x{height}")
            self.root.minsize(min_width, min_height)
            
            # Create main window UI
            self.main_window = MainWindow(
                root=self.root,
                config=self.config
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create main window: {e}")
            messagebox.showerror("Error", f"Failed to create application window: {e}")
            sys.exit(1)

    def setup_error_handling(self):
        """Configure error handling."""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                self.root.destroy()
                return

            self.logger.error(
                "Uncaught exception",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            messagebox.showerror(
                "Error",
                f"An unexpected error occurred: {exc_value}"
            )

        # Set exception handlers
        sys.excepthook = handle_exception
        threading.excepthook = lambda args: handle_exception(
            args.exc_type, args.exc_value, args.exc_traceback
        )
    # Add this method to the VoiceClips class in app.py

    def open_settings(self):
        """Open settings window."""
        try:
            settings_window = SettingsWindow(self.root, self.config)
            settings_window.wait_window()  # Wait for settings window to close
            
            # Apply new settings if needed
            if settings_window.settings_changed:
                self.apply_settings()
                
        except Exception as e:
            self.logger.error(f"Error opening settings: {e}")
            messagebox.showerror("Error", f"Failed to open settings: {e}")

    def apply_settings(self):
        """Apply updated settings to all components."""
        try:
            # Update theme
            new_theme = self.config.get("general.theme", UI_THEME)
            if new_theme in VALID_THEMES:
                self.root.style.theme_use(new_theme)

            # Update recording settings
            self.recording_manager.update_settings({
                "format": self.config.get("recording.format", DEFAULT_FILE_EXTENSION),
                "save_path": self.config.get("recording.save_path", DEFAULT_RECORDINGS_FOLDER),
                "quality": self.config.get("video.quality", "High")
            })

            # Update audio settings
            self.audio_mixer.update_settings({
                "mic_device": self.config.get("audio.mic_device", "Default"),
                "desktop_device": self.config.get("audio.desktop_device", "Default"),
                "mic_volume": self.config.get("audio.mic_volume", DEFAULT_MIC_VOLUME),
                "desktop_volume": self.config.get("audio.desktop_volume", DEFAULT_DESKTOP_VOLUME)
            })

            # Update clipper settings
            self.clipper.update_settings({
                "duration": self.config.get("clipping.duration", DEFAULT_CLIP_DURATION),
                "format": self.config.get("clipping.format", DEFAULT_CLIP_FORMAT),
                "save_path": self.config.get("clipping.save_path", DEFAULT_CLIPS_FOLDER)
            })

            # Update performance settings
            if self.config.get("performance.priority") == "High":
                self.performance_optimizer.set_optimization_threshold(0.7)  # More aggressive optimization
            else:
                self.performance_optimizer.set_optimization_threshold(0.8)  # Default threshold

            self.logger.info("Settings applied successfully")
            messagebox.showinfo("Success", SUCCESS_MESSAGES["settings_saved"])

        except Exception as e:
            self.logger.error(f"Error applying settings: {e}")
            messagebox.showerror("Error", f"Failed to apply settings: {e}")

    def run(self):
        """Start the application."""
        try:
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error running application: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        try:
            # Save configuration
            self.config.save()
            
            # Stop components
            self.performance_monitor.stop()
            self.recording_scheduler.stop()
            self.clipper.cleanup()
            self.recording_manager.cleanup()
            self.audio_mixer.cleanup()
            self.device_manager.cleanup()
            
            # Performance cleanup
            self.performance_utils.cleanup()
            
            self.logger.info("Application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

def main():
    """Application entry point."""
    app = VoiceClips()
    app.run()

if __name__ == "__main__":
    main()