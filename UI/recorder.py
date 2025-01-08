import threading
import cv2
import numpy as np
import pyautogui
import pyaudio
import wave
import time
import os
import shutil
from moviepy import VideoFileClip, AudioFileClip

class ScreenRecorder:
    def __init__(self, filename='output.mp4', fps=30.0, resolution=(1920, 1080)):
        self.filename = filename
        self.temp_dir = os.path.join(os.path.dirname(filename), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)

        self.fps = fps
        self.resolution = resolution
        self.running = False
        self.audio_frames = []

        self.audio = pyaudio.PyAudio()
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.sample_rate = 44100
        self.chunk_size = 1024 * 2

        try:
            self.audio_stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            print(f"Error: Unable to open audio stream: {e}")
            self.audio_stream = None

    def start_recording(self, update_gui_frame_callback=None):
        self.running = True
        frame_interval = 1.0 / self.fps  # Time between frames
        self.frame_interval = frame_interval

        temp_video = os.path.join(self.temp_dir, "temp_video.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video, fourcc, self.fps, self.resolution)

        if not out.isOpened():
            print("Error: Unable to open video writer.")
            return

        def record_audio():
            while self.running and self.audio_stream:
                try:
                    audio_data = self.audio_stream.read(self.chunk_size)
                    self.audio_frames.append(audio_data)
                except Exception as e:
                    print(f"Error recording audio: {e}")
                    break

        audio_thread = threading.Thread(target=record_audio, daemon=True)
        audio_thread.start()

        last_frame_time = time.time()

        try:
            while self.running:
                current_time = time.time()
                if current_time - last_frame_time >= frame_interval:
                    frame = np.array(pyautogui.screenshot())
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, self.resolution)
                    out.write(frame)
                    if update_gui_frame_callback:
                        update_gui_frame_callback(frame)
                    last_frame_time = current_time
        finally:
            if out:
                out.release()  # Release the video writer
            self.stop_recording(temp_video)

    def stop_recording(self, temp_video=None):
        self.running = False

        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio.terminate()

        temp_audio = os.path.join(self.temp_dir, "temp_audio.wav")
        with wave.open(temp_audio, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(self.audio_frames))

        file_extension = os.path.splitext(self.filename)[-1].lower()

        try:
            video_clip = VideoFileClip(temp_video).with_fps(self.fps)
            audio_clip = AudioFileClip(temp_audio)
            final_clip = video_clip.with_audio(audio_clip)  # Correct way to set audio

            # Write output based on selected file type
            if file_extension in [".mp4", ".mov", ".mkv"]:
                final_clip.write_videofile(self.filename, codec='libx264', audio_codec='aac', fps=self.fps)
            else:
                raise Exception(f"Unsupported format: {file_extension}")

            print(f"Recording saved as {self.filename}")

        except Exception as e:
            print(f"Error saving {file_extension.upper()} file: {e}")
            fallback_filename = self.filename.replace(file_extension, ".mp4")
            if 'final_clip' in locals():
                final_clip.write_videofile(fallback_filename, codec='libx264', audio_codec='aac', fps=self.fps)
                print(f"Fallback: Saved as MP4 at {fallback_filename}")

        finally:
            if 'video_clip' in locals():
                video_clip.close()
            if 'audio_clip' in locals():
                audio_clip.close()

        # Clean up temporary files after saving
        try:
            os.remove(temp_video)
            os.remove(temp_audio)
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error removing temp directory: {e}")
