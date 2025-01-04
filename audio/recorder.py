import pyaudio

class AudioRecorder:
    def __init__(self, settings):
        self.audio = pyaudio.PyAudio()
        self.settings = settings
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1,
                                      rate=self.settings['sample_rate'], input=True,
                                      frames_per_buffer=self.settings['chunk_size'])

    def record(self, duration):
        frames = []
        for _ in range(int(self.settings['sample_rate'] / self.settings['chunk_size'] * duration)):
            data = self.stream.read(self.settings['chunk_size'])
            frames.append(data)
        return b''.join(frames)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
