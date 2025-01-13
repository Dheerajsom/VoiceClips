import tkinter
import glob
import cv2
import platform
import subprocess
from typing import Tuple

def get_desktop_resolution() -> Tuple[int, int]:
    root = tkinter.Tk()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height

def get_default_output_path(ext: str = "mp4") -> str:
    filenames = glob.glob(f"out_????.{ext}")
    for i in range(1, 10000):
        name = f"out_{i:04d}.{ext}"
        if name not in filenames:
            return name
    return f"out_9999.{ext}"

def list_available_devices():
    index = 0
    available_devices = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            break
        available_devices.append(f"Device {index}")
        cap.release()
        index += 1
    return available_devices

def list_available_audio_devices():
    system = platform.system()
    audio_devices = []

    if system == "Darwin":  # macOS
        try:
            result = subprocess.run(["ffmpeg", "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                                    stderr=subprocess.PIPE, text=True)
            for line in result.stderr.split("\n"):
                if """[AVFoundation""" in line and "audio" in line.lower():
                    audio_devices.append(line.strip().split('[')[-1].split(']')[0])
        except Exception as e:
            audio_devices.append("Error listing audio devices")

    elif system == "Linux":  # Linux using `pactl`
        try:
            result = subprocess.run(["pactl", "list", "short", "sources"], stdout=subprocess.PIPE, text=True)
            for line in result.stdout.split("\n"):
                if "RUNNING" in line:
                    audio_devices.append(line.split()[1])
        except Exception as e:
            audio_devices.append("Error listing audio devices")

    elif system == "Windows":  # Windows using `ffmpeg` with `dshow`
        try:
            result = subprocess.run(["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                                    stderr=subprocess.PIPE, text=True)
            for line in result.stderr.split("\n"):
                if "DirectShow audio" in line:
                    audio_devices.append(line.strip().split('"')[1])
        except Exception as e:
            audio_devices.append("Error listing audio devices")

    return audio_devices if audio_devices else ["No audio devices found"]
