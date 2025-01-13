import platform

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
    elif system == "Windows":
        return [
            "ffmpeg", "-f", "gdigrab", "-framerate", str(fps), "-i", "desktop",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k",
            "-fps_mode", "cfr", "-r", str(fps), output_path
        ]
