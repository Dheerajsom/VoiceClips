import tkinter as tk

def create_button(parent, text, command):
    button = tk.Button(parent, text=text, command=command)
    button.pack(pady=10)
    return button

def create_label(parent, text):
    label = tk.Label(parent, text=text)
    label.pack(pady=10)
    return label

def create_entry(parent, default_text):
    entry = tk.Entry(parent)
    entry.insert(0, default_text)
    entry.pack(pady=10)
    return entry
