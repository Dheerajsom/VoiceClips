import pyaudio

def record_audio(duration=5, settings=None):
    if settings is None:
        settings = {
            'format': pyaudio.paInt16,
            'channels': 1,
            'rate': 44100,
            'frames_per_buffer': 1024,
        }
    audio = pyaudio.PyAudio()
    stream = audio.open(format=settings['format'], channels=settings['channels'],
                        rate=settings['rate'], input=True,
                        frames_per_buffer=settings['frames_per_buffer'])

    frames = []
    for i in range(0, int(settings['rate'] / settings['frames_per_buffer'] * duration)):
        data = stream.read(settings['frames_per_buffer'])
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    return b''.join(frames)
