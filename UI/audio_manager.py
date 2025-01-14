from utils import list_available_audio_devices

class AudioControl:
    def __init__(self):
        self.audio_sources = list_available_audio_devices()
        self.current_volume = 100

    def set_volume(self, volume):
        self.current_volume = volume
        print(f"Audio volume set to {volume}%")
