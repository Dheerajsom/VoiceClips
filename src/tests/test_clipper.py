# tests/test_clipper.py
import pytest
import time
import numpy as np

class TestClipper:
    def test_voice_detection(self, clipper):
        """Test voice command detection."""
        clipper.start_listening()
        time.sleep(1)  # Allow time for initialization
        assert clipper.is_listening
        clipper.stop_listening()
        assert not clipper.is_listening

    def test_clip_creation(self, clipper, temp_dir):
        """Test clip creation."""
        # Simulate frame buffer
        frame_size = (1920, 1080, 3)
        for _ in range(30 * 30):  # 30 seconds at 30 fps
            frame = np.random.randint(0, 255, frame_size, dtype=np.uint8)
            clipper.frame_buffer.append(frame.tobytes())

        # Create clip
        clipper.save_clip()
        
        clips = list(Path(temp_dir / "clips").glob("*.mp4"))
        assert len(clips) == 1
        assert clips[0].stat().st_size > 0

    def test_buffer_management(self, clipper):
        """Test buffer management."""
        # Fill buffer
        frame_size = (1920, 1080, 3)
        for _ in range(35 * 30):  # Overflow the 30-second buffer
            frame = np.random.randint(0, 255, frame_size, dtype=np.uint8)
            clipper.frame_buffer.append(frame.tobytes())

        # Check buffer size
        assert len(clipper.frame_buffer) == 30 * 30  # Should maintain 30 seconds