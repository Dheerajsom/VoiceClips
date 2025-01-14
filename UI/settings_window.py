# settings_window.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Function to open the settings window
def open_settings_window(parent, settings_callback):
    settings_window = tk.Toplevel(parent)
    settings_window.title("Settings")
    settings_window.geometry("800x600")

    # Sections in the settings window based on OBS-like categories
    sections = ["General", "Stream", "Output", "Audio", "Video", "Hotkeys", "Advanced"]

    sidebar = tk.Frame(settings_window, bg="#333")
    sidebar.pack(side=tk.LEFT, fill=tk.Y)
    main_content = tk.Frame(settings_window, bg="#2c2f33")
    main_content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    section_vars = {"General": {}, "Stream": {}, "Output": {}, "Audio": {}, "Video": {}, "Hotkeys": {}, "Advanced": {}}

    def save_settings():
        settings = {}
        for section, variables in section_vars.items():
            settings[section] = {key: var.get() for key, var in variables.items()}
        settings_callback(settings)
        messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")

    # Sidebar buttons for each section
    for section in sections:
        button = tk.Button(sidebar, text=section, bg="#444", fg="#fff", command=lambda s=section: load_section(main_content, s, section_vars[s]))
        button.pack(fill=tk.X, pady=5)

    # Initial load of the "General" section
    load_section(main_content, "General", section_vars["General"])

    # Save and Apply buttons
    save_button = tk.Button(settings_window, text="Apply", command=save_settings)
    save_button.pack(side=tk.BOTTOM, pady=10)

# Function to dynamically load content in the main content area based on the selected section
def load_section(main_content, section, variables):
    for widget in main_content.winfo_children():
        widget.destroy()

    if section == "General":
        ttk.Label(main_content, text="General Settings", font=("Helvetica", 16), background="#2c2f33", foreground="#fff").pack(pady=20)

        # Language selection
        ttk.Label(main_content, text="Language:", background="#2c2f33", foreground="#fff").pack(pady=5)
        language_var = tk.StringVar(value="English")
        language_menu = ttk.Combobox(main_content, textvariable=language_var, values=["English", "Spanish", "French"])
        language_menu.pack(pady=5)
        variables["language"] = language_var

        # Theme selection
        ttk.Label(main_content, text="Theme:", background="#2c2f33", foreground="#fff").pack(pady=5)
        theme_var = tk.StringVar(value="Dark")
        theme_menu = ttk.Combobox(main_content, textvariable=theme_var, values=["Light", "Dark"])
        theme_menu.pack(pady=5)
        variables["theme"] = theme_var

    elif section == "Stream":
        ttk.Label(main_content, text="Stream Settings", font=("Helvetica", 16), background="#2c2f33", foreground="#fff").pack(pady=20)

        # Stream key and platform
        ttk.Label(main_content, text="Stream Key:", background="#2c2f33", foreground="#fff").pack(pady=5)
        stream_key_var = tk.StringVar(value="")
        stream_key_entry = ttk.Entry(main_content, textvariable=stream_key_var)
        stream_key_entry.pack(pady=5)
        variables["stream_key"] = stream_key_var

        ttk.Label(main_content, text="Streaming Platform:", background="#2c2f33", foreground="#fff").pack(pady=5)
        platform_var = tk.StringVar(value="YouTube")
        platform_menu = ttk.Combobox(main_content, textvariable=platform_var, values=["YouTube", "Twitch", "Facebook Live"])
        platform_menu.pack(pady=5)
        variables["platform"] = platform_var

    elif section == "Output":
        ttk.Label(main_content, text="Output Settings", font=("Helvetica", 16), background="#2c2f33", foreground="#fff").pack(pady=20)

        # Recording Path
        ttk.Label(main_content, text="Recording Path:", background="#2c2f33", foreground="#fff").pack(pady=5)
        recording_path_var = tk.StringVar(value="")
        ttk.Entry(main_content, textvariable=recording_path_var).pack(pady=5)
        ttk.Button(main_content, text="Browse", command=lambda: browse_recording_path(recording_path_var)).pack(pady=5)
        variables["recording_path"] = recording_path_var

        # Output format
        ttk.Label(main_content, text="Recording Format:", background="#2c2f33", foreground="#fff").pack(pady=5)
        output_format_var = tk.StringVar(value="MP4")
        output_format_menu = ttk.Combobox(main_content, textvariable=output_format_var, values=["MP4", "MKV", "FLV", "MOV"])
        output_format_menu.pack(pady=5)
        variables["output_format"] = output_format_var

    elif section == "Audio":
        ttk.Label(main_content, text="Audio Settings", font=("Helvetica", 16), background="#2c2f33", foreground="#fff").pack(pady=20)

        # Desktop Audio Device
        ttk.Label(main_content, text="Desktop Audio Device:", background="#2c2f33", foreground="#fff").pack(pady=5)
        desktop_audio_var = tk.StringVar(value="Default")
        desktop_audio_menu = ttk.Combobox(main_content, textvariable=desktop_audio_var, values=["Default", "Speakers", "Headphones"])
        desktop_audio_menu.pack(pady=5)
        variables["desktop_audio_device"] = desktop_audio_var

        # Mic/Auxiliary Audio Device
        ttk.Label(main_content, text="Mic/Auxiliary Audio Device:", background="#2c2f33", foreground="#fff").pack(pady=5)
        mic_audio_var = tk.StringVar(value="Default")
        mic_audio_menu = ttk.Combobox(main_content, textvariable=mic_audio_var, values=["Default", "Microphone 1", "Microphone 2"])
        mic_audio_menu.pack(pady=5)
        variables["mic_audio_device"] = mic_audio_var

    elif section == "Video":
        ttk.Label(main_content, text="Video Settings", font=("Helvetica", 16), background="#2c2f33", foreground="#fff").pack(pady=20)

        # Canvas resolution
        ttk.Label(main_content, text="Base (Canvas) Resolution:", background="#2c2f33", foreground="#fff").pack(pady=5)
        canvas_resolution_var = tk.StringVar(value="1920x1080")
        canvas_resolution_entry = ttk.Entry(main_content, textvariable=canvas_resolution_var)
        canvas_resolution_entry.pack(pady=5)
        variables["canvas_resolution"] = canvas_resolution_var

        # Output resolution
        ttk.Label(main_content, text="Output (Scaled) Resolution:", background="#2c2f33", foreground="#fff").pack(pady=5)
        output_resolution_var = tk.StringVar(value="1280x720")
        output_resolution_entry = ttk.Entry(main_content, textvariable=output_resolution_var)
        output_resolution_entry.pack(pady=5)
        variables["output_resolution"] = output_resolution_var

        # FPS control
        ttk.Label(main_content, text="FPS Control:", background="#2c2f33", foreground="#fff").pack(pady=5)
        fps_var = tk.StringVar(value="30")
        fps_menu = ttk.Combobox(main_content, textvariable=fps_var, values=["24", "30", "60"])
        fps_menu.pack(pady=5)
        variables["fps"] = fps_var

    elif section == "Hotkeys":
        ttk.Label(main_content, text="Hotkeys Settings", font=("Helvetica", 16), background="#2c2f33", foreground="#fff").pack(pady=20)

        ttk.Label(main_content, text="Start/Stop Recording Hotkey:", background="#2c2f33", foreground="#fff").pack(pady=5)
        hotkey_var = tk.StringVar(value="Ctrl+R")
        hotkey_entry = ttk.Entry(main_content, textvariable=hotkey_var)
        hotkey_entry.pack(pady=5)
        variables["recording_hotkey"] = hotkey_var

    elif section == "Advanced":
        ttk.Label(main_content, text="Advanced Settings", font=("Helvetica", 16), background="#2c2f33", foreground="#fff").pack(pady=20)

        ttk.Label(main_content, text="Process Priority:", background="#2c2f33", foreground="#fff").pack(pady=5)
        priority_var = tk.StringVar(value="Normal")
        priority_menu = ttk.Combobox(main_content, textvariable=priority_var, values=["Low", "Normal", "High"])
        priority_menu.pack(pady=5)
        variables["priority"] = priority_var

        ttk.Label(main_content, text="Enable Portable Mode:", background="#2c2f33", foreground="#fff").pack(pady=5)
        portable_mode_var = tk.BooleanVar()
        portable_mode_check = ttk.Checkbutton(main_content, variable=portable_mode_var, text="Enable")
        portable_mode_check.pack(pady=5)
        variables["portable_mode"] = portable_mode_var

# Helper function to browse recording path
def browse_recording_path(var):
    path = filedialog.askdirectory()
    if path:
        var.set(path)
