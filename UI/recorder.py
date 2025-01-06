import threading
import cv2
import numpy as np
import pyautogui
import wave
import pyaudio

class ScreenRecorder:
    def __init__(self, filename='output.mp4', fps=60.0, resolution=(1920, 1080), on_new_frame=None):
        self.filename = filename
        self.audio_output = self.filename.replace('.mp4', '.wav')  # Ensure audio file is .wav
        self.fps = fps
        self.resolution = resolution
        self.codec = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = None
        self.running = False
        self.lock = threading.Lock()
        self.on_new_frame = on_new_frame  # Callback function for GUI updates

        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []

        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16, channels=1,
                rate=44100, input=True, frames_per_buffer=1024
            )
        except OSError as e:
            print(f"Error: Unable to open audio stream. {e}")
            self.stream = None

    def start_recording(self):
        """Start recording the screen to a video file."""
        with self.lock:
            self.out = cv2.VideoWriter(self.filename, self.codec, self.fps, self.resolution)
            self.running = True

        if self.stream:
            audio_thread = threading.Thread(target=self.record_audio)
            audio_thread.start()
            print("Audio recording started...")

        while self.running:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, self.resolution)

            with self.lock:
                if self.out and self.running:
                    self.out.write(frame)
                    if self.on_new_frame:
                        self.on_new_frame(frame)  # Update frame in GUI

        self.stop_recording()

    def stop_recording(self):
        """Stop the recording."""
        with self.lock:
            self.running = False
            if self.out:
                self.out.release()
                self.out = None

            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.audio.terminate()
                self.save_audio()

        print("Recording stopped and saved successfully.")

    def record_audio(self):
        """Record audio concurrently while the video is being recorded."""
        while self.running:
            try:
                data = self.stream.read(1024, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f"Audio error: {e}")
                break

    def save_audio(self):
        """Save the recorded audio to a .wav file."""
        if not self.frames:
            print("No audio data to save.")
            return

        with wave.open(self.audio_output, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.frames))
        print(f"Audio saved to {self.audio_output}")

    def change_frame_rate(self, new_rate):
        """Change the frame rate dynamically."""
        with self.lock:
            self.fps = new_rate
            print(f"Frame rate changed to {self.fps} FPS")

    def start_recording_thread(self, status_label):
        """Start the recording in a separate thread to avoid blocking the GUI."""
        if not self.running:
            thread = threading.Thread(target=self.start_recording, daemon=True)
            thread.start()
            status_label.config(text="Status: Recording...")
        else:
            print("Recording is already in progress.")
