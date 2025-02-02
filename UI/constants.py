DEFAULT_FPS = 30
DEFAULT_FILE_EXTENSION = "mp4"
ACCEPTABLE_FILE_EXTENSIONS = ["avi", "mp4", "mov", "mkv", "webm"]
DEFAULT_CLIP_DURATION = 30
DEFAULT_CLIP_HOTKEY = "Ctrl+C"
BASE_CANVAS_RESOLUTION = "1920x1080"
OUTPUT_SCALED_RESOLUTION = "1280x720"
VIDEO_FILTERS = {
    "bilinear": "-vf scale=iw*0.5:ih*0.5",
    "bicubic": "-vf scale=iw*0.5:ih*0.5 -sws_flags bicubic",
    "lanczos": "-vf scale=iw*0.5:ih*0.5 -sws_flags lanczos"
}
