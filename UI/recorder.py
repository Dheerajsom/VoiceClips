import threading
import cv2
import numpy as np
import pyaudio
import wave
import time
import os
import shutil
import mss

class ScreenRecorder:
    def __init__(self, filename='output.mp4', fps=30.0, resolution=(1920, 1080)):
        self.filename = filename
        self.temp_dir = os.path.join(os.path.dirname(filename), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.fps = fps
        self.resolution = resolution
        self.running = False
        self.audio_frames = []
        self.video_writer = None

        self.audio = pyaudio.PyAudio()
        self.audio_format = pyaudio.paInt16
        self.channels = 1  # Mono audio for compatibility
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
        frame_interval = 1.0 / self.fps

        temp_video = os.path.join(self.temp_dir, "temp_video.avi")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(temp_video, fourcc, self.fps, self.resolution)

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

        with mss.mss() as sct:  # Use mss for faster screen capture
            monitor = {"top": 0, "left": 0, "width": self.resolution[0], "height": self.resolution[1]}
            try:
                while self.running:
                    start_time = time.time()
                    frame = np.array(sct.grab(monitor))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    frame = cv2.resize(frame, self.resolution)
                    self.video_writer.write(frame)
                    if update_gui_frame_callback:
                        update_gui_frame_callback(frame)

                    # Sleep to maintain frame capture rate
                    elapsed_time = time.time() - start_time
                    sleep_time = max(0, frame_interval - elapsed_time)
                    time.sleep(sleep_time)
            finally:
                if self.video_writer:
                    self.video_writer.release()  # Ensure video_writer is released
                self.stop_recording()

    def stop_recording(self):
        if not self.running:
            return

        self.running = False

        if self.video_writer is not None:
            self.video_writer.release()

        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio.terminate()

        temp_video = os.path.join(self.temp_dir, "temp_video.avi")
        temp_audio = os.path.join(self.temp_dir, "temp_audio.wav")
        with wave.open(temp_audio, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(self.audio_frames))

        file_extension = os.path.splitext(self.filename)[-1].lower()
        try:
            if file_extension == ".mov":
                # MOV: Use compatible codecs
                ffmpeg_cmd = f'ffmpeg -i "{temp_video}" -i "{temp_audio}" -c:v libx264 -c:a aac "{self.filename}" -y'
            elif file_extension == ".mkv":
                # MKV: Standard H.264/AAC encoding
                ffmpeg_cmd = f'ffmpeg -i "{temp_video}" -i "{temp_audio}" -c:v libx264 -c:a aac -preset medium -crf 23 "{self.filename}" -y'
            else:
                # MP4 or Default encoding
                ffmpeg_cmd = f'ffmpeg -i "{temp_video}" -i "{temp_audio}" -c:v libx264 -c:a aac -b:a 192k -shortest "{self.filename}" -y'

            print(f"Running ffmpeg command:\n{ffmpeg_cmd}")
            exit_code = os.system(ffmpeg_cmd)

            if exit_code == 0:
                print(f"Recording saved as {self.filename}")
            else:
                raise Exception(f"FFmpeg failed with exit code {exit_code}")

        except Exception as e:
            print(f"Error saving {file_extension.upper()} file: {e}")
            fallback_filename = self.filename.replace(file_extension, ".mp4")
            ffmpeg_cmd_fallback = f'ffmpeg -i "{temp_video}" -i "{temp_audio}" -c:v libx264 -c:a aac "{fallback_filename}" -y'
            os.system(ffmpeg_cmd_fallback)
            print(f"Fallback: Saved as MP4 at {fallback_filename}")

        try:
            os.remove(temp_video)
            os.remove(temp_audio)
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error removing temp directory: {e}")
