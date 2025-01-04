import tkinter as tk

def create_button(parent, text, command):
    button = tk.Button(parent, text=text, command=command)
    button.pack(pady=20)
    return button
