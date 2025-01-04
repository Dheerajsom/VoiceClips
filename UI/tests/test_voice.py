import pytest
from src.voice.recognizer import VoiceRecognizer

def test_voice_recognition():
    recognizer = VoiceRecognizer()
    # Mock audio data needed for testing
    test_audio_data = 'path_to_test_audio_file.wav'  # You need to provide an actual audio file path
    result = recognizer.recognize(test_audio_data)
    assert "expected transcription" in result  # Replace with expected result
