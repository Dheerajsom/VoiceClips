import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import subprocess
from PIL import Image, ImageTk
import mss
import time
import wave
import pyaudio
from collections import deque
from recorder import video_capture_command
from constants import DEFAULT_FPS, ACCEPTABLE_FILE_EXTENSIONS, BASE_CANVAS_RESOLUTION, OUTPUT_SCALED_RESOLUTION, VIDEO_FILTERS
from utils import get_desktop_resolution, list_available_audio_devices, check_ffmpeg
import settings_window
from clipper import Clipper
import os
import ttkbootstrap as ttkbs
from audio_mixer import set_mic_volume, set_system_volume
import io
from PIL import Image
from pynput import keyboard
import re


class ScreenRecorderApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Advanced Screen Recorder with Voice Commands")
        self.master.geometry("1280x720")

        # Check FFmpeg installation
        if not check_ffmpeg():
            messagebox.showerror("Error", "FFmpeg is not installed. Please install FFmpeg to use this application.")
            self.master.destroy()
            return

        self.recording_process = None
        self.screen_capture_active = False
        self.sources = []
        self.scenes = []
        self.audio_devices = list_available_audio_devices() if list_available_audio_devices() else ["No devices found"]
        
        # Initialize buffers for clipping
        self.frame_buffer = deque(maxlen=30 * 30)  # 30 seconds at 30 fps
        self.audio_buffer = deque(maxlen=30 * 44100 * 2)  # 30 seconds of stereo audio at 44.1kHz
        
        self.settings = {
            "General": {"language": "English", "theme": "Dark"},
            "Stream": {"stream_key": "", "platform": "YouTube"},
            "Output": {
                "recording_path": "",
                "output_format": "MP4",
                "save_location": os.path.expanduser("~/Documents"),
                "clip_format": "mp4"
                "clip_duration" "30",  # Add this
                "clip_hotkey": "Ctrl+C"  # Add this
            },
            "Audio": {
                "desktop_audio_device": "Default",
                "mic_audio_device": "Default"
            },
            "Video": {
                "canvas_resolution": "1920x1080",
                "output_resolution": "1280x720",
                "fps": "30"
            },
            "Hotkeys": {"recording_hotkey": "Ctrl+R"},
            "Advanced": {"priority": "Normal", "portable_mode": False}
        }

        # Initialize clipper with buffers
        self.clipper = Clipper()
        self.clipper.set_buffers(self.frame_buffer, self.audio_buffer)
        
        self.current_filename = ""
        self.create_layout()

        # Initialize audio components
        self.init_audio()

        self.hotkey_listener = None
        self.setup_hotkey_listener()

    def init_audio(self):
        """Initialize audio components"""
        self.audio = pyaudio.PyAudio()
        self.audio_stream = None
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100

    def create_layout(self):
        """Sets up the application layout."""
        # Split screen layout
        self.main_frame = ttkbs.Frame(self.master, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttkbs.Frame(self.main_frame, width=640, height=720)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.right_frame = ttkbs.Frame(self.main_frame, width=640, height=720)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: Video preview
        self.preview_label = ttkbs.Label(self.left_frame, text="Preview", font=("Helvetica", 16, "bold"), anchor="center")
        self.preview_label.pack(pady=10)

        self.preview_frame = ttkbs.Frame(self.left_frame, bootstyle="primary")
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        self.video_canvas = ttkbs.Label(self.preview_frame, bootstyle="secondary", anchor="center")
        self.video_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right: Controls
        self.control_label = ttkbs.Label(self.right_frame, text="Recording Controls", font=("Helvetica", 16, "bold"), anchor="w")
        self.control_label.pack(pady=10)

        control_frame = ttkbs.Frame(self.right_frame)
        control_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Resolution Input
        self.res_label = ttkbs.Label(control_frame, text="Resolution (WxH):")
        self.res_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.resolution_entry = ttkbs.Entry(control_frame, bootstyle="info")
        default_width, default_height = get_desktop_resolution()
        self.resolution_entry.insert(0, f"{default_width}x{default_height}")
        self.resolution_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # FPS Input
        self.fps_label = ttkbs.Label(control_frame, text="FPS:")
        self.fps_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.fps_entry = ttkbs.Entry(control_frame, bootstyle="info")
        self.fps_entry.insert(0, str(DEFAULT_FPS))
        self.fps_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Save Format Dropdown
        self.format_label = ttkbs.Label(control_frame, text="Save Format:")
        self.format_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.format_var = tk.StringVar(value="mp4")
        self.format_menu = ttkbs.Combobox(control_frame, textvariable=self.format_var, values=ACCEPTABLE_FILE_EXTENSIONS, bootstyle="info")
        self.format_menu.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Filename Input
        self.filename_label = ttkbs.Label(control_frame, text="Filename:")
        self.filename_label.grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.filename_entry = ttkbs.Entry(control_frame, bootstyle="info")
        self.filename_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Audio Mixer Sliders
        self.mic_volume_label = ttkbs.Label(control_frame, text="Mic Volume:")
        self.mic_volume_label.grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.mic_volume_slider = ttkbs.Scale(control_frame, from_=0, to=100, orient="horizontal", command=self.adjust_mic_volume, bootstyle="info")
        self.mic_volume_slider.set(50)
        self.mic_volume_slider.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        self.system_volume_label = ttkbs.Label(control_frame, text="System Volume:")
        self.system_volume_label.grid(row=5, column=0, padx=10, pady=5, sticky="e")
        self.system_volume_slider = ttkbs.Scale(control_frame, from_=0, to=100, orient="horizontal", command=self.adjust_system_volume, bootstyle="info")
        self.system_volume_slider.set(50)
        self.system_volume_slider.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        # Control Buttons
        self.start_button = ttkbs.Button(control_frame, text="Start Recording", command=self.start_recording, bootstyle="success")
        self.start_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")

        self.stop_button = ttkbs.Button(control_frame, text="Stop Recording", command=self.stop_recording, state="disabled", bootstyle="danger")
        self.stop_button.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        self.settings_button = ttkbs.Button(control_frame, text="Open Settings", command=self.open_settings, bootstyle="secondary")
        self.settings_button.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # Status Labels
        self.record_timer_label = ttkbs.Label(control_frame, text="Recording Time: 00:00", font=("Helvetica", 12))
        self.record_timer_label.grid(row=8, column=0, columnspan=2, pady=5, sticky="ew")

        self.clip_status_label = ttkbs.Label(control_frame, text="Voice Command: Ready", font=("Helvetica", 12))
        self.clip_status_label.grid(row=9, column=0, columnspan=2, pady=5, sticky="ew")

    def setup_hotkey_listener(self):
        """Setup keyboard listener for clip hotkey"""
        if self.hotkey_listener:
            self.hotkey_listener.stop()

        def on_press(key):
            try:
                # Get current hotkey setting
                hotkey = self.settings["Output"]["clip_hotkey"]
                # Parse hotkey string (e.g., "Ctrl+C")
                modifiers, main_key = self.parse_hotkey(hotkey)
                
                # Check if the pressed key matches the hotkey
                if self.is_hotkey_pressed(key, modifiers, main_key):
                    if self.screen_capture_active:  # Only clip if recording
                        print(f"Clip hotkey pressed: {hotkey}")
                        self.clipper.save_clip()
            except Exception as e:
                print(f"Hotkey error: {e}")

        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.start()

    def parse_hotkey(self, hotkey_str):
        """Parse hotkey string into modifiers and main key"""
        parts = hotkey_str.split('+')
        main_key = parts[-1].strip().lower()
        modifiers = [mod.strip().lower() for mod in parts[:-1]]
        return modifiers, main_key

    def is_hotkey_pressed(self, key, modifiers, main_key):
        """Check if the pressed key matches the hotkey combination"""
        try:
            # Get the key character
            if hasattr(key, 'char'):
                key_char = key.char.lower()
            else:
                key_char = key.name.lower()

            # Check if the main key matches
            if key_char != main_key:
                return False

            # Check modifiers
            ctrl_pressed = keyboard.Controller().pressed(keyboard.Key.ctrl)
            shift_pressed = keyboard.Controller().pressed(keyboard.Key.shift)
            alt_pressed = keyboard.Controller().pressed(keyboard.Key.alt)

            # Verify all required modifiers are pressed
            return (('ctrl' in modifiers) == ctrl_pressed and
                   ('shift' in modifiers) == shift_pressed and
                   ('alt' in modifiers) == alt_pressed)
        except Exception as e:
            print(f"Error checking hotkey: {e}")
            return False


    def adjust_mic_volume(self, volume):
        """Adjust microphone volume."""
        set_mic_volume(int(float(volume)))

    def adjust_system_volume(self, volume):
        """Adjust system volume."""
        set_system_volume(int(float(volume)))

    def open_settings(self):
        settings_window.open_settings_window(self.master, self.apply_settings)

    def apply_settings(self, new_settings):
        """Apply new settings including clip duration and hotkey"""
        self.settings.update(new_settings)
        
        # Update UI elements
        self.resolution_entry.delete(0, tk.END)
        self.resolution_entry.insert(0, self.settings["Video"]["canvas_resolution"])
        self.fps_entry.delete(0, tk.END)
        self.fps_entry.insert(0, self.settings["Video"]["fps"])
        self.format_var.set(self.settings["Output"]["output_format"])
        
        # Update clipper settings
        save_location = self.settings["Output"]["save_location"]
        os.makedirs(save_location, exist_ok=True)
        self.clipper.set_save_location(save_location)
        self.clipper.set_file_format(self.settings["Output"]["clip_format"])
        
        # Update clip duration
        try:
            clip_duration = int(self.settings["Output"]["clip_duration"])
            self.clipper.set_buffer_duration(clip_duration)
        except ValueError:
            print("Invalid clip duration, using default (30 seconds)")
            self.clipper.set_buffer_duration(30)
        
        # Update hotkey listener
        self.setup_hotkey_listener()
        
        print(f"Settings applied: Save location: {save_location}, "
              f"Format: {self.settings['Output']['clip_format']}, "
              f"Duration: {self.settings['Output']['clip_duration']}s, "
              f"Hotkey: {self.settings['Output']['clip_hotkey']}")

    def __del__(self):
        """Cleanup on application close"""
        if hasattr(self, 'audio'):
            self.audio.terminate()
        if hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()  
    def start_recording(self):
        resolution = self.resolution_entry.get().strip()
        if not resolution:
            messagebox.showerror("Error", "Resolution cannot be empty.")
            return
            
        try:
            fps = int(self.fps_entry.get())
            width, height = map(int, resolution.split('x'))
        except ValueError:
            messagebox.showerror("Error", "Invalid resolution or FPS format.")
            return

        file_format = self.format_var.get()
        filename = self.filename_entry.get().strip()

        if not filename:
            messagebox.showerror("Error", "Please specify a filename.")
            return

        # Use settings for save location
        save_location = self.settings["Output"]["save_location"]
        os.makedirs(save_location, exist_ok=True)
        
        output_path = os.path.join(save_location, f"{filename}.{file_format}")
        self.current_filename = output_path

        # Clear buffers
        self.frame_buffer.clear()
        self.audio_buffer.clear()

        self.screen_capture_active = True
        self.start_time = time.time()

        # Start capture threads
        threading.Thread(target=self.capture_frames, daemon=True).start()
        threading.Thread(target=self.capture_audio, daemon=True).start()
        self.update_timer()

        # Start voice detection only when recording starts
        self.clipper.start_listening()
        print("Voice detection started")

        command = video_capture_command(fps, width, height, True, output_path)
        self.recording_process = subprocess.Popen(command)

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.clip_status_label.config(text="Voice Command: Active - Say 'clip' to save last 30 seconds")

    def capture_frames(self):
        """Capture and buffer frames"""
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            while self.screen_capture_active:
                try:
                    frame = sct.grab(monitor)
                    frame_bytes = frame.rgb
                    self.frame_buffer.append(frame_bytes)
                    
                    # Update preview
                    img = Image.frombytes("RGB", frame.size, frame.rgb)
                    img_resized = img.resize((640, 360))
                    imgtk = ImageTk.PhotoImage(image=img_resized)
                    self.video_canvas.imgtk = imgtk
                    self.video_canvas.config(image=imgtk)
                    
                except Exception as e:
                    print(f"Frame capture error: {e}")
                
                time.sleep(1/30)

    def capture_audio(self):
        """Capture and buffer audio"""
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            while self.screen_capture_active:
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    self.audio_buffer.append(data)
                except Exception as e:
                    print(f"Audio capture error: {e}")
                    
        except Exception as e:
            print(f"Audio stream error: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()

    def stop_recording(self):
        self.screen_capture_active = False
        
        # Stop voice detection
        self.clipper.stop_listening()
        print("Voice detection stopped")
        
        if self.recording_process:
            self.recording_process.terminate()
            self.recording_process.wait()
            
        self.video_canvas.config(image="")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.filename_entry.delete(0, tk.END)
        self.clip_status_label.config(text="Voice Command: Ready")
        
        if os.path.exists(self.current_filename):
            messagebox.showinfo("Recording Stopped", 
                              f"Recording saved successfully to {self.current_filename}.")
        else:
            messagebox.showerror("Error", 
                               "There was an error saving the recording.")
            
        self.current_filename = ""

    def update_timer(self):
        if self.screen_capture_active:
            elapsed_time = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed_time, 60)
            self.record_timer_label.config(
                text=f"Recording Time: {minutes:02}:{seconds:02}")
            self.master.after(1000, self.update_timer)

    def __del__(self):
        """Cleanup on application close"""
        if hasattr(self, 'audio'):
            self.audio.terminate()

if __name__ == "__main__":
    root = ttkbs.Window(themename="darkly")
    app = ScreenRecorderApp(root)
    root.mainloop()