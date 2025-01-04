
import tkinter as tk
from tkinter import messagebox, simpledialog, Label, Entry
from widgets import create_button, create_label, create_entry

def start_recording():
    # Placeholder function for starting the recording
    print("Recording started!")
    status_label.config(text="Status: Recording...")

def stop_recording():
    # Placeholder function for stopping the recording
    print("Recording stopped!")
    status_label.config(text="Status: Recording stopped.")

def change_frame_rate():
    # Placeholder function to change frame rate
    new_rate = frame_rate_entry.get()
    print(f"Frame rate changed to: {new_rate} fps")
    status_label.config(text=f"Status: Frame rate set to {new_rate} fps")

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
    root.iconbitmap('path_to_icon.ico')  # Set the window icon

    # Buttons
    create_button(root, "Start Recording", start_recording)
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
