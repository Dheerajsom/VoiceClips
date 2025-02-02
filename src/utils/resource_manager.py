# src/utils/resource_manager.py
import os
from pathlib import Path
from typing import Optional, Dict
import json
import logging

class ResourceManager:
    """Manages application resources and assets."""
    
    def __init__(self, resource_dir: str):
        self.logger = logging.getLogger(__name__)
        self.resource_dir = Path(resource_dir)
        self.cache: Dict = {}
        
        # Ensure resource directories exist
        self.ensure_directories()

    def ensure_directories(self):
        """Create necessary resource directories."""
        directories = [
            'icons',
            'themes',
            'locales',
            'plugins',
            'templates'
        ]
        
        for directory in directories:
            (self.resource_dir / directory).mkdir(parents=True, exist_ok=True)

    def get_icon(self, name: str) -> Optional[str]:
        """Get path to icon file."""
        try:
            icon_path = self.resource_dir / 'icons' / f"{name}.png"
            return str(icon_path) if icon_path.exists() else None
        except Exception as e:
            self.logger.error(f"Error loading icon {name}: {e}")
            return None

    def get_theme(self, name: str) -> Optional[Dict]:
        """Load theme configuration."""
        try:
            if name in self.cache:
                return self.cache[name]

            theme_file = self.resource_dir / 'themes' / f"{name}.json"
            if not theme_file.exists():
                return None

            with open(theme_file, 'r') as f:
                theme_data = json.load(f)
                self.cache[name] = theme_data
                return theme_data

        except Exception as e:
            self.logger.error(f"Error loading theme {name}: {e}")
            return None

    def get_locale(self, language: str) -> Optional[Dict]:
        """Load language translations."""
        try:
            locale_file = self.resource_dir / 'locales' / f"{language}.json"
            if not locale_file.exists():
                return None

            with open(locale_file, 'r') as f:
                return json.load(f)

        except Exception as e:
            self.logger.error(f"Error loading locale {language}: {e}")
            return None

    def list_themes(self) -> list:
        """List available themes."""
        try:
            theme_dir = self.resource_dir / 'themes'
            return [f.stem for f in theme_dir.glob('*.json')]
        except Exception as e:
            self.logger.error(f"Error listing themes: {e}")
            return []

    def list_locales(self) -> list:
        """List available language translations."""
        try:
            locale_dir = self.resource_dir / 'locales'
            return [f.stem for f in locale_dir.glob('*.json')]
        except Exception as e:
            self.logger.error(f"Error listing locales: {e}")
            return []

    def add_resource(self, resource_type: str, name: str, data: bytes) -> bool:
        """Add a new resource file."""
        try:
            resource_path = self.resource_dir / resource_type / name
            with open(resource_path, 'wb') as f:
                f.write(data)
            return True
        except Exception as e:
            self.logger.error(f"Error adding resource {name}: {e}")
            return False

    def remove_resource(self, resource_type: str, name: str) -> bool:
        """Remove a resource file."""
        try:
            resource_path = self.resource_dir / resource_type / name
            if resource_path.exists():
                resource_path.unlink()
            return True
        except Exception as e:
            self.logger.error(f"Error removing resource {name}: {e}")
            return False

    def clear_cache(self):
        """Clear resource cache."""
        self.cache.clear()