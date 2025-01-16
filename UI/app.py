# app.py - Enhanced Screen Recorder with Full Features and Additions

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import subprocess
from PIL import Image, ImageTk
import mss
import time
from recorder import video_capture_command
from constants import DEFAULT_FPS, ACCEPTABLE_FILE_EXTENSIONS, BASE_CANVAS_RESOLUTION, OUTPUT_SCALED_RESOLUTION, VIDEO_FILTERS
from utils import get_desktop_resolution, list_available_audio_devices
import settings_window
from clipper import Clipper
import os

class ScreenRecorderApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Advanced Screen Recorder with Full Features")
        self.recording_process = None
        self.screen_capture_active = False
        self.sources = []
        self.scenes = []  # Added for scene management
        self.audio_devices = list_available_audio_devices() if list_available_audio_devices() else ["No devices found"]
        self.settings = {
            "General": {"language": "English", "theme": "Dark"},
            "Stream": {"stream_key": "", "platform": "YouTube"},
            "Output": {"recording_path": "", "output_format": "MP4", "save_location": os.path.expanduser("~/Documents"), "clip_format": "mp4"},
            "Audio": {"desktop_audio_device": "Default", "mic_audio_device": "Default"},
            "Video": {"canvas_resolution": "1920x1080", "output_resolution": "1280x720", "fps": "30"},
            "Hotkeys": {"recording_hotkey": "Ctrl+R"},
            "Advanced": {"priority": "Normal", "portable_mode": False}
        }

        self.clipper = Clipper()
        self.clipper.start_listening()

        # UI Layout with Preview and Control sections
        self.top_half_frame = tk.Frame(master)
        self.top_half_frame.pack(fill=tk.BOTH, expand=True)

        self.bottom_half_frame = tk.Frame(master, bg="#2c2f33")
        self.bottom_half_frame.pack(fill=tk.BOTH, expand=False)

        self.preview_label = tk.Label(self.top_half_frame, text="Preview", font=("Helvetica", 16), bg="#444", fg="#fff")
        self.preview_label.pack(fill=tk.X, pady=5)

        self.preview_frame = tk.Frame(self.top_half_frame, bg="black", height=360)
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        self.video_canvas = tk.Label(self.preview_frame, bg="black")
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        self.control_label = tk.Label(self.bottom_half_frame, text="Recording Controls", font=("Helvetica", 16), bg="#333", fg="#fff")
        self.control_label.grid(row=0, column=0, columnspan=4, pady=10, sticky="nsew")
        for i in range(4):
            self.bottom_half_frame.columnconfigure(i, weight=1)

        # Resolution and FPS
        self.res_label = tk.Label(self.bottom_half_frame, text="Resolution (WxH):", bg="#2c2f33", fg="#fff")
        self.res_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.resolution_entry = tk.Entry(self.bottom_half_frame)
        default_width, default_height = get_desktop_resolution()
        self.resolution_entry.insert(0, f"{default_width}x{default_height}")
        self.resolution_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.fps_label = tk.Label(self.bottom_half_frame, text="FPS:", bg="#2c2f33", fg="#fff")
        self.fps_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.fps_entry = tk.Entry(self.bottom_half_frame)
        self.fps_entry.insert(0, str(DEFAULT_FPS))
        self.fps_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Save Format
        self.format_label = tk.Label(self.bottom_half_frame, text="Save Format:", bg="#2c2f33", fg="#fff")
        self.format_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.format_var = tk.StringVar(value="mp4")
        self.format_menu = tk.OptionMenu(self.bottom_half_frame, self.format_var, *ACCEPTABLE_FILE_EXTENSIONS)
        self.format_menu.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Audio Controls
        self.audio_checkbutton = tk.Checkbutton(self.bottom_half_frame, text="Record Audio", bg="#2c2f33", fg="#fff", variable=tk.BooleanVar(value=True))
        self.audio_checkbutton.grid(row=4, column=0, columnspan=3, pady=5, sticky="w")

        self.audio_device_label = tk.Label(self.bottom_half_frame, text="Select Audio Device:", bg="#2c2f33", fg="#fff")
        self.audio_device_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.audio_device_var = tk.StringVar(value=self.audio_devices[0] if self.audio_devices else "None")
        self.audio_device_menu = tk.OptionMenu(self.bottom_half_frame, self.audio_device_var, *self.audio_devices)
        self.audio_device_menu.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        # Transitions and Hotkeys
        self.transition_label = tk.Label(self.bottom_half_frame, text="Transition:", bg="#2c2f33", fg="#fff")
        self.transition_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.transition_var = tk.StringVar(value="fade")
        self.transition_menu = tk.OptionMenu(self.bottom_half_frame, self.transition_var, "fade", "cut", "slide", "stinger")
        self.transition_menu.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

        self.hotkey_label = tk.Label(self.bottom_half_frame, text="Hotkey (Switch Scene):", bg="#2c2f33", fg="#fff")
        self.hotkey_label.grid(row=7, column=0, padx=10, pady=5, sticky="w")
        self.hotkey_entry = tk.Entry(self.bottom_half_frame)
        self.hotkey_entry.grid(row=7, column=1, padx=10, pady=5, sticky="ew")

        # Replay Buffer
        self.replay_buffer_label = tk.Label(self.bottom_half_frame, text="Replay Buffer (Seconds):", bg="#2c2f33", fg="#fff")
        self.replay_buffer_label.grid(row=8, column=0, padx=10, pady=5, sticky="w")
        self.replay_buffer_entry = tk.Entry(self.bottom_half_frame)
        self.replay_buffer_entry.insert(0, "10")
        self.replay_buffer_entry.grid(row=8, column=1, padx=10, pady=5, sticky="ew")

        # Control Buttons
        self.start_button = tk.Button(self.bottom_half_frame, text="Start Recording", command=self.start_recording, bg="#0f0", fg="#000")
        self.start_button.grid(row=9, column=0, padx=10, pady=10, sticky="ew")

        self.stop_button = tk.Button(self.bottom_half_frame, text="Stop Recording", command=self.stop_recording, state="disabled", bg="#f00", fg="#fff")
        self.stop_button.grid(row=9, column=1, padx=10, pady=10, sticky="ew")

        self.settings_button = tk.Button(self.bottom_half_frame, text="Open Settings", command=self.open_settings, bg="#555", fg="#fff")
        self.settings_button.grid(row=10, column=2, padx=10, pady=10, sticky="ew")

        self.record_timer_label = tk.Label(self.bottom_half_frame, text="Recording Time: 00:00", font=("Helvetica", 12), bg="#2c2f33", fg="#fff")
        self.record_timer_label.grid(row=11, column=0, columnspan=3, pady=5, sticky="ew")

        # Scene and Source Buttons
        self.add_scene_button = tk.Button(self.bottom_half_frame, text="Add Scene", command=self.add_scene, bg="#444", fg="#fff")
        self.add_scene_button.grid(row=12, column=0, padx=10, pady=5)
        self.add_source_button = tk.Button(self.bottom_half_frame, text="Add Source", command=self.add_source, bg="#444", fg="#fff")
        self.add_source_button.grid(row=12, column=1, padx=10, pady=5)

    def open_settings(self):
        settings_window.open_settings_window(self.master, self.apply_settings)

    def apply_settings(self, new_settings):
        self.settings.update(new_settings)
        self.resolution_entry.delete(0, tk.END)
        self.resolution_entry.insert(0, self.settings["Video"]["canvas_resolution"])
        self.fps_entry.delete(0, tk.END)
        self.fps_entry.insert(0, self.settings["Video"]["fps"])
        self.format_var.set(self.settings["Output"]["output_format"])
        save_location = new_settings["Output"]["save_location"]
        clip_format = new_settings["Output"]["clip_format"]
        self.clipper.set_save_location(save_location)
        self.clipper.set_file_format(clip_format)

    def add_scene(self):
        scene_name = tk.simpledialog.askstring("New Scene", "Enter Scene Name:")
        if scene_name:
            self.scenes.append(scene_name)
            messagebox.showinfo("Scene Added", f"Scene '{scene_name}' added.")

    def add_source(self):
        source_type = tk.simpledialog.askstring("Source Type", "Enter source type (image/window/capture):")
        if source_type:
            source_path = filedialog.askopenfilename() if source_type == "image" else None
            self.sources.append({"type": source_type, "path": source_path})
            messagebox.showinfo("Source Added", f"Added {source_type} source.")

    def show_preview(self):
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            while self.screen_capture_active:
                frame = sct.grab(monitor)
                img = Image.frombytes("RGB", frame.size, frame.rgb)
                img_resized = img.resize((1280, 360))
                imgtk = ImageTk.PhotoImage(image=img_resized)
                self.video_canvas.imgtk = imgtk
                self.video_canvas.config(image=imgtk)
                self.master.after(100)

    def start_recording(self):
        resolution = self.resolution_entry.get()
        fps = int(self.fps_entry.get())
        width, height = map(int, resolution.split('x'))
        file_format = self.format_var.get()
        record_audio = self.audio_checkbutton.cget('text') == "Record Audio"

        file_type = filedialog.asksaveasfilename(defaultextension=f".{file_format}",
                                                 filetypes=[(ext.upper(), f"*.{ext}") for ext in ACCEPTABLE_FILE_EXTENSIONS])
        if not file_type:
            return

        self.screen_capture_active = True
        self.start_time = time.time()
        threading.Thread(target=self.show_preview, daemon=True).start()
        self.update_timer()

        command = video_capture_command(fps, width, height, record_audio, file_type)
        self.recording_process = subprocess.Popen(command)

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

    def update_timer(self):
        if self.screen_capture_active:
            elapsed_time = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed_time, 60)
            self.master.after(1000, self.update_timer)
            self.record_timer_label.config(text=f"Recording Time: {minutes:02}:{seconds:02}")

    def stop_recording(self):
        self.screen_capture_active = False
        if self.recording_process:
            self.recording_process.terminate()
            self.recording_process.wait()
        self.video_canvas.config(image="")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        messagebox.showinfo("Recording Stopped", "Recording saved successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1280x720")
    app = ScreenRecorderApp(root)
    root.mainloop()
