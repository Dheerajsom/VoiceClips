# tests/conftest.py
import pytest
import os
import tempfile
from pathlib import Path
from src.utils.config_manager import ConfigManager
from src.utils.platform_utils import PlatformManager
from src.features.recording import RecordingManager
from src.clipper import Clipper

@pytest.fixture
def temp_dir():
    """Provide temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def config(temp_dir):
    """Provide test configuration."""
    config_file = temp_dir / "config.json"
    config = ConfigManager(str(config_file))
    config.update({
        "recording": {
            "save_path": str(temp_dir / "recordings"),
            "format": "mp4"
        },
        "clipping": {
            "save_path": str(temp_dir / "clips"),
            "duration": 30,
            "format": "mp4"
        }
    })
    return config

@pytest.fixture
def platform_manager():
    """Provide platform manager."""
    return PlatformManager()

@pytest.fixture
def recording_manager(config):
    """Provide recording manager."""
    return RecordingManager(config)

@pytest.fixture
def clipper(config):
    """Provide clipper instance."""
    return Clipper(
        output_folder=config.get("clipping.save_path"),
        buffer_duration=config.get("clipping.duration"),
        format=config.get("clipping.format")
    )