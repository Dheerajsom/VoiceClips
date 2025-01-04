import threading
import cv2
import numpy as np
import pyautogui

class ScreenRecorder:
    def __init__(self, filename='output.avi', fps=12.0, resolution=(1920, 1080)):
        self.filename = filename
        self.fps = fps
        self.resolution = resolution
        self.codec = cv2.VideoWriter_fourcc(*'XVID')
        self.out = None
        self.running = False
        self.lock = threading.Lock()

    def start_recording(self):
        with self.lock:
            self.out = cv2.VideoWriter(self.filename, self.codec, self.fps, self.resolution)
            self.running = True
        while self.running:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, self.resolution)
            with self.lock:
                self.out.write(frame)

    def stop_recording(self):
        with self.lock:
            self.running = False
            if self.out:
                self.out.release()
                cv2.destroyAllWindows()
                print("Recording stopped.")

    def change_frame_rate(self, new_fps):
        with self.lock:
            self.fps = new_fps
            # Restart the video writer with new frame rate
            self.out = cv2.VideoWriter(self.filename, self.codec, self.fps, self.resolution)
            print(f"Frame rate changed to: {new_fps} fps")

