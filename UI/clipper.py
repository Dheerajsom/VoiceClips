import os
import time
from collections import deque
import threading
import subprocess
import vosk
import pyaudio
from rapidfuzz import fuzz
import platform
import wave
import io
from PIL import Image
from utils import list_available_audio_devices, get_macos_devices
class Clipper:
    def __init__(self, buffer_duration=30, output_folder="clips", format="mp4", model_path=None):
        self.buffer_duration = buffer_duration
        self.output_folder = os.path.expanduser(output_folder)  # Expand user path
        self.format = format.lower()  # Ensure lowercase format
        self.is_listening = False
        self.frame_buffer = None
        self.audio_buffer = None
        self.clip_counter = 0
        self.lock = threading.Lock()

        # Create output folder if it doesn't exist
        os.makedirs(self.output_folder, exist_ok=True)

        # Vosk model setup
        if model_path is None:
            default_model_path = os.path.expanduser("~/Downloads/vosk-model-en-us-0.22")
            if os.path.isdir(default_model_path):
                model_path = default_model_path
                print(f"Using default model path: {model_path}")
            else:
                raise FileNotFoundError("Vosk model path is invalid or not found.")

        try:
            self.model = vosk.Model(model_path)
            self.audio_stream = pyaudio.PyAudio()
        except Exception as e:
            raise Exception(f"Failed to initialize: {str(e)}")

    def set_buffers(self, frame_buffer, audio_buffer):
        """Set the frame and audio buffers from the main app"""
        self.frame_buffer = frame_buffer
        self.audio_buffer = audio_buffer

    def set_save_location(self, folder_path):
        """Set the save directory for clips."""
        self.output_folder = folder_path
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def set_file_format(self, format):
        """Set the file format for clips (mp4, mov, mkv, etc.)."""
        self.format = format.lower()

    def save_clip(self):
        """Save the buffered content as a clip"""
        with self.lock:
            if not self.frame_buffer or len(self.frame_buffer) == 0:
                print("No frames to save")
                return

            self.clip_counter += 1
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # Create output filename
            output_filename = os.path.join(
                self.output_folder, 
                f"clip_{timestamp}_{self.clip_counter}.{self.format.lower()}"
            )
            
            print(f"Saving clip to: {output_filename}")

            # Get system-specific FFmpeg command
            system = platform.system()
            
            if system == "Darwin":  # macOS
                command = [
                    "ffmpeg",
                    "-f", "avfoundation",
                    "-framerate", "30",
                    "-video_size", "1920x1080",  # Adjust based on your screen size
                    "-capture_cursor", "1",
                    "-capture_mouse_clicks", "1",
                    "-i", "1:0",  # Screen:Audio device
                    "-t", str(self.buffer_duration),  # Duration of the clip
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-strict", "experimental",
                    "-y",
                    output_filename
                ]
            elif system == "Linux":
                command = [
                    "ffmpeg",
                    "-f", "x11grab",
                    "-r", "30",
                    "-s", "1920x1080",
                    "-i", ":0.0",
                    "-f", "pulse",
                    "-i", "default",
                    "-t", str(self.buffer_duration),
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-y",
                    output_filename
                ]
            else:  # Windows
                audio_devices = list_available_audio_devices()
                selected_audio_device = audio_devices[0] if "None" not in audio_devices else None
                
                command = [
                    "ffmpeg",
                    "-f", "gdigrab",
                    "-framerate", "30",
                    "-video_size", "1920x1080",
                    "-i", "desktop",
                ]

                # Add audio input
                if selected_audio_device:
                    command.extend([
                        "-f", "dshow",
                        "-i", f"audio={selected_audio_device}"
                    ])
                else:
                    command.extend([
                        "-f", "lavfi",
                        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"
                    ])

                # Add output options
                command.extend([
                    "-t", str(self.buffer_duration),
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p",
                    "-profile:v", "baseline",
                    "-level", "3.0",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-y",
                    output_filename
                ])

            try:
                print(f"Running FFmpeg command: {' '.join(command)}")
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                print(f"Clip saved successfully: {output_filename}")
                
            except subprocess.CalledProcessError as e:
                print(f"Error saving clip: {e}")
                if e.stderr:
                    print(f"FFmpeg error: {e.stderr}")
            except Exception as e:
                print(f"Error saving clip: {e}")
    def listen_for_clips(self):
        """Continuously listens for clip commands."""
        try:
            # Configure audio stream for optimal voice recognition
            stream = self.audio_stream.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=2048,  # Reduced buffer size for better responsiveness
                input_device_index=None,  # Use default input device
                stream_callback=None
            )
            
            recognizer = vosk.KaldiRecognizer(self.model, 16000)
            print("\nVoice Command System Active - Listening for 'clip' command...")
            print("----------------------------------------")
            
            self.is_listening = True
            recent_commands = deque(maxlen=3)  # Store recent commands to prevent duplicates
            last_clip_time = 0  # To prevent multiple clips in quick succession

            while self.is_listening:
                try:
                    data = stream.read(2048, exception_on_overflow=False)
                    if recognizer.AcceptWaveform(data):
                        result = eval(recognizer.Result())
                        recognized_text = result.get("text", "").lower().strip()
                        
                        # Only process if we have meaningful text
                        if recognized_text and len(recognized_text) > 1:
                            # Clean up the text
                            cleaned_text = ' '.join(
                                word for word in recognized_text.split()
                                if len(word) > 1 and  # Ignore single characters
                                word not in ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to']  # Ignore common words
                            )
                            
                            if cleaned_text:
                                print(f"Heard: {cleaned_text}")
                                
                                # Check for clip command
                                current_time = time.time()
                                clip_words = ['clip', 'clips', 'clipped', 'click', 'quick','cli','clis']
                                
                                # Direct match check
                                clip_detected = any(word in cleaned_text for word in clip_words)
                                
                                # Fuzzy match check if no direct match
                                if not clip_detected:
                                    for word in cleaned_text.split():
                                        ratio = fuzz.ratio("clip", word)
                                        if ratio > 40:  # High threshold for accuracy
                                            clip_detected = True
                                            print(f"Fuzzy match: '{word}' matches 'clip' with {ratio}% confidence")
                                            break
                                
                                # Process clip command if detected
                                if clip_detected:
                                    # Check if enough time has passed since last clip
                                    if current_time - last_clip_time > 2.0:  # 2-second cooldown
                                        if cleaned_text not in recent_commands:
                                            print("\n🎬 Clip command detected! Creating clip...\n")
                                            threading.Thread(target=self.save_clip).start()
                                            last_clip_time = current_time
                                            recent_commands.append(cleaned_text)
                                        else:
                                            print("Duplicate command ignored")
                                    else:
                                        print("Please wait before creating another clip")

                except Exception as e:
                    print(f"Error processing audio: {e}")
                    
        except Exception as e:
            print(f"Error in speech recognition: {e}")
        finally:
            if 'stream' in locals():
                stream.stop_stream()
                stream.close()
            print("\nVoice Command System Stopped")
    def start_listening(self):
        """Starts the speech recognition in a new thread."""
        threading.Thread(target=self.listen_for_clips, daemon=True).start()

    def stop_listening(self):
        """Stops listening for speech commands."""
        self.is_listening = False