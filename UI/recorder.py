import platform
from utils import list_available_audio_devices

def video_capture_command(fps, width, height, audio, output_path, source_type="screen", window_title=None):
    system = platform.system()
    if source_type == "window" and window_title:
        if system == "Darwin":  # macOS window capture
            input_option = f"{window_title}:none"
        elif system == "Windows":
            input_option = f"title={window_title}"
        else:
            input_option = ":0.0+0,0"
    else:
        input_option = "3:0" if audio else "1:none"  # Full screen + audio input for macOS

    if system == "Darwin":
        return [
            "ffmpeg", "-f", "avfoundation", "-framerate", str(fps),
            "-video_size", f"{width}x{height}",
            "-pix_fmt", "uyvy422",  # Fixed pixel format for macOS
            "-i", input_option, "-c:v", "libx264",
            "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k",
            "-fps_mode", "cfr", "-r", str(fps), output_path
        ]
    elif system == "Linux":
        return [
            "ffmpeg", "-f", "x11grab", "-r", str(fps), "-s", f"{width}x{height}",
            "-i", ":0.0", "-f", "pulse", "-i", "default", "-c:v", "libx264",
            "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k",
            "-fps_mode", "cfr", "-r", str(fps), output_path
        ]
    
    system = platform.system()

    if source_type == "window" and window_title:
        input_option = f"title={window_title}" if system == "Windows" else f"{window_title}:none"
    else:
        input_option = "desktop" if system == "Windows" else "3:0" if audio else "1:none"

    width += width % 2
    height += height % 2

    audio_devices = list_available_audio_devices()
    selected_audio_device = audio_devices[0] if audio and "None" not in audio_devices else None
    audio_input = ["-f", "dshow", "-i", f"audio='{selected_audio_device}'"] if selected_audio_device else ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

    return [
        "ffmpeg", "-f", "gdigrab", "-framerate", str(fps), "-video_size", f"{width}x{height}", "-i", input_option,
        *audio_input,
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-profile:v", "baseline", "-level", "3.0", "-c:a", "aac", "-b:a", "128k", "-r", str(fps), output_path
    ]
