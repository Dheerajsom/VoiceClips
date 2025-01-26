# utils.py
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

def get_macos_devices():
    """Get list of available audio/video devices on macOS"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stderr
    except Exception as e:
        print(f"Error getting macOS devices: {e}")
        return ""

def list_available_audio_devices():
    system = platform.system()
    audio_devices = []

    if system == "Darwin":  # macOS
        devices_info = get_macos_devices()
        for line in devices_info.split('\n'):
            if "[audio]" in line:
                try:
                    index = line.split("]")[0].split("[")[1]
                    name = line.split("]")[1].strip()
                    audio_devices.append(f"{index}:{name}")
                except:
                    continue
    elif system == "Windows":
        try:
            result = subprocess.run(
                ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                stderr=subprocess.PIPE,
                text=True
            )
            for line in result.stderr.split("\n"):
                if "DirectShow audio devices" in line:
                    audio_devices.append(line.split('"')[1])
        except Exception:
            pass
    elif system == "Linux":
        try:
            result = subprocess.run(
                ["pactl", "list", "sources"],
                stdout=subprocess.PIPE,
                text=True
            )
            for line in result.stdout.split("\n"):
                if "Name:" in line:
                    audio_devices.append(line.split(":")[1].strip())
        except Exception:
            pass

    if not audio_devices:
        print("No audio devices found. Proceeding with default audio.")
        audio_devices.append("Default")

    return audio_devices

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def get_ffmpeg_command(system):
    """Get appropriate FFmpeg command for the system"""
    if system == "Windows":
        return "ffmpeg.exe"
    return "ffmpeg"

def get_system_info():
    """Get system information for debugging"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }