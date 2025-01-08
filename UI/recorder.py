import threading
import cv2
import numpy as np
import pyautogui
import pyaudio
import wave
import time
import os
import shutil

class ScreenRecorder:
    def __init__(self, filename='output.mp4', fps=60.0, resolution=(1920, 1080)):
        self.filename = filename
        self.temp_dir = os.path.join(os.path.dirname(filename), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.fps = fps
        self.resolution = resolution
        self.running = False
        self.audio_frames = []

        self.audio = pyaudio.PyAudio()
        self.audio_format = pyaudio.paInt16
        self.channels = 1  # Mono audio for better compatibility
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
        self.frame_interval = frame_interval
        
        temp_video = os.path.join(self.temp_dir, "temp_video.avi")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(temp_video, fourcc, self.fps, self.resolution)

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
                if current_time - last_frame_time >= self.frame_interval:
                    frame = np.array(pyautogui.screenshot())
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, self.resolution)
                    out.write(frame)
                    if update_gui_frame_callback:
                        update_gui_frame_callback(frame)
                    last_frame_time = current_time
        finally:
            self.stop_recording(out, temp_video)

    def stop_recording(self, video_writer=None, temp_video=None):
        self.running = False
        video_writer.release()

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

        # Detect file extension
        file_extension = os.path.splitext(self.filename)[-1].lower()

        try:
            if file_extension == ".mov":
            # MOV: Use H.264 (compatible codec)
                ffmpeg_cmd = f'ffmpeg -i "{temp_video}" -i "{temp_audio}" -c:v libx264 -c:a aac -async 1 -shortest "{self.filename}" -y'
            elif file_extension == ".mkv":
        # MKV: Standard H.264/AAC encoding
                ffmpeg_cmd = f'ffmpeg -i "{temp_video}" -i "{temp_audio}" -c:v libx264 -c:a aac -preset medium -crf 23 -async 1 -shortest "{self.filename}" -y'
            else:
        # MP4 or Default encoding
                ffmpeg_cmd = f'ffmpeg -i "{temp_video}" -i "{temp_audio}" -c:v libx264 -c:a aac -b:a 192k -async 1 -shortest "{self.filename}" -y'

            print(f"Running ffmpeg command:\n{ffmpeg_cmd}")
            exit_code = os.system(ffmpeg_cmd)

            if exit_code == 0:
                print(f"Recording saved as {self.filename}")
            else:
                raise Exception(f"FFmpeg failed with exit code {exit_code}")

        except Exception as e:
            print(f"Error saving {file_extension.upper()} file: {e}")
            # Fallback to MP4 if another format fails
            fallback_filename = self.filename.replace(file_extension, ".mp4")
            ffmpeg_cmd_fallback = f'ffmpeg -i "{temp_video}" -i "{temp_audio}" -c:v libx264 -c:a aac -async 1 "{fallback_filename}" -y'
            os.system(ffmpeg_cmd_fallback)
            print(f"Fallback: Saved as MP4 at {fallback_filename}")


        # Clean up temporary files after ffmpeg completes
        try:
            os.remove(temp_video)
            os.remove(temp_audio)
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error removing temp directory: {e}")