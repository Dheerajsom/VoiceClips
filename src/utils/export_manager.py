# src/utils/export_manager.py
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import subprocess
from packaging import version
APP_VERSION = "1.0.0"

class ExportManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_formats = {
            'settings': ['json'],
            'scenes': ['json'],
            'clips': ['mp4', 'mov', 'mkv'],
            'recordings': ['mp4', 'mov', 'mkv']
        }

    def export_settings(self, settings: Dict, filepath: str) -> bool:
        """Export application settings."""
        try:
            data = {
                'version': APP_VERSION,
                'timestamp': datetime.now().isoformat(),
                'settings': settings
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting settings: {e}")
            return False

    def import_settings(self, filepath: str) -> Optional[Dict]:
        """Import application settings."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Validate version compatibility
            if 'version' in data:
                imported_version = version.parse(data['version'])
                current_version = version.parse(APP_VERSION)
                
                if imported_version.major > current_version.major:
                    raise ValueError("Settings file is from a newer version")
            
            return data.get('settings')
            
        except Exception as e:
            self.logger.error(f"Error importing settings: {e}")
            return None

    def export_scene_collection(self, scenes: List[Dict], filepath: str) -> bool:
        """Export scene collection."""
        try:
            data = {
                'version': APP_VERSION,
                'timestamp': datetime.now().isoformat(),
                'scenes': scenes
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting scenes: {e}")
            return False

    def export_clip(self, clip_path: str, output_path: str, 
                   format: str = 'mp4', settings: Dict = None) -> bool:
        """Export clip with optional transcoding."""
        try:
            if not settings:
                settings = self._get_default_export_settings(format)
            
            command = [
                'ffmpeg',
                '-i', clip_path,
                *settings['video_args'],
                *settings['audio_args'],
                '-y',
                output_path
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Error exporting clip: {e}")
            return False

    def _get_default_export_settings(self, format: str) -> Dict:
        """Get default export settings for format."""
        settings = {
            'mp4': {
                'video_args': [
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23'
                ],
                'audio_args': [
                    '-c:a', 'aac',
                    '-b:a', '192k'
                ]
            },
            'mov': {
                'video_args': [
                    '-c:v', 'prores_ks',
                    '-profile:v', '3',
                    '-vendor', 'apl0'
                ],
                'audio_args': [
                    '-c:a', 'pcm_s16le'
                ]
            },
            'mkv': {
                'video_args': [
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23'
                ],
                'audio_args': [
                    '-c:a', 'libvorbis',
                    '-q:a', '4'
                ]
            }
        }
        return settings.get(format, settings['mp4'])

    def export_recording(self, recording_path: str, output_path: str,
                        format: str = 'mp4', quality: str = 'high') -> bool:
        """Export recording with quality settings."""
        try:
            settings = self._get_quality_settings(quality, format)
            return self.export_clip(recording_path, output_path, format, settings)
        
        except Exception as e:
            self.logger.error(f"Error exporting recording: {e}")
            return False

    def _get_quality_settings(self, quality: str, format: str) -> Dict:
        """Get settings for quality level."""
        quality_presets = {
            'low': {
                'video_args': [
                    '-c:v', 'libx264',
                    '-preset', 'veryfast',
                    '-crf', '28'
                ],
                'audio_args': [
                    '-c:a', 'aac',
                    '-b:a', '128k'
                ]
            },
            'medium': {
                'video_args': [
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23'
                ],
                'audio_args': [
                    '-c:a', 'aac',
                    '-b:a', '192k'
                ]
            },
            'high': {
                'video_args': [
                    '-c:v', 'libx264',
                    '-preset', 'slow',
                    '-crf', '18'
                ],
                'audio_args': [
                    '-c:a', 'aac',
                    '-b:a', '320k'
                ]
            }
        }
        return quality_presets.get(quality.lower(), quality_presets['medium'])

    def validate_export_format(self, file_type: str, format: str) -> bool:
        """Validate if format is supported for file type."""
        return format in self.supported_formats.get(file_type, [])

    def get_supported_formats(self, file_type: str) -> List[str]:
        """Get supported formats for file type."""
        return self.supported_formats.get(file_type, [])