import tkinter as tk
from tkinter import Label, Button, Frame, OptionMenu, StringVar, Scale, Checkbutton, BooleanVar, filedialog
from tkinter.ttk import Separator
from PIL import Image, ImageTk
from .recorder import ScreenRecorder
import threading
import psutil
from datetime import timedelta
from pynput import keyboard
from datetime import datetime
import time
import cv2
import os

# Create recordings directory (absolute path)
RECORDINGS_DIR = os.path.join(os.path.abspath(os.getcwd()), 'recordings')
os.makedirs(RECORDINGS_DIR, exist_ok=True)

scenes = {}
sources = {}
current_scene = None

# Initialize performance stats variables
frames_count = 0
last_frame_time = time.time()

def resize_frame_to_fit(frame, max_width, max_height):
    height, width = frame.shape[:2]
    ratio = min(max_width/width, max_height/height)
    new_size = (int(width * ratio), int(height * ratio))
    return cv2.resize(frame, new_size)

def update_video_frame(frame):
    global video_display_label
    display_width = video_frame.winfo_width()
    display_height = video_frame.winfo_height()
    resized_frame = resize_frame_to_fit(frame, display_width, display_height)
    image = Image.fromarray(resized_frame)
    photo = ImageTk.PhotoImage(image)
    video_display_label.config(image=photo)
    video_display_label.image = photo

def start_timer():
    global seconds
    seconds = 0
    update_timer()

def update_timer():
    global seconds, timer_label
    if recorder and recorder.running:
        seconds += 1
        timer_label.config(text=f"Duration: {str(timedelta(seconds=seconds))}")
        timer_label.after(1000, update_timer)

def update_stats():
    global fps_label, last_frame_time, frames_count
    if recorder and recorder.running:
        current_time = time.time()
        frames_count += 1
        if current_time - last_frame_time >= 1:
            actual_fps = frames_count / (current_time - last_frame_time)
            frames_count = 0
            last_frame_time = current_time
        cpu_usage = psutil.cpu_percent()
        fps_label.config(text=f"FPS: {actual_fps:.1f} | CPU: {cpu_usage}%")
        fps_label.after(1000, update_stats)

def start_recording():
    global recorder, status_label
    if not recorder or not recorder.running:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(RECORDINGS_DIR, f"recording_{current_time}.mp4")
        
        fps = float(frame_rate_var.get())
        resolution = tuple(map(int, resolution_var.get().split('x')))
        recorder = ScreenRecorder(filename, fps, resolution)
        
        recording_thread = threading.Thread(
            target=recorder.start_recording,
            args=(update_video_frame,),
            daemon=True
        )
        recording_thread.start()
        status_label.config(text="Status: Recording...")
        start_timer()

def stop_recording():
    global recorder, status_label
    if recorder and recorder.running:
        # Open save file dialog for the user to choose the save location
        save_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("MKV files", "*.mkv"), ("MOV files", "*.mov")],
            title="Save Recording As"
        )

        if save_path:
            recorder.filename = save_path  # Set the filename to the selected path
            recorder.stop_recording()  # Stop and save the recording
            status_label.config(text=f"Status: Stopped Recording. Saved at: {save_path}")
        else:
            status_label.config(text="Status: Recording stopped without saving.")

        timer_label.config(text="Duration: 00:00:00")

def bind_hotkeys():
    def on_activate_start():
        start_recording()

    def on_activate_stop():
        stop_recording()

    hotkeys = keyboard.GlobalHotKeys({
        '<ctrl>+<shift>+r': on_activate_start,
        '<ctrl>+<shift>+s': on_activate_stop,
    })
    hotkeys.start()

def run_app():
    global video_display_label, status_label, frame_rate_var, resolution_var, timer_label, fps_label, video_frame, recorder, seconds, desktop_audio_var, mic_audio_var
    root = tk.Tk()
    root.title("VoiceClips")
    root.geometry("1600x900")
    root.configure(bg="#2E2E2E")

    # Configure weights for layout
    root.grid_rowconfigure(0, weight=1, minsize=450)  # Video frame row
    root.grid_rowconfigure(1, weight=1, minsize=250)  # Control panel row
    root.grid_columnconfigure(0, weight=1)

    recorder = None
    seconds = 0

    frame_rate_var = StringVar(root, "30.0")
    resolution_var = StringVar(root, "1280x720")
    resolution_options = ["1920x1080", "1280x720", "640x480"]

    # Video Display Frame
    video_frame = Frame(root, bg="black")
    video_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    video_display_label = Label(video_frame, bg="black")
    video_display_label.pack(fill=tk.BOTH, expand=True)

    # Control Panel Frame
    control_frame = Frame(root, bg="#404040")
    control_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    # === Performance Stats (FPS/CPU and Timer) ===
    Label(control_frame, text="Performance Stats:", bg="#404040", fg="white").grid(row=0, column=0, columnspan=4, padx=5, pady=5)
    fps_label = Label(control_frame, text="FPS: 0 | CPU: 0%", bg="#404040", fg="white")
    fps_label.grid(row=1, column=0, padx=5)

    timer_label = Label(control_frame, text="Duration: 00:00:00", bg="#404040", fg="white")
    timer_label.grid(row=1, column=1, padx=5)

    # === Recording Controls ===
    Label(control_frame, text="Recording Controls:", bg="#404040", fg="white").grid(row=2, column=0, columnspan=4, padx=5, pady=5)
    record_btn = Button(control_frame, text="Start Recording", command=start_recording, bg="green", fg="white")
    record_btn.grid(row=3, column=0, padx=5, pady=5)

    stop_btn = Button(control_frame, text="Stop Recording", command=stop_recording, bg="red", fg="white")
    stop_btn.grid(row=3, column=1, padx=5, pady=5)

    # === Stream Settings ===
    Label(control_frame, text="Streaming Platform:", bg="#404040", fg="white").grid(row=8, column=0, padx=5)
    stream_options = ["YouTube", "Twitch", "Facebook Live", "Custom RTMP"]
    stream_var = StringVar(root, value="Select Platform")
    OptionMenu(control_frame, stream_var, *stream_options).grid(row=8, column=1)

    Button(control_frame, text="Start Stream", command=lambda: print(f"Start Stream on {stream_var.get()}")).grid(row=8, column=2)
    Button(control_frame, text="Stop Stream", command=lambda: print("Stop Stream")).grid(row=8, column=3)

    # === Status Bar ===
    status_label = Label(control_frame, text="Status: Ready", bg="#2E2E2E", fg="white", anchor="w")
    status_label.grid(row=9, column=0, columnspan=4, padx=10, pady=5, sticky="ew")

    root.after(1000, update_stats)
    bind_hotkeys()
    root.mainloop()
