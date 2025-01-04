# main.py
import tkinter as tk
from tkinter import messagebox
from threading import Thread
from audio import ScreenRecorder

def start_recording():
    global recorder_thread
    recorder = ScreenRecorder('test_video.avi', 10, (1366, 768))
    recorder_thread = Thread(target=recorder.start_recording)
    recorder_thread.start()
    status_label.config(text="Status: Recording...")

def stop_recording():
    recorder.stop_recording()
    status_label.config(text="Status: Recording stopped.")

def run_app():
    root = tk.Tk()
    root.title("Screen Recorder")

    global status_label
    status_label = tk.Label(root, text="Status: Ready")
    status_label.pack()

    start_btn = tk.Button(root, text="Start Recording", command=start_recording)
    start_btn.pack()

    stop_btn = tk.Button(root, text="Stop Recording", command=stop_recording)
    stop_btn.pack()

    root.mainloop()

if __name__ == "__main__":
    run_app()

