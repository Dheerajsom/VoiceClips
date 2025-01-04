import cv2
import numpy as np
import pyautogui

class ScreenRecorder:
    def __init__(self, filename='output.avi', fps=12.0, resolution=(1920, 1080)):
        """Initialize the screen recorder with the filename, fps, and resolution."""
        self.filename = filename
        self.fps = fps
        self.resolution = resolution
        self.codec = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(self.filename, self.codec, self.fps, self.resolution)

    def record_screen(self, duration):
        """Record the screen for a given duration in seconds."""
        print("Recording started...")
        for _ in range(int(self.fps * duration)):
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, self.resolution)
            self.out.write(frame)
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.stop_recording()

    def stop_recording(self):
        """Stop the recording and release resources."""
        self.out.release()
        cv2.destroyAllWindows()
        print("Recording stopped.")

# Example usage
if __name__ == "__main__":
    recorder = ScreenRecorder(filename='test_video.avi', fps=10, resolution=(1366, 768))
    recorder.record_screen(duration=10)

