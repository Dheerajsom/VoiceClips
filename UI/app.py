import tkinter as tk
from tkinter import Label, Button, Frame, Entry, OptionMenu, StringVar, Toplevel, messagebox  # added messagebox for alerts
from PIL import Image, ImageTk
from .recorder import ScreenRecorder
import threading
import psutil  # added for system stats display
from datetime import timedelta  # added for recording timer
from pynput import keyboard   # added for hotkey support


# added scene management
scenes = {}  # Store scenes with their respective sources
sources = {}  # Store available sources for scenes
current_scene = None  # Track the currently selected scene


def add_source(source_type):
    """Add a new source (e.g., webcam, image, display capture) to the current scene."""
    global sources, current_scene
    if current_scene:
        source_name = f"{source_type} {len(sources) + 1}"
        sources[source_name] = source_type
        scenes[current_scene].append(source_name)
        messagebox.showinfo("Info", f"Added {source_name} to {current_scene}")

def add_scene():
    """Add a new scene."""
    global scenes, current_scene
    scene_name = f"Scene {len(scenes) + 1}"
    scenes[scene_name] = []
    scene_var.set(scene_name)
    update_scene_list()

def update_scene_list():
    """Update the scene dropdown menu."""
    scene_menu["menu"].delete(0, "end")
    for scene_name in scenes.keys():
        scene_menu["menu"].add_command(label=scene_name, command=lambda value=scene_name: switch_scene(value))

def switch_scene(scene_name):
    """Switch to the selected scene."""
    global current_scene
    current_scene = scene_name
    status_label.config(text=f"Scene: {scene_name}")

def add_transition_effect(effect_type):
    """Apply transitions between scenes."""
    status_label.config(text=f"Transition: {effect_type}")

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
seconds = 0  # added for timer

def start_timer():  # added for timer
    global seconds
    seconds = 0
    update_timer()

def update_timer():  # added for timer updates
    global seconds, timer_label
    if recorder and recorder.running:
        seconds += 1
        timer_label.config(text=f"Duration: {str(timedelta(seconds=seconds))}")
        timer_label.after(1000, update_timer)

def start_recording():
    global recorder, status_label, frame_rate_var, resolution_var
    if not recorder or not recorder.running:
        fps = float(frame_rate_var.get())
        resolution = tuple(map(int, resolution_var.get().split('x')))
        recorder = ScreenRecorder('test_video.mp4', fps, resolution, on_new_frame=update_video_frame)
        recorder.start_recording_thread(status_label)
        start_timer()  # added to start the timer
    else:
        print("Recording is already in progress.")
        messagebox.showinfo("Info", "Recording is already in progress.")  # added alert

def stop_recording():
    global recorder, status_label
    if recorder:
        recorder.stop_recording()
        status_label.config(text="Recording stopped. File saved as: "+ recorder.filename)
    else:
        status_label.config(text="No recording in progress.")

def update_stats():  # added for system stats
    global fps_label
    if recorder and recorder.running:
        fps = frame_rate_var.get()
        cpu_usage = psutil.cpu_percent()
        fps_label.config(text=f"FPS: {fps} | CPU: {cpu_usage}%")
        fps_label.after(1000, update_stats)

def bind_hotkeys():
    """Bind hotkeys for starting and stopping recording using `pynput`."""
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
    global video_display_label, status_label, frame_rate_var, resolution_var, timer_label, fps_label, scene_var, scene_menu
    root = tk.Tk()
    root.title("VoiceClips")
    root.geometry("1200x800")
    root.configure(bg="#2E2E2E")  # Modern dark background

    start_img = load_image('/Users/sreekarravavarapu/VoiceClips/start button.jpg', max_size=(60, 60))
    stop_img = load_image('/Users/sreekarravavarapu/VoiceClips/stop.jpg', max_size=(60, 60))

    frame_rate_var = StringVar(root, "60.0")
    resolution_var = StringVar(root, "1920x1080")
    resolution_options = {"1920x1080": "1920x1080", "1280x720": "1280x720", "640x480": "640x480"}

    scene_var = StringVar(root)
    scene_var.set("Default")
    scene_menu = OptionMenu(root, scene_var, "Scene 1", "Scene 2", "Add New Scene")
    scene_menu.grid()

    # Layout organization using grid
    main_frame = Frame(root, bg="#2E2E2E")
    main_frame.grid(row=0, column=0, sticky="nsew")

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Video display frame with fixed height
    video_frame = Frame(main_frame, bg="black", height=400)  # Fixed height for video display
    video_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=0)  # Ensure control frame has enough space
    main_frame.grid_columnconfigure(0, weight=1)

    video_display_label = Label(video_frame, bg="black")
    video_display_label.pack(fill=tk.BOTH, expand=True)

    # Control Frame
    control_frame = Frame(main_frame, bg="#404040", height=150)  # Fixed height for control frame
    control_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    # FPS and Timer Labels
    fps_label = Label(control_frame, text="FPS: 0 | CPU: 0%", bg="#404040", fg="white")
    fps_label.pack(side=tk.LEFT, padx=10)

    timer_label = Label(control_frame, text="Duration: 00:00:00", bg="#404040", fg="white")
    timer_label.pack(side=tk.LEFT, padx=10)

    status_label = Label(root, text="Status: Ready", anchor="w", bg="#2E2E2E", fg="white")
    status_label.grid(row=2, column=0, sticky="we", padx=10, pady=10)

    frame_rate_entry = OptionMenu(control_frame, frame_rate_var, "30.0", "60.0", "120.0")
    frame_rate_entry.config(bg="#505050", fg="white")
    frame_rate_entry.pack(side=tk.LEFT, padx=5)

    resolution_menu = OptionMenu(control_frame, resolution_var, *resolution_options.keys())
    resolution_menu.config(bg="#505050", fg="white")
    resolution_menu.pack(side=tk.LEFT, padx=5)

    start_btn = Button(control_frame, image=start_img, command=start_recording, bg="green", highlightthickness=0)
    start_btn.image = start_img
    start_btn.pack(side=tk.LEFT, padx=5)

    stop_btn = Button(control_frame, image=stop_img, command=stop_recording, bg="red", highlightthickness=0)
    stop_btn.image = stop_img
    stop_btn.pack(side=tk.LEFT, padx=5)

    add_scene_btn = Button(control_frame, text="Add Scene", command=add_scene, bg="blue", fg="white")  # added button to add scene
    add_scene_btn.pack(side=tk.LEFT, padx=5)

    root.after(1000, update_stats)  # System stats updater
    bind_hotkeys()  # Hotkey binding
    root.mainloop()
