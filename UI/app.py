import tkinter as tk
from tkinter import messagebox


def run_app():
    root = tk.Tk()
    root.title("Voice Clips")

    # Set the window icon using a file path with double backslashes
    root.iconbitmap('C:\\Users\\dheer\\Documents\\VoiceClips\\voiceclipslogo.ico')

    # Default window dimensions
    window_width = 1200
    window_height = 700

    # Get the screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate the position to center the window
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)

    # Set the position and size of the window
    root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')


    root.mainloop()