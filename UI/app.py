import tkinter as tk

def run_app():
    root = tk.Tk()
    root.title("Voice Clips")
    root.geometry('400x200')

    label = tk.Label(root, text="Welcome to Voice Clips!")
    label.pack(pady=20)

    root.mainloop()
