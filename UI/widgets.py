import tkinter as tk
from tkinter import StringVar

def create_button(parent, text, command, bg="#505050"):
    button = tk.Button(parent, text=text, command=command, bg=bg, fg="white")
    button.pack(pady=5)
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

def create_menu(parent, options):
    """Create a dropdown menu for scene or resolution selection."""
    menu = tk.OptionMenu(parent, StringVar(value=options[0]), *options)
    menu.pack(pady=10)
    return menu