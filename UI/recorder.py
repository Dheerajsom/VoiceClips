# recorder.py
import platform
from utils import list_available_audio_devices

def video_capture_command(fps, width, height, audio, output_path, source_type="screen", window_title=None):
    system = platform.system()
    
    # Ensure even dimensions
    width += width % 2
    height += height % 2

    if system == "Darwin":  # macOS
        # Get available devices
        devices_info = list_available_audio_devices()
        print(f"Available devices:\n{devices_info}")  # Debug info
        
        # Default device configuration for macOS
        video_device = "1"  # Usually "1" is screen capture
        audio_device = "0"  # Usually "0" is default audio input
        
        command = [
            "ffmpeg",
            "-f", "avfoundation",
            "-framerate", str(fps),
            "-video_size", f"{width}x{height}",
            "-capture_cursor", "1",  # Capture cursor
            "-capture_mouse_clicks", "1",  # Capture mouse clicks
            "-i", f"{video_device}:{audio_device}",  # Format: "video:audio"
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",  # Compatible pixel format
            "-c:a", "aac",
            "-b:a", "128k",
            "-strict", "experimental",
            "-r", str(fps),
            "-y",  # Overwrite output file
            output_path
        ]

    elif system == "Linux":
        command = [
            "ffmpeg",
            "-f", "x11grab",
            "-r", str(fps),
            "-s", f"{width}x{height}",
            "-i", ":0.0",
            "-f", "pulse",
            "-i", "default",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            output_path
        ]

    else:  # Windows
        audio_devices = list_available_audio_devices()
        selected_audio_device = audio_devices[0] if audio and "None" not in audio_devices else None
        
        command = [
            "ffmpeg",
            "-f", "gdigrab",
            "-framerate", str(fps),
            "-video_size", f"{width}x{height}",
            "-i", "desktop",
        ]

        # Add audio input if available
        if selected_audio_device:
            command.extend([
                "-f", "dshow",
                "-i", f"audio={selected_audio_device}"
            ])
        else:
            command.extend([
                "-f", "lavfi",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"
            ])

        # Add output options
        command.extend([
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-profile:v", "baseline",
            "-level", "3.0",
            "-c:a", "aac",
            "-b:a", "128k",
            "-r", str(fps),
            "-y",
            output_path
        ])

    print(f"FFmpeg command: {' '.join(command)}")  # Debug info
    return command