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

    if system == "Windows":
        try:
            result = subprocess.run(["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                                    stderr=subprocess.PIPE, text=True)
            for line in result.stderr.split("\n"):
                if "DirectShow audio" in line:
                    audio_device = line.split('"')[1]
                    audio_devices.append(audio_device)
        except Exception:
            pass

    if not audio_devices:
        print("No audio devices found. Proceeding with silent audio fallback.")
        audio_devices.append("None")

    return audio_devices
    