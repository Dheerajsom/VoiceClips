# tests/test_recording.py
import pytest
import time
from pathlib import Path

class TestRecording:
    def test_start_recording(self, recording_manager, temp_dir):
        """Test starting a recording."""
        assert not recording_manager.is_recording
        success = recording_manager.start_recording()
        assert success
        assert recording_manager.is_recording
        assert recording_manager.current_recording is not None
        recording_manager.stop_recording()

    def test_stop_recording(self, recording_manager):
        """Test stopping a recording."""
        recording_manager.start_recording()
        time.sleep(2)  # Record for 2 seconds
        success = recording_manager.stop_recording()
        assert success
        assert not recording_manager.is_recording
        assert recording_manager.current_recording is None

    def test_pause_resume(self, recording_manager):
        """Test pausing and resuming recording."""
        recording_manager.start_recording()
        assert recording_manager.toggle_pause()
        assert recording_manager.is_paused
        assert recording_manager.toggle_pause()
        assert not recording_manager.is_paused
        recording_manager.stop_recording()

    def test_recording_file_created(self, recording_manager, temp_dir):
        """Test that recording file is created."""
        recording_manager.start_recording()
        time.sleep(2)
        recording_manager.stop_recording()
        
        recordings = list(Path(temp_dir / "recordings").glob("*.mp4"))
        assert len(recordings) == 1
        assert recordings[0].stat().st_size > 0