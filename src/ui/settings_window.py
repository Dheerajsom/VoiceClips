# src/ui/settings_window.py
import os
import sys
from pathlib import Path
import subprocess
from typing import List, Dict, Any
import tkinter as tk
import ttkbootstrap as ttkbs
from tkinter import filedialog, messagebox

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Use absolute imports
from src.constants import *
class SettingsWindow(ttkbs.Toplevel):  # Inherit from Toplevelclass SettingsWindow(ttkbs.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        
        self.parent = parent
        self.config = config
        
        # Window setup
        self.title("Settings")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()  # Make window modal
        
        # Center the window
        self.center_window()
        
        # Initialize UI
        self.create_ui()
        self.load_current_settings()


    def center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    def create_ui(self):
        """Create settings UI."""
        # Main container
        main = ttkbs.Frame(self, padding=10)  # Changed from self.window to self
        main.pack(fill=tk.BOTH, expand=True)

        # Create split view
        self.create_sidebar(main)
        self.create_content_area(main)

        # Bottom buttons
        self.create_bottom_buttons()

    def create_sidebar(self, parent):
        """Create settings categories sidebar."""
        sidebar = ttkbs.Frame(parent, width=200)
        sidebar.pack(side='left', fill='y', padx=(0, 10))

        # Categories
        categories = [
            "General", "Video", "Audio", "Output",
            "Hotkeys", "Advanced"
        ]

        for category in categories:
            btn = ttkbs.Button(
                sidebar,
                text=category,
                command=lambda c=category: self.show_category(c),
                bootstyle="secondary-outline",
                width=20
            )
            btn.pack(pady=2)

    def create_content_area(self, parent):
        """Create main content area."""
        self.content = ttkbs.Frame(parent)
        self.content.pack(side='left', fill='both', expand=True)

        # Initialize category frames
        self.category_frames = {}
        
        # Create frames for each category
        self.create_general_settings()
        self.create_video_settings()
        self.create_audio_settings()
        self.create_output_settings()
        self.create_hotkey_settings()
        self.create_advanced_settings()

        # Show default category
        self.show_category("General")


    def create_general_settings(self):
        """Create general settings frame."""
        frame = ttkbs.Frame(self.content)
        self.category_frames["General"] = frame

        # Language selection
        ttkbs.Label(frame, text="Language:").pack(anchor='w', pady=(0, 5))
        self.language_var = tk.StringVar()
        ttkbs.Combobox(
            frame,
            textvariable=self.language_var,
            values=["English", "Spanish", "French"]
        ).pack(fill='x', pady=(0, 10))

        # Theme selection
        ttkbs.Label(frame, text="Theme:").pack(anchor='w', pady=(0, 5))
        self.theme_var = tk.StringVar()
        ttkbs.Combobox(
            frame,
            textvariable=self.theme_var,
            values=VALID_THEMES  # Use the valid themes list
        ).pack(fill='x', pady=(0, 10))


    def create_video_settings(self):
        """Create video settings frame."""
        frame = ttkbs.Frame(self.content)
        self.category_frames["Video"] = frame

        # Resolution settings
        ttkbs.Label(frame, text="Base Canvas Resolution:").pack(anchor='w', pady=(0, 5))
        self.base_resolution_var = tk.StringVar()
        ttkbs.Entry(
            frame,
            textvariable=self.base_resolution_var
        ).pack(fill='x', pady=(0, 10))

        # FPS settings
        ttkbs.Label(frame, text="FPS:").pack(anchor='w', pady=(0, 5))
        self.fps_var = tk.StringVar()
        ttkbs.Combobox(
            frame,
            textvariable=self.fps_var,
            values=["30", "60"]
        ).pack(fill='x', pady=(0, 10))

        # Video Input Device
        ttkbs.Label(frame, text="Video Input:").pack(anchor='w', pady=(0, 5))
        self.video_device_var = tk.StringVar()
        self.video_devices_combo = ttkbs.Combobox(
            frame,
            textvariable=self.video_device_var,
            values=self.get_video_devices()
        )
        self.video_devices_combo.pack(fill='x', pady=(0, 10))

        # Refresh devices button
        ttkbs.Button(
            frame,
            text="Refresh Devices",
            command=self.refresh_video_devices
        ).pack(fill='x', pady=(0, 10))

    def get_video_devices(self) -> List[str]:
        """Get list of available video input devices."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                capture_output=True,
                text=True
            )
            
            devices = []
            capture_video = False
            
            for line in result.stderr.split('\n'):
                if '[AVFoundation input device' in line and 'video devices' in line:
                    capture_video = True
                elif '[AVFoundation input device' in line and 'audio devices' in line:
                    capture_video = False
                elif capture_video and ']' in line:
                    # Extract device name and index
                    try:
                        index = line.split(']')[0].split('[')[1]
                        name = line.split(']')[1].strip()
                        devices.append(f"{index}: {name}")
                    except:
                        continue
            
            # Always add screen capture option
            devices.append("Screen Capture")
            return devices
        except Exception as e:
            print(f"Error getting video devices: {e}")
            return ["Screen Capture"]

    def refresh_video_devices(self):
        """Refresh the list of video devices."""
        devices = self.get_video_devices()
        self.video_devices_combo['values'] = devices
    def create_audio_settings(self):
        """Create audio settings frame."""
        frame = ttkbs.Frame(self.content)
        self.category_frames["Audio"] = frame

        # Desktop audio device
        ttkbs.Label(frame, text="Desktop Audio Device:").pack(anchor='w', pady=(0, 5))
        self.desktop_audio_var = tk.StringVar()
        ttkbs.Combobox(
            frame,
            textvariable=self.desktop_audio_var,
            values=self.get_audio_devices()
        ).pack(fill='x', pady=(0, 10))

        # Mic audio device
        ttkbs.Label(frame, text="Microphone:").pack(anchor='w', pady=(0, 5))
        self.mic_audio_var = tk.StringVar()
        ttkbs.Combobox(
            frame,
            textvariable=self.mic_audio_var,
            values=self.get_audio_devices()
        ).pack(fill='x', pady=(0, 10))

    def create_output_settings(self):
        """Create output settings frame."""
        frame = ttkbs.Frame(self.content)
        self.category_frames["Output"] = frame

        # Recording path
        ttkbs.Label(frame, text="Recording Path:").pack(anchor='w', pady=(0, 5))
        path_frame = ttkbs.Frame(frame)
        path_frame.pack(fill='x', pady=(0, 10))
        
        self.recording_path_var = tk.StringVar()
        ttkbs.Entry(
            path_frame,
            textvariable=self.recording_path_var
        ).pack(side='left', fill='x', expand=True)
        
        ttkbs.Button(
            path_frame,
            text="Browse",
            command=lambda: self.browse_path(self.recording_path_var)
        ).pack(side='right', padx=(5, 0))

        # Clip settings
        ttkbs.Label(frame, text="Clip Duration (seconds):").pack(anchor='w', pady=(0, 5))
        self.clip_duration_var = tk.StringVar()
        ttkbs.Entry(
            frame,
            textvariable=self.clip_duration_var
        ).pack(fill='x', pady=(0, 10))

        # File format
        ttkbs.Label(frame, text="Recording Format:").pack(anchor='w', pady=(0, 5))
        self.format_var = tk.StringVar()
        ttkbs.Combobox(
            frame,
            textvariable=self.format_var,
            values=ACCEPTABLE_FILE_EXTENSIONS
        ).pack(fill='x', pady=(0, 10))

    def create_hotkey_settings(self):
        """Create hotkey settings frame."""
        frame = ttkbs.Frame(self.content)
        self.category_frames["Hotkeys"] = frame

        # Start/Stop Recording
        ttkbs.Label(frame, text="Toggle Recording:").pack(anchor='w', pady=(0, 5))
        self.record_hotkey_var = tk.StringVar()
        ttkbs.Entry(
            frame,
            textvariable=self.record_hotkey_var
        ).pack(fill='x', pady=(0, 10))

        # Create Clip
        ttkbs.Label(frame, text="Create Clip:").pack(anchor='w', pady=(0, 5))
        self.clip_hotkey_var = tk.StringVar()
        ttkbs.Entry(
            frame,
            textvariable=self.clip_hotkey_var
        ).pack(fill='x', pady=(0, 10))

    def create_advanced_settings(self):
        """Create advanced settings frame."""
        frame = ttkbs.Frame(self.content)
        self.category_frames["Advanced"] = frame

        # Process priority
        ttkbs.Label(frame, text="Process Priority:").pack(anchor='w', pady=(0, 5))
        self.priority_var = tk.StringVar()
        ttkbs.Combobox(
            frame,
            textvariable=self.priority_var,
            values=["Normal", "High", "Above Normal"]
        ).pack(fill='x', pady=(0, 10))

        # Portable mode
        self.portable_mode_var = tk.BooleanVar()
        ttkbs.Checkbutton(
            frame,
            text="Enable Portable Mode",
            variable=self.portable_mode_var
        ).pack(anchor='w', pady=5)

    def create_bottom_buttons(self):
        """Create bottom button bar."""
        button_frame = ttkbs.Frame(self)  # Changed from self.window to self
        button_frame.pack(fill='x', padx=10, pady=10)

        ttkbs.Button(
            button_frame,
            text="Apply",
            command=self.apply_settings,
            bootstyle="primary"
        ).pack(side='right', padx=5)

        ttkbs.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,  # Changed from self.window.destroy
            bootstyle="secondary"
        ).pack(side='right', padx=5)
    def show_category(self, category):
        """Show selected category frame."""
        for frame in self.category_frames.values():
            frame.pack_forget()
        
        self.category_frames[category].pack(fill='both', expand=True)
    def save_config(self):
        """Save configuration to file."""
        try:
            new_config = self.config.get_default_config()
            
            # Update configuration sections
            new_config['general']['language'] = self.language_var.get()
            new_config['general']['theme'] = self.theme_var.get()
            
            # Save configuration
            if self.config.update(new_config):
                self.settings_changed = True
                return True
            
            return False
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Saving configuration")
            return False

    def get_audio_devices(self):
        """Get list of available audio devices."""
        # Implement audio device detection
        return ["Default", "System Audio", "Microphone"]

    def browse_path(self, var):
        """Open folder browser dialog."""
        path = filedialog.askdirectory()
        if path:
            var.set(path)

# src/ui/settings_window.py

    def load_current_settings(self):
        """Load current settings into UI."""
        # Load general settings
        self.language_var.set(self.config.get("general.language", "English"))
        self.theme_var.set(self.config.get("general.theme", "darkly"))
        
        # Load video settings
        self.base_resolution_var.set(self.config.get("video.base_resolution", "1920x1080"))
        self.fps_var.set(self.config.get("video.fps", "30"))
        
        # Load audio settings
        self.desktop_audio_var.set(self.config.get("audio.desktop_audio_device", "Default"))
        self.mic_audio_var.set(self.config.get("audio.mic_audio_device", "Default"))
        
        # Load output settings
        self.recording_path_var.set(self.config.get("recording.path", DEFAULT_SAVE_LOCATION))
        self.clip_duration_var.set(str(self.config.get("clipping.duration", DEFAULT_CLIP_DURATION)))
        self.format_var.set(self.config.get("recording.format", DEFAULT_FILE_EXTENSION))
        
        # Load hotkey settings
        self.record_hotkey_var.set(self.config.get("hotkeys.record", "Ctrl+R"))
        self.clip_hotkey_var.set(self.config.get("clipping.hotkey", "Ctrl+C"))
        
        # Load advanced settings
        self.priority_var.set(self.config.get("advanced.priority", "Normal"))
        self.portable_mode_var.set(self.config.get("advanced.portable_mode", False))

    def apply_settings(self):
        """Save and apply settings."""
        try:
            # Create new configuration dictionary
            new_config = {
                "general": {
                    "language": self.language_var.get(),
                    "theme": self.theme_var.get()
                },
                "video": {
                    "base_resolution": self.base_resolution_var.get(),
                    "fps": self.fps_var.get(),
                    "input_device": self.video_device_var.get()  # Save selected device
                },
                "audio": {
                    "desktop_audio_device": self.desktop_audio_var.get(),
                    "mic_audio_device": self.mic_audio_var.get()
                },
                "recording": {
                    "path": self.recording_path_var.get(),
                    "format": self.format_var.get()
                },
                "clipping": {
                    "duration": int(self.clip_duration_var.get()),
                    "hotkey": self.clip_hotkey_var.get()
                },
                "hotkeys": {
                    "record": self.record_hotkey_var.get()
                },
                "advanced": {
                    "priority": self.priority_var.get(),
                    "portable_mode": self.portable_mode_var.get()
                }
            }
            
            # Update configuration
            if self.config.update(new_config):
                messagebox.showinfo("Success", "Settings saved successfully!")
                self.destroy()
            else:
                raise Exception("Failed to save configuration")
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to save settings: {str(e)}"
            )