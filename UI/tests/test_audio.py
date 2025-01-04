import pytest
from src.audio.recorder import AudioRecorder
from src.config import AUDIO_SETTINGS

def test_audio_recording():
    recorder = AudioRecorder(AUDIO_SETTINGS)
    data = recorder.record(1)  # Record for 1 second
    assert len(data) > 0
    recorder.close()
