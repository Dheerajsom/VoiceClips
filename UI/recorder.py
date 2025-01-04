import threading
import cv2
import numpy as np
import pyautogui
from threading import Thread

class ScreenRecorder:
    def __init__(self, filename='output.avi', fps=60.0, resolution=(1920, 1080), on_new_frame=None):
        self.filename = filename
        self.fps = fps
        self.resolution = resolution
        self.codec = cv2.VideoWriter_fourcc(*'XVID')
        self.out = None
        self.running = False
        self.lock = threading.Lock()
        self.on_new_frame = on_new_frame  # Callback function for handling new frames

    def start_recording(self):
        """Start recording the screen to a video file."""
        with self.lock:
            self.out = cv2.VideoWriter(self.filename, self.codec, self.fps, self.resolution)
            self.running = True
        
        while self.running:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, self.resolution)
            with self.lock:
                if self.out is not None and self.running:
                    self.out.write(frame)
                    if self.on_new_frame:
                        self.on_new_frame(frame)  # Call the callback with the new frame

    def stop_recording(self):
        """Stop the recording."""
        with self.lock:
            self.running = False
            if self.out:
                self.out.release()
                self.out = None
                cv2.destroyAllWindows()
                print("Recording stopped.")

    def change_frame_rate(self, new_rate):
        """Change the frame rate of the recording."""
        with self.lock:
            self.fps = new_rate
            if self.out:
                self.out.release()  # Restart the video writer with new frame rate
                self.out = cv2.VideoWriter(self.filename, self.codec, self.fps, self.resolution)

    def start_recording_thread(self, status_label):
        """Start the recording in a separate thread to avoid blocking the GUI."""
        if not self.running:
            thread = Thread(target=self.start_recording)
            thread.start()
            status_label.config(text="Status: Recording...")
        else:
            print("Recording is already in progress.")
