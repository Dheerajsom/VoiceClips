import tkinter as tk
from tkinter import messagebox
from threading import Thread
import sys
sys.path.append('..')  # Ensure that this script can access modules in the parent directory

from .widgets import create_button, create_label, create_entry
from audio.recorder import ScreenRecorder

recorder = None  # Initialize the recorder as a global variable

def start_recording():
    global recorder
    recorder = ScreenRecorder('test_video.avi', 10, (1366, 768))  # Define video filename and settings
    recorder.start_recording()

def stop_recording():
    global recorder
    if recorder:
        recorder.stop_recording()
        status_label.config(text="Status: Recording stopped.")
    else:
        print("No recording in progress.")

def start_recording_thread():
    global recorder
    if not recorder or not recorder.running:
        thread = Thread(target=start_recording)
        thread.start()
        status_label.config(text="Status: Recording...")
    else:
        print("Recording is already in progress.")

def change_frame_rate():
    if recorder:
        new_rate = frame_rate_entry.get()
        try:
            new_rate = float(new_rate)
            recorder.change_frame_rate(new_rate)
            status_label.config(text=f"Status: Frame rate set to {new_rate} fps")
        except ValueError:
            status_label.config(text="Invalid frame rate entered.")
    else:
        print("Recorder not initialized.")

def run_app():
    root = tk.Tk()
    root.title("Voice Clips")

    # Define dimensions and positioning
    window_width = 1200
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')
    root.iconbitmap('C:\\Users\\dheer\\Documents\\VoiceClips\\voiceclipslogo.ico')  # Set the window icon

    # Buttons
    create_button(root, "Start Recording", start_recording_thread)
    create_button(root, "Stop Recording", stop_recording)
    create_button(root, "Change Frame Rate", change_frame_rate)

    # Entry for frame rate
    global frame_rate_entry
    frame_rate_entry = create_entry(root, "30")  # Default frame rate

    # Status label
    global status_label
    status_label = create_label(root, "Status: Ready")

    root.mainloop()

if __name__ == "__main__":
    run_app()
