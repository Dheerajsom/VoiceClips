# Updated `clipper.py` with Automatic Model Path Handling and Error Resolution
import os
import time
from collections import deque
import threading
import subprocess
import vosk
import pyaudio

class Clipper:
    def __init__(self, buffer_duration=30, output_folder="clips", format="mp4", model_path=None):
        self.buffer_duration = buffer_duration  # Default duration (seconds)
        self.frames = deque(maxlen=buffer_duration * 30)  # Assuming 30 FPS
        self.recording = False
        self.output_folder = output_folder
        self.format = format
        self.is_listening = False

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        # Automatically set model path if not provided
        if model_path is None:
            default_model_path = os.path.expanduser("~/Downloads/vosk-model-en-us-0.22")
            if os.path.isdir(default_model_path):
                model_path = default_model_path
                print(f"Using default model path: {model_path}")
            else:
                raise FileNotFoundError("Vosk model path is invalid or not found. Please download a model and place it in ~/Downloads or specify a custom path.")

        try:
            self.model = vosk.Model(model_path)
        except Exception as e:
            raise Exception(f"Failed to load Vosk model: {str(e)}")

        self.audio_stream = pyaudio.PyAudio()

    def set_save_location(self, folder_path):
        """Set the save directory for clips."""
        self.output_folder = folder_path
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def set_file_format(self, format):
        """Set the file format for clips (mp4, mov, mkv, etc.)."""
        self.format = format.lower()

    def start_buffering(self):
        """Starts buffering frames."""
        self.recording = True
        self.frames.clear()

    def stop_buffering(self):
        """Stops buffering frames."""
        self.recording = False

    def add_frame(self, frame):
        """Adds frames to the buffer if recording."""
        if self.recording:
            self.frames.append(frame)

    def save_clip(self, clip_duration):
        """Saves the last `clip_duration` seconds as a video with audio."""
        frames_to_save = min(len(self.frames), clip_duration * 30)
        if frames_to_save <= 0:
            print("Not enough buffered frames to save a clip.")
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(self.output_folder, f"clip_{timestamp}.{self.format}")
        temp_audio_file = os.path.join(self.output_folder, "temp_audio.wav")

        # Record audio for synchronization with video
        audio_stream = self.audio_stream.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
        audio_frames = []

        print("Recording audio while saving the clip...")
        for _ in range(0, int(16000 / 4096 * clip_duration)):
            data = audio_stream.read(4096, exception_on_overflow=False)
            audio_frames.append(data)

        audio_stream.stop_stream()
        audio_stream.close()

        with open("temp_buffer.yuv", "wb") as temp_file:
            for frame in list(self.frames)[-frames_to_save:]:
                temp_file.write(frame)

        with open(temp_audio_file, "wb") as audio_file:
            audio_file.write(b"".join(audio_frames))

        # Combine video and audio into the chosen format
        ffmpeg_command = [
            "ffmpeg", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", "1920x1080",
            "-r", "30", "-i", "temp_buffer.yuv", "-f", "wav", "-i", temp_audio_file,
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k",
            output_filename
        ]

        subprocess.run(ffmpeg_command)
        os.remove("temp_buffer.yuv")
        os.remove(temp_audio_file)
        print(f"Clip saved: {output_filename}")

    def listen_for_clips(self):
        """Continuously listens for clip commands."""
        stream = self.audio_stream.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
        recognizer = vosk.KaldiRecognizer(self.model, 16000)

        print("Listening for 'clip' command...")
        self.is_listening = True

        while self.is_listening:
            data = stream.read(4096, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                command = eval(result).get("text", "").lower()
                print(f"Recognized text: {command}")
                if "clip" in command:
                    self.save_clip(self.buffer_duration)
                    print("Clip command detected and video clip saved with audio.")

        stream.stop_stream()
        stream.close()

    def start_listening(self):
        """Starts the speech recognition in a new thread."""
        threading.Thread(target=self.listen_for_clips, daemon=True).start()

    def stop_listening(self):
        """Stops listening for speech commands."""
        self.is_listening = False

if __name__ == "__main__":
    try:
        clipper = Clipper()
        clipper.start_listening()
        input("Press Enter to stop listening...")
        clipper.stop_listening()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please download a Vosk model and place it in the ~/Downloads directory or specify a valid path.")
