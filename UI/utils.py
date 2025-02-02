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

def list_available_audio_devices():
    """Get list of available audio devices with improved detection"""
    system = platform.system()
    audio_devices = []

    if system == "Windows":
        # Try using sounddevice library first (more reliable)
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            for device in devices:
                if device['max_input_channels'] > 0:  # Input devices only
                    audio_devices.append(device['name'])
        except ImportError:
            # Fallback to dshow enumeration
            try:
                result = subprocess.run(
                    ['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                lines = result.stderr.split('\n')
                audio_section = False
                for line in lines:
                    if "DirectShow audio devices" in line:
                        audio_section = True
                    elif audio_section and "]  \"" in line:
                        device_name = line.split('\"')[1]
                        if device_name and "virtual" not in device_name.lower():
                            audio_devices.append(device_name)
            except subprocess.SubprocessError as e:
                print(f"Error enumerating DirectShow devices: {e}")

    elif system == "Darwin":  # macOS
        # Try using sounddevice first
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            for device in devices:
                if device['max_input_channels'] > 0:
                    audio_devices.append(device['name'])
        except ImportError:
            # Fallback to CoreAudio enumeration
            try:
                result = subprocess.run(
                    ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                    stderr=subprocess.PIPE,
                    text=True
                )
                for line in result.stderr.split('\n'):
                    if '[audio]' in line:
                        try:
                            name = line.split(']')[1].strip()
                            if name and "virtual" not in name.lower():
                                audio_devices.append(name)
                        except IndexError:
                            continue
            except subprocess.SubprocessError as e:
                print(f"Error enumerating CoreAudio devices: {e}")

    else:  # Linux
        # Try using sounddevice first
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            for device in devices:
                if device['max_input_channels'] > 0:
                    audio_devices.append(device['name'])
        except ImportError:
            # Try PulseAudio first
            try:
                result = subprocess.run(
                    ['pactl', 'list', 'sources'],
                    stdout=subprocess.PIPE,
                    text=True
                )
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Name:' in line:
                        name = line.split(':')[1].strip()
                        if name and "virtual" not in name.lower():
                            audio_devices.append(name)
            except (subprocess.SubprocessError, FileNotFoundError):
                # Fallback to ALSA
                try:
                    result = subprocess.run(
                        ['arecord', '-l'],
                        stdout=subprocess.PIPE,
                        text=True
                    )
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'card' in line and 'device' in line:
                            name = line.split(':')[1].strip()
                            if name and "virtual" not in name.lower():
                                audio_devices.append(name)
                except (subprocess.SubprocessError, FileNotFoundError) as e:
                    print(f"Error enumerating ALSA devices: {e}")

    # Add default device if no devices found
    if not audio_devices:
        print("No specific audio devices found. Adding default audio device.")
        audio_devices.append("Default Audio Device")
        
    # Remove duplicates while preserving order
    audio_devices = list(dict.fromkeys(audio_devices))
    
    print(f"Detected audio devices: {audio_devices}")
    return audio_devices

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
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