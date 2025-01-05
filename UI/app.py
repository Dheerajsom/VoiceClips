import tkinter as tk
from tkinter import Label, Button, Frame, Entry, OptionMenu, StringVar, Toplevel
from PIL import Image, ImageTk
from .recorder import ScreenRecorder
import threading

def update_video_frame(frame):
    """Update the GUI with new video frames."""
    global video_display_label
    image = Image.fromarray(frame)
    photo = ImageTk.PhotoImage(image)
    video_display_label.config(image=photo)
    video_display_label.image = photo

def load_image(path, max_size=(100, 100)):
    """Load an image from the path and resize it to max_size."""
    image = Image.open(path)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)  # Using ImageResampling.LANCZOS for better quality
    return ImageTk.PhotoImage(image)

recorder = None

def start_recording():
    global recorder, status_label, frame_rate_var, resolution_var
    if not recorder or not recorder.running:
        fps = float(frame_rate_var.get())
        resolution = tuple(map(int, resolution_var.get().split('x')))
        recorder = ScreenRecorder('test_video.mp4', fps, resolution, on_new_frame=update_video_frame)
        recorder.start_recording_thread(status_label)
    else:
        print("Recording is already in progress.")

def stop_recording():
    global recorder, status_label
    if recorder:
        recorder.stop_recording()
        status_label.config(text="Recording stopped. File saved as: "+ recorder.filename)
    else:
        status_label.config(text="No recording in progress.")

def run_app():
    global video_display_label, status_label, frame_rate_var, resolution_var
    root = tk.Tk()
    root.title("VoiceClips")
    root.geometry("1200x700")

    start_img = load_image('/Users/sreekarravavarapu/VoiceClips/start button.jpg')
    stop_img = load_image('/Users/sreekarravavarapu/VoiceClips/stop.jpg')

    frame_rate_var = StringVar(root, "60.0")
    resolution_var = StringVar(root, "1920x1080")
    resolution_options = {"1920x1080": "1920x1080", "1280x720": "1280x720", "640x480": "640x480"}

    control_frame = Frame(root)
    control_frame.pack(side=tk.BOTTOM, fill=tk.X)

    frame_rate_entry = OptionMenu(control_frame, frame_rate_var, "30.0", "60.0", "120.0")
    frame_rate_entry.pack(side=tk.LEFT, padx=10)

    resolution_menu = OptionMenu(control_frame, resolution_var, *resolution_options.keys())
    resolution_menu.pack(side=tk.LEFT, padx=10)

    start_btn = Button(control_frame, image=start_img, command=start_recording)
    start_btn.image = start_img
    start_btn.pack(side=tk.LEFT, padx=5)

    stop_btn = Button(control_frame, image=stop_img, command=stop_recording)
    stop_btn.image = stop_img
    stop_btn.pack(side=tk.LEFT, padx=5)
    
    status_label = Label(root, text="Status: Ready")
    status_label.pack(side=tk.BOTTOM, fill=tk.X)

    video_display_label = Label(root)
    video_display_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    root.mainloop()


