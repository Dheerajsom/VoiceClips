import tkinter as tk
from tkinter import messagebox

def run_app():
    root = tk.Tk()
    root.title("Voice Clips")

    def on_exit():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_exit)
    root.mainloop()
