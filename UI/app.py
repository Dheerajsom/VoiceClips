import tkinter as tk
from tkinter import Label, Button, Frame
from PIL import Image, ImageTk
from .recorder import ScreenRecorder

def update_video_frame(frame):
    """Update the GUI with new video frames."""
    global video_display_label
    image = Image.fromarray(frame)  # Convert NumPy array to PIL Image
    photo = ImageTk.PhotoImage(image)  # Convert PIL Image to PhotoImage
    video_display_label.config(image=photo)
    video_display_label.image = photo  # Keep a reference to avoid garbage collection

recorder = None

def start_recording():
    global recorder, status_label
    if not recorder or not recorder.running:
        recorder = ScreenRecorder('test_video.avi', 10, (1366, 768), on_new_frame=update_video_frame)
        recorder.start_recording_thread(status_label)
    else:
        print("Recording is already in progress.")

def stop_recording():
    global recorder, status_label
    if recorder:
        recorder.stop_recording()
        status_label.config(text="Recording stopped.")
    else:
        status_label.config(text="No recording in progress.")

def run_app():
    global video_display_label, status_label
    root = tk.Tk()
    root.title("VoiceClips")
    root.geometry("1200x700")  # Window size
    root.iconbitmap('C:\\Users\\dheer\\Documents\\VoiceClips\\voiceclipslogo.ico')

    # Video display label
    video_display_label = Label(root)
    video_display_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Status label at the bottom
    status_label = Label(root, text="Status: Ready")
    status_label.pack(side=tk.BOTTOM, fill=tk.X)

    # Control frame for buttons
    control_frame = Frame(root)
    control_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # Buttons for controlling recording
    start_btn = Button(control_frame, text="Start Recording", command=start_recording)
    start_btn.pack(side=tk.LEFT, padx=5, pady=5)

    stop_btn = Button(control_frame, text="Stop Recording", command=stop_recording)
    stop_btn.pack(side=tk.LEFT, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    run_app()
