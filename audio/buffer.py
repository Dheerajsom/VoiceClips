from collections import deque

class AudioBuffer:
    def __init__(self, maxsize=100):
        self.buffer = deque(maxlen=maxsize)

    def add(self, data):
        self.buffer.append(data)

    def get_all(self):
        return list(self.buffer)

    def clear(self):
        self.buffer.clear()
