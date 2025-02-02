# src/utils/config_manager.py
import json
import os
import logging
from typing import Any, Dict, Optional
from pathlib import Path
import sys

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Constants that were previously imported from constants.py
UI_THEME = "darkly"
DEFAULT_SAVE_LOCATION = str(Path.home() / "Documents" / "VoiceClips")
DEFAULT_CLIPS_FOLDER = str(Path.home() / "Documents" / "VoiceClips" / "Clips")
DEFAULT_RECORDINGS_FOLDER = str(Path.home() / "Documents" / "VoiceClips" / "Recordings")

class ConfigManager:
    """Manages application configuration and settings."""
    
    def __init__(self, config_file: str):
        self.logger = logging.getLogger(__name__)
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.load_config()

    def save(self) -> bool:
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            self.logger.info("Configuration saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                self.logger.info("Configuration loaded successfully")
                return True
            else:
                self.logger.info("No configuration file found, using defaults")
                self.config = self.get_default_config()
                return self.save()  # Changed from save_config to save

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.config = self.get_default_config()
            return False

    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            self.logger.info("Configuration saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        try:
            # Support nested keys (e.g., "video.resolution")
            keys = key.split('.')
            value = self.config
            
            # Add debug logging
            print(f"Getting config key: {key}")
            print(f"Current config: {self.config}")
            
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                    if value is None:
                        print(f"Returning default value: {default}")
                        return default
                else:
                    print(f"Returning default value: {default}")
                    return default
                    
            print(f"Returning value: {value if value is not None else default}")
            return value if value is not None else default
            
        except Exception as e:
            print(f"Error getting config value: {e}")
            return default

    def set(self, key: str, value: Any) -> bool:
        """Set configuration value."""
        try:
            keys = key.split('.')
            config = self.config
            
            # Navigate to the correct nested level
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            return True

        except Exception as e:
            self.logger.error(f"Error setting configuration value: {e}")
            return False

    def update(self, new_config: Dict[str, Any]) -> bool:
        """Update multiple configuration values."""
        try:
            self._deep_update(self.config, new_config)
            return self.save()  # Save after updating
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False

    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> None:
        """Recursively update nested dictionary."""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "general": {
                "language": "English",
                "theme": "darkly",  # Explicitly set to "darkly"
                "check_updates": True
            },
            "video": {
                "resolution": "1920x1080",
                "fps": 30,
                "quality": "High",
                "encoder": "x264",
                "input_device": "Screen Capture" 
            },
            "audio": {
                "sample_rate": 44100,
                "channels": 2,
                "mic_device": "Default",
                "desktop_device": "Default"
            },
            "recording": {
                "format": "mp4",
                "save_path": str(Path.home() / "Videos" / "StreamStudio"),
                "filename_template": "recording_{timestamp}"
            },
            "clipping": {
                "duration": 30,
                "format": "mp4",
                "save_path": str(Path.home() / "Videos" / "StreamStudio" / "Clips"),
                "hotkey": "Ctrl+C"
            },
            "streaming": {
                "service": "",
                "server": "",
                "key": "",
                "bitrate": 2500
            },
            "ui": {
                "layout": "default",
                "show_preview": True,
                "show_stats": True
            }
        }

    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values."""
        try:
            self.config = self.get_default_config()
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            return False

    def export_config(self, filepath: str) -> bool:
        """Export configuration to file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False

    def import_config(self, filepath: str) -> bool:
        """Import configuration from file."""
        try:
            with open(filepath, 'r') as f:
                new_config = json.load(f)
            self.config = new_config
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False