import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import subprocess
from PIL import Image, ImageTk
import mss
import time  # Import for timer
from recorder import video_capture_command
from constants import DEFAULT_FPS, ACCEPTABLE_FILE_EXTENSIONS
from utils import get_desktop_resolution, list_available_audio_devices

class ScreenRecorderApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Advanced Screen Recorder")
        self.recording_process = None
        self.screen_capture_active = False
        self.sources = []

        # Scene Manager
        self.scene_frame = tk.Frame(master, bg="#222")
        self.scene_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.add_source_button = tk.Button(self.scene_frame, text="Add Source", command=self.add_source)
        self.add_source_button.pack(pady=5)

        # Preview and Controls
        self.main_frame = tk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_frame = tk.Frame(self.main_frame, width=640, height=480)
        self.preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.video_canvas = tk.Label(self.preview_frame, bg="black")
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.preview_label = tk.Label(self.control_frame, text="Recording Controls", font=("Helvetica", 16))
        self.preview_label.pack(pady=10)

        default_width, default_height = get_desktop_resolution()
        self.res_label = tk.Label(self.control_frame, text="Resolution (WxH):")
        self.res_label.pack()
        self.resolution_entry = tk.Entry(self.control_frame)
        self.resolution_entry.insert(0, f"{default_width}x{default_height}")
        self.resolution_entry.pack(pady=5)

        self.fps_label = tk.Label(self.control_frame, text="Frames per Second (FPS):")
        self.fps_label.pack()
        self.fps_entry = tk.Entry(self.control_frame)
        self.fps_entry.insert(0, str(DEFAULT_FPS))
        self.fps_entry.pack(pady=5)

        self.format_label = tk.Label(self.control_frame, text="Save Format:")
        self.format_label.pack()
        self.format_var = tk.StringVar(value="mp4")
        self.format_menu = tk.OptionMenu(self.control_frame, self.format_var, *ACCEPTABLE_FILE_EXTENSIONS)
        self.format_menu.pack(pady=5)

        self.source_label = tk.Label(self.control_frame, text="Source Type (leave blank for full screen):")
        self.source_label.pack()
        self.source_entry = tk.Entry(self.control_frame)
        self.source_entry.insert(0, "")
        self.source_entry.pack(pady=5)

        self.audio_checkbox = tk.BooleanVar(value=True)
        self.audio_checkbutton = tk.Checkbutton(self.control_frame, text="Record Audio", variable=self.audio_checkbox)
        self.audio_checkbutton.pack(pady=5)

        self.start_button = tk.Button(self.control_frame, text="Start Recording", command=self.start_recording)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self.control_frame, text="Stop Recording", command=self.stop_recording, state="disabled")
        self.stop_button.pack(pady=5)

        self.transition_label = tk.Label(self.control_frame, text="Transition:")
        self.transition_label.pack()
        self.transition_var = tk.StringVar(value="fade")
        self.transition_menu = tk.OptionMenu(self.control_frame, self.transition_var, "fade", "cut", "slide")
        self.transition_menu.pack()

        # Timer Label for recording time
        self.record_timer_label = tk.Label(self.control_frame, text="Recording Time: 00:00", font=("Helvetica", 12))
        self.record_timer_label.pack(pady=5)

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
                img_resized = img.resize((640, 480))
                imgtk = ImageTk.PhotoImage(image=img_resized)
                self.video_canvas.imgtk = imgtk
                self.video_canvas.config(image=imgtk)
                self.master.after(100)

    def start_recording(self):
        resolution = self.resolution_entry.get()
        fps = int(self.fps_entry.get())
        width, height = map(int, resolution.split('x'))
        file_format = self.format_var.get()
        source_type = self.source_entry.get().strip().lower()
        record_audio = self.audio_checkbox.get()

        if not source_type:
            source_type = None

        file_type = filedialog.asksaveasfilename(defaultextension=f".{file_format}",
                                                 filetypes=[(ext.upper(), f"*.{ext}") for ext in ACCEPTABLE_FILE_EXTENSIONS])
        if not file_type:
            return

        self.screen_capture_active = True
        self.start_time = time.time()  # Timer starts here
        threading.Thread(target=self.show_preview, daemon=True).start()
        self.update_timer()  # Start updating the timer

        command = video_capture_command(fps, width, height, record_audio, file_type, source_type)
        print("FFmpeg Command:", " ".join(command))
        self.recording_process = subprocess.Popen(command)

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

    def update_timer(self):
        if self.screen_capture_active:
            elapsed_time = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed_time, 60)
            self.record_timer_label.config(text=f"Recording Time: {minutes:02}:{seconds:02}")
            self.master.after(1000, self.update_timer)

    def stop_recording(self):
        self.screen_capture_active = False
        if self.recording_process:
            self.recording_process.terminate()
            self.recording_process.wait()
        self.video_canvas.config(image="")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.record_timer_label.config(text="Recording Stopped")
        messagebox.showinfo("Recording Stopped", "Recording saved successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x600")
    app = ScreenRecorderApp(root)
    root.mainloop()
