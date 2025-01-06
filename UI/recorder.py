import threading
import time
import cv2
import numpy as np
import pyautogui
import wave
import pyaudio
from moviepy import VideoFileClip, AudioFileClip

class ScreenRecorder:
    def __init__(self, filename='output.mp4', fps=30.0, resolution=(1920, 1080)):
        self.filename = filename
        self.audio_output = "temp_audio.wav"
        self.fps = fps
        self.resolution = resolution
        self.codec = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = None
        self.running = False
        self.audio_frames = []

        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16, channels=1,
                rate=44100, input=True, frames_per_buffer=1024
            )
        except OSError as e:
            print(f"Error: Unable to open audio stream. {e}")
            self.stream = None

    def start_recording(self):
        """Start recording the screen and audio."""
        self.out = cv2.VideoWriter(self.filename, self.codec, self.fps, self.resolution)
        self.running = True

        if self.stream:
            audio_thread = threading.Thread(target=self.record_audio)
            audio_thread.start()

        frame_interval = 1.0 / self.fps  # Frame capture interval in seconds

        print("Recording started...")
        while self.running:
            start_time = time.time()

            # Capture screen
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, self.resolution)
            self.out.write(frame)

            elapsed_time = time.time() - start_time
            time.sleep(max(0, frame_interval - elapsed_time))

        self.stop_recording()

    def stop_recording(self):
        """Stop recording and save video and audio."""
        self.running = False
        if self.out:
            self.out.release()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            self.save_audio()
            self.combine_audio_video()

        print("Recording stopped.")

    def record_audio(self):
        """Record audio while capturing video."""
        while self.running:
            data = self.stream.read(1024, exception_on_overflow=False)
            self.audio_frames.append(data)

    def save_audio(self):
        """Save recorded audio to a .wav file."""
        with wave.open(self.audio_output, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.audio_frames))
        print(f"Audio saved to {self.audio_output}")

    def combine_audio_video(self):
        """Combine video and audio into a single .mp4 file."""
        print("Combining audio and video...")
        video_clip = VideoFileClip(self.filename)
        audio_clip = AudioFileClip(self.audio_output)

        # Ensure the audio duration matches the video
        final_audio = audio_clip.set_duration(video_clip.duration)

        final_clip = video_clip.set_audio(final_audio)
        final_filename = self.filename.replace(".mp4", "_final.mp4")
        final_clip.write_videofile(final_filename, codec="libx264", audio_codec="aac")
        print(f"Final video saved as {final_filename}")

