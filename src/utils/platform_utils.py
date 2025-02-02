# src/utils/platform_utils.py
import platform
import os
import subprocess
import logging
from typing import Dict, Optional, List
import shutil

class PlatformManager:
    """Handles platform-specific operations and checks."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system = platform.system().lower()
        self.ffmpeg_path = self._find_ffmpeg()

    def get_system(self) -> str:
        """Get current operating system."""
        return self.system

    def is_windows(self) -> bool:
        return self.system == 'windows'

    def is_macos(self) -> bool:
        return self.system == 'darwin'

    def is_linux(self) -> bool:
        return self.system == 'linux'

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        try:
            # Check FFmpeg
            result = subprocess.run(['ffmpeg', '-version'], 
                                capture_output=True, 
                                text=True)
            if result.returncode != 0:
                print("FFmpeg not found")  # Debug print
                return False
                
            print("FFmpeg found:", result.stdout.split('\n')[0])  # Debug print
            return True

        except Exception as e:
            print(f"Error checking dependencies: {e}")  # Debug print
            return False

    def _find_ffmpeg(self) -> Optional[str]:
        """Locate FFmpeg executable."""
        try:
            # Check if FFmpeg is in PATH
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path:
                return ffmpeg_path

            # Platform-specific locations
            if self.is_windows():
                common_paths = [
                    r"C:\Program Files\FFmpeg\bin\ffmpeg.exe",
                    r"C:\FFmpeg\bin\ffmpeg.exe"
                ]
            elif self.is_macos():
                common_paths = [
                    "/usr/local/bin/ffmpeg",
                    "/opt/homebrew/bin/ffmpeg"
                ]
            else:  # Linux
                common_paths = [
                    "/usr/bin/ffmpeg",
                    "/usr/local/bin/ffmpeg"
                ]

            for path in common_paths:
                if os.path.isfile(path):
                    return path

            return None

        except Exception as e:
            self.logger.error(f"Error finding FFmpeg: {e}")
            return None

    def _check_audio_devices(self) -> bool:
        """Check for available audio devices."""
        try:
            if self.is_windows():
                return self._check_windows_audio()
            elif self.is_macos():
                return self._check_macos_audio()
            else:
                return self._check_linux_audio()

        except Exception as e:
            self.logger.error(f"Error checking audio devices: {e}")
            return False

    def _check_windows_audio(self) -> bool:
        try:
            result = subprocess.run(
                ['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
                capture_output=True,
                text=True
            )
            return 'DirectShow audio devices' in result.stderr
        except Exception:
            return False

    def _check_macos_audio(self) -> bool:
        try:
            result = subprocess.run(
                ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                capture_output=True,
                text=True
            )
            return '[audio]' in result.stderr
        except Exception:
            return False

    def _check_linux_audio(self) -> bool:
        try:
            result = subprocess.run(
                ['pactl', 'list', 'sources'],
                capture_output=True,
                text=True
            )
            return len(result.stdout) > 0
        except Exception:
            return False

    def get_config_path(self) -> str:
        """Get platform-specific config directory."""
        if self.is_windows():
            base_path = os.environ.get('APPDATA')
        elif self.is_macos():
            base_path = os.path.expanduser('~/Library/Application Support')
        else:
            base_path = os.path.expanduser('~/.config')

        return os.path.join(base_path, 'StreamStudio')

    def get_temp_path(self) -> str:
        """Get platform-specific temp directory."""
        if self.is_windows():
            return os.path.join(os.environ.get('TEMP'), 'StreamStudio')
        return os.path.join('/tmp', 'StreamStudio')