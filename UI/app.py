import tkinter as tk
from tkinter import Label, Button, Frame, OptionMenu, StringVar
from PIL import Image, ImageTk
from .recorder import ScreenRecorder
import threading
import psutil
from datetime import timedelta
from pynput import keyboard
from datetime import datetime
import cv2
import os
import sys

# Create recordings directory (absolute path)
RECORDINGS_DIR = os.path.join(os.path.abspath(os.getcwd()), 'recordings')
os.makedirs(RECORDINGS_DIR, exist_ok=True)

scenes = {}
sources = {}
current_scene = None

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
    global fps_label
    if recorder and recorder.running:
        fps = frame_rate_var.get()
        cpu_usage = psutil.cpu_percent()
        fps_label.config(text=f"FPS: {fps} | CPU: {cpu_usage}%")
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
        recorder.running = False  # Signal the recording thread to stop
        recorder.stop_recording()
        status_label.config(text=f"Recording stopped. Saved at: {recorder.filename}")
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
    global video_display_label, status_label, frame_rate_var, resolution_var, timer_label, fps_label, video_frame, recorder, seconds
    root = tk.Tk()
    root.title("VoiceClips")
    root.geometry("1920x1080")
    root.configure(bg="#2E2E2E")

    recorder = None
    seconds = 0

    frame_rate_var = StringVar(root, "30.0")
    resolution_var = StringVar(root, "1920x1080")
    resolution_options = {"1920x1080": "1920x1080", "1280x720": "1280x720", "640x480": "640x480"}

    main_frame = Frame(root, bg="#2E2E2E")
    main_frame.pack(fill=tk.BOTH, expand=True)

    video_frame = Frame(main_frame, bg="black")
    video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    video_display_label = Label(video_frame, bg="black")
    video_display_label.pack(fill=tk.BOTH, expand=True)

    control_frame = Frame(main_frame, bg="#404040")
    control_frame.pack(fill=tk.X, padx=10, pady=5)

    left_controls = Frame(control_frame, bg="#404040")
    left_controls.pack(side=tk.LEFT, fill=tk.Y, padx=5)

    fps_label = Label(left_controls, text="FPS: 0 | CPU: 0%", bg="#404040", fg="white")
    fps_label.pack(side=tk.LEFT, padx=5)

    timer_label = Label(left_controls, text="Duration: 00:00:00", bg="#404040", fg="white")
    timer_label.pack(side=tk.LEFT, padx=5)

    center_controls = Frame(control_frame, bg="#404040")
    center_controls.pack(side=tk.LEFT, fill=tk.Y, expand=True)

    frame_rate_entry = OptionMenu(center_controls, frame_rate_var, "30.0", "60.0")
    frame_rate_entry.config(bg="#505050", fg="white")
    frame_rate_entry.pack(side=tk.LEFT, padx=5)

    resolution_menu = OptionMenu(center_controls, resolution_var, *resolution_options.keys())
    resolution_menu.config(bg="#505050", fg="white")
    resolution_menu.pack(side=tk.LEFT, padx=5)

    right_controls = Frame(control_frame, bg="#404040")
    right_controls.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

    stop_btn = Button(right_controls, text="Stop Recording", command=stop_recording, bg="red", fg="white")
    stop_btn.pack(side=tk.RIGHT, padx=5)

    record_btn = Button(right_controls, text="Start Recording", command=start_recording, bg="green", fg="white")
    record_btn.pack(side=tk.RIGHT, padx=5)

    status_label = Label(main_frame, text="Status: Ready", anchor="w", bg="#2E2E2E", fg="white")
    status_label.pack(fill=tk.X, padx=10, pady=5)

    root.after(1000, update_stats)
    bind_hotkeys()
    root.mainloop()
