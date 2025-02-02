# src/constants.py

import os
from pathlib import Path

# Application Constants
APP_NAME = "VoiceClips"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Your Name"
APP_WEBSITE = "https://yourwebsite.com"

# Paths
USER_HOME = str(Path.home())
DEFAULT_SAVE_LOCATION = str(Path(USER_HOME) / "Documents" / "VoiceClips")
DEFAULT_CLIPS_FOLDER = str(Path(DEFAULT_SAVE_LOCATION) / "Clips")
DEFAULT_RECORDINGS_FOLDER = str(Path(DEFAULT_SAVE_LOCATION) / "Recordings")
DEFAULT_CONFIG_PATH = str(Path(USER_HOME) / ".voiceclips" / "config.json")
DEFAULT_LOGS_PATH = str(Path(USER_HOME) / ".voiceclips" / "logs")
DEFAULT_CACHE_PATH = str(Path(USER_HOME) / ".voiceclips" / "cache")

# Video Settings
DEFAULT_FPS = 30
BASE_CANVAS_RESOLUTION = "1920x1080"
OUTPUT_SCALED_RESOLUTION = "1280x720"
ACCEPTABLE_FILE_EXTENSIONS = ["mp4", "mkv", "avi", "mov"]
DEFAULT_FILE_EXTENSION = "mp4"
VIDEO_BITRATES = {
    "low": "2500k",
    "medium": "5000k",
    "high": "8000k"
}
VIDEO_PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium"]
DEFAULT_VIDEO_PRESET = "veryfast"

# Audio Settings
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 2
AUDIO_CHUNK_SIZE = 1024
DEFAULT_AUDIO_FORMAT = 'wav'
AUDIO_BITRATES = {
    "low": "128k",
    "medium": "256k",
    "high": "320k"
}
DEFAULT_MIC_VOLUME = 75
DEFAULT_DESKTOP_VOLUME = 75

# Clipping Settings
DEFAULT_CLIP_DURATION = 30  # seconds
DEFAULT_CLIP_HOTKEY = "Ctrl+C"
DEFAULT_CLIP_FORMAT = "mp4"
CLIP_BUFFER_SIZE = DEFAULT_CLIP_DURATION * DEFAULT_FPS
CLIP_NAMING_FORMAT = "clip_{timestamp}_{counter}"

# UI Settings
UI_THEME = "darkly"
VALID_THEMES = [
    "darkly",     # Dark theme
    "cosmo",      # Light theme
    "superhero",  # Dark blue theme
    "solar",      # Dark brown theme
    "cyborg",     # Dark gray theme
    "vapor",      # Dark purple theme
    "litera",     # Light minimal theme
    "flatly",     # Light flat theme
    "yeti",       # Light modern theme
    "journal"     # Light clean theme
]
UI_DEFAULT_SIZE = "1280x720"
UI_MIN_SIZE = "800x600"
UI_FONTS = {
    "header": ("Helvetica", 16, "bold"),
    "normal": ("Helvetica", 12),
    "small": ("Helvetica", 10)
}
UI_COLORS = {
    "bg_dark": "#2b2b2b",
    "bg_light": "#3b3b3b",
    "text": "#ffffff",
    "accent": "#007acc",
    "error": "#ff3333",
    "success": "#33cc33"
}

# Performance Settings
PERFORMANCE_UPDATE_INTERVAL = 1.0  # seconds
PERFORMANCE_HISTORY_LENGTH = 3600  # 1 hour
PERFORMANCE_THRESHOLDS = {
    "cpu_warning": 80,
    "cpu_critical": 90,
    "memory_warning": 80,
    "memory_critical": 90,
    "disk_warning": 80,
    "disk_critical": 90
}

# Error Messages
ERROR_MESSAGES = {
    "ffmpeg_not_found": "FFmpeg is not installed. Please install FFmpeg to use this application.",
    "invalid_resolution": "Invalid resolution format. Use WIDTHxHEIGHT (e.g., 1920x1080)",
    "no_audio_devices": "No audio devices found. Check your system audio settings.",
    "no_video_devices": "No video capture devices found.",
    "invalid_path": "Invalid save location. Please choose a valid directory.",
    "no_disk_space": "Not enough disk space to continue recording.",
    "permission_denied": "Permission denied. Please check folder permissions.",
    "config_error": "Error loading configuration. Using defaults.",
    "recording_error": "Error during recording. Please check logs.",
    "clipping_error": "Error creating clip. Please check logs."
}

# Success Messages
SUCCESS_MESSAGES = {
    "recording_started": "Recording started successfully",
    "recording_stopped": "Recording stopped successfully",
    "clip_created": "Clip created successfully",
    "settings_saved": "Settings saved successfully",
    "config_loaded": "Configuration loaded successfully"
}

# FFmpeg Commands
FFMPEG_COMMANDS = {
    "windows": {
        "screen": "-f gdigrab -framerate {fps} -i desktop",
        "audio": "-f dshow -i audio=\"{device}\""
    },
    "darwin": {  # macOS
        "screen": "-f avfoundation -i \"1:0\" -framerate {fps}",
        "audio": "-f avfoundation -i \":{audio_index}\""
    },
    "linux": {
        "screen": "-f x11grab -r {fps} -i :0.0",
        "audio": "-f pulse -i default"
    }
}

# Logging Settings
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

# Voice Recognition Settings
VOICE_COMMANDS = {
    "clip": ["clip", "clips", "clipped", "save that", "clip that"],
    "start": ["start recording", "begin recording", "start"],
    "stop": ["stop recording", "end recording", "stop"],
    "pause": ["pause recording", "pause"],
    "resume": ["resume recording", "resume"]
}
VOICE_COMMAND_SIMILARITY_THRESHOLD = 75  # Fuzzy matching threshold

# Default Configuration
DEFAULT_CONFIG = {
    "general": {
        "language": "English",
        "theme": UI_THEME,
        "check_updates": True
    },
    "video": {
        "resolution": BASE_CANVAS_RESOLUTION,
        "fps": DEFAULT_FPS,
        "quality": "High",
        "encoder": "x264",
        "preset": DEFAULT_VIDEO_PRESET
    },
    "audio": {
        "sample_rate": AUDIO_SAMPLE_RATE,
        "channels": AUDIO_CHANNELS,
        "mic_device": "Default",
        "desktop_device": "Default",
        "mic_volume": DEFAULT_MIC_VOLUME,
        "desktop_volume": DEFAULT_DESKTOP_VOLUME
    },
    "recording": {
        "format": DEFAULT_FILE_EXTENSION,
        "save_path": DEFAULT_RECORDINGS_FOLDER,
        "filename_template": "recording_{timestamp}"
    },
    "clipping": {
        "duration": DEFAULT_CLIP_DURATION,
        "format": DEFAULT_CLIP_FORMAT,
        "save_path": DEFAULT_CLIPS_FOLDER,
        "hotkey": DEFAULT_CLIP_HOTKEY
    },
    "performance": {
        "priority": "Normal",
        "gpu_encoding": True,
        "optimization_threshold": 80
    }
}