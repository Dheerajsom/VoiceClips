# src/clipper.py

import os
import sys
from pathlib import Path
import time
import threading
import subprocess
import vosk
import pyaudio
import wave
import logging
from typing import Optional, List, Dict, Tuple
from collections import deque
from datetime import datetime
from rapidfuzz import fuzz
import numpy as np
from pynput import keyboard
from plyer import notification

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.constants import *
from src.utils.audio_manager import AudioManager
from src.utils.video_manager import VideoManager
from src.utils.error_handler import ErrorHandler

class Clipper:
    """Manages video clipping functionality."""
    
    def __init__(self, buffer_duration: int = DEFAULT_CLIP_DURATION,
                 output_folder: str = DEFAULT_CLIPS_FOLDER,
                 format: str = DEFAULT_CLIP_FORMAT):
        
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)
        
        self.setup_clipper(buffer_duration, output_folder, format)
        self.initialize_voice_recognition()
        self.setup_hotkey()
        
        # Initialize managers
        self.audio_manager = AudioManager()
        self.video_manager = VideoManager()
        
        # Statistics
        self.clips_created = 0
        self.last_clip_time = 0
        self.clip_durations = []
        
        # Buffer synchronization
        self.sync_lock = threading.Lock()
        self.last_frame_timestamp = 0
        self.frame_interval = 1.0 / DEFAULT_FPS

    def setup_clipper(self, buffer_duration: int, output_folder: str, format: str):
        """Initialize clipper settings and buffers."""
        try:
            self.buffer_duration = buffer_duration
            self.output_folder = Path(output_folder)
            self.format = format.lower()
            self.is_listening = False
            self.clip_counter = 0
            self.lock = threading.Lock()

            # Create frame and audio buffers
            buffer_size = int(buffer_duration * DEFAULT_FPS)
            self.frame_buffer = deque(maxlen=buffer_size)
            self.audio_buffer = deque(maxlen=int(buffer_duration * AUDIO_SAMPLE_RATE * AUDIO_CHANNELS))

            # Ensure output directory exists
            self.output_folder.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(
                f"Clipper initialized: duration={buffer_duration}s, "
                f"format={format}, output={output_folder}"
            )

        except Exception as e:
            self.error_handler.handle_error(e, context="Clipper setup")
            raise

    def initialize_voice_recognition(self):
        """Setup voice recognition system."""
        try:
            model_path = self.find_vosk_model()
            self.model = vosk.Model(model_path)
            self.audio_stream = pyaudio.PyAudio()
            
            # Configure recognition settings
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            self.recent_commands = deque(maxlen=5)
            
            self.logger.info("Voice recognition initialized successfully")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Voice recognition setup")
            raise

    def find_vosk_model(self) -> str:
        """Locate Vosk model directory."""
        model_paths = [
            Path.home() / "vosk-model-en-us-0.22",
            Path.home() / "Downloads" / "vosk-model-en-us-0.22",
            Path(__file__).parent.parent / "models" / "vosk-model-en-us-0.22"
        ]
        
        for path in model_paths:
            if path.is_dir():
                return str(path)
                
        raise FileNotFoundError("Vosk model not found. Please download and install it.")

    def set_managers(self, video_manager, audio_mixer):
        """Set video and audio managers."""
        self.video_manager = video_manager
        self.audio_mixer = audio_mixer
        self._initialize_buffers()

    def _initialize_buffers(self):
        """Initialize capture buffers."""
        try:
            # Calculate buffer sizes
            video_buffer_size = int(self.buffer_duration * DEFAULT_FPS)
            audio_buffer_size = int(self.buffer_duration * AUDIO_SAMPLE_RATE)
            
            # Create buffers
            self.frame_buffer = deque(maxlen=video_buffer_size)
            self.audio_buffer = deque(maxlen=audio_buffer_size)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Initializing buffers")
    def setup_hotkey(self):
        """Setup keyboard shortcut for clipping."""
        try:
            # Parse the hotkey string
            hotkey_str = DEFAULT_CLIP_HOTKEY.replace('Ctrl', '<ctrl>')
            
            self.hotkey = keyboard.GlobalHotKeys({
                hotkey_str: self._handle_clip_command
            })
            self.hotkey.start()
            self.logger.info(f"Hotkey {DEFAULT_CLIP_HOTKEY} registered successfully")
        except Exception as e:
            self.error_handler.handle_error(e, context="Hotkey setup")

    def start_listening(self):
        """Start voice command detection."""
        if self.is_listening:
            return
            
        self.is_listening = True
        self.listen_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self.listen_thread.start()
        self.logger.info("Voice command detection started")

    def stop_listening(self):
        """Stop voice command detection."""
        self.is_listening = False
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join()
        self.logger.info("Voice command detection stopped")

    def _listen_loop(self):
        """Main voice detection loop."""
        try:
            stream = self.audio_stream.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4096
            )
            
            while self.is_listening:
                try:
                    data = stream.read(4096, exception_on_overflow=False)
                    if self.recognizer.AcceptWaveform(data):
                        result = eval(self.recognizer.Result())
                        text = result.get("text", "").lower()
                        
                        if text:
                            self.logger.debug(f"Recognized: {text}")
                            if self._should_create_clip(text):
                                self._handle_clip_command()
                                
                except Exception as e:
                    self.error_handler.handle_error(e, context="Audio processing")
                    
        except Exception as e:
            self.error_handler.handle_error(e, context="Voice recognition loop")
        finally:
            stream.stop_stream()
            stream.close()
    def _should_create_clip(self, text: str) -> bool:
        """Determine if a clip should be created based on voice input."""
        # Prevent rapid clips
        if time.time() - self.last_clip_time < 2.0:
            return False
            
        # Check recent commands to prevent duplicates
        if text in self.recent_commands:
            return False
            
        # Check for clip commands
        for command in VOICE_COMMANDS["clip"]:
            if command in text:
                return True
            
            # Fuzzy matching for similar commands
            words = text.split()
            if any(fuzz.ratio(command, word) > VOICE_COMMAND_SIMILARITY_THRESHOLD 
                   for word in words):
                return True
                
        return False

    def _handle_clip_command(self):
        """Handle clip creation command."""
        self.logger.info("Clip command detected")
        threading.Thread(target=self.save_clip).start()
        self.recent_commands.append("clip")
        self.last_clip_time = time.time()

    def add_frame(self, frame: np.ndarray, timestamp: float):
        """Add a frame to the buffer with timestamp."""
        with self.sync_lock:
            try:
                # Ensure frame timing is consistent
                if self.last_frame_timestamp > 0:
                    expected_time = self.last_frame_timestamp + self.frame_interval
                    if abs(timestamp - expected_time) > self.frame_interval * 0.5:
                        self.logger.warning("Frame timing inconsistency detected")
                
                self.frame_buffer.append({
                    'data': frame.copy(),
                    'timestamp': timestamp
                })
                self.last_frame_timestamp = timestamp
                
            except Exception as e:
                self.error_handler.handle_error(e, context="Adding frame to buffer")

    def add_audio(self, audio_data: bytes, timestamp: float):
        """Add audio data to the buffer with timestamp."""
        with self.sync_lock:
            try:
                self.audio_buffer.append({
                    'data': audio_data,
                    'timestamp': timestamp
                })
            except Exception as e:
                self.error_handler.handle_error(e, context="Adding audio to buffer")

    def save_clip(self) -> bool:
        """Save the buffered content as a clip."""
        with self.lock:
            if not self.frame_buffer:
                self.logger.warning("No frames to save")
                return False

            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.clip_counter += 1
                
                output_path = self.output_folder / f"clip_{timestamp}_{self.clip_counter}.{self.format}"
                self.logger.info(f"Saving clip to: {output_path}")
                
                # Create temporary files
                temp_video = self._save_temp_video(timestamp)
                temp_audio = self._save_temp_audio(timestamp)
                
                # Combine video and audio
                if self._combine_video_audio(temp_video, temp_audio, output_path):
                    self.clips_created += 1
                    clip_duration = len(self.frame_buffer) / DEFAULT_FPS
                    self.clip_durations.append(clip_duration)
                    self.show_notification(SUCCESS_MESSAGES["clip_created"])
                    return True
                    
                return False
                
            except Exception as e:
                self.error_handler.handle_error(e, context="Saving clip")
                return False
            finally:
                self._cleanup_temp_files(temp_video, temp_audio)

    def _save_temp_video(self, timestamp: str) -> Path:
        """Save temporary video file."""
        temp_video = self.output_folder / f"temp_video_{timestamp}.raw"
        try:
            with self.sync_lock:
                with open(temp_video, 'wb') as f:
                    for frame_data in self.frame_buffer:
                        f.write(frame_data['data'].tobytes())
            return temp_video
        except Exception as e:
            self.error_handler.handle_error(e, context="Saving temporary video")
            raise

    def _save_temp_audio(self, timestamp: str) -> Path:
        """Save temporary audio file."""
        temp_audio = self.output_folder / f"temp_audio_{timestamp}.wav"
        try:
            with self.sync_lock:
                if self.audio_buffer:
                    with wave.open(str(temp_audio), 'wb') as wf:
                        wf.setnchannels(AUDIO_CHANNELS)
                        wf.setsampwidth(2)  # 16-bit audio
                        wf.setframerate(AUDIO_SAMPLE_RATE)
                        audio_data = b''.join([data['data'] for data in self.audio_buffer])
                        wf.writeframes(audio_data)
            return temp_audio
        except Exception as e:
            self.error_handler.handle_error(e, context="Saving temporary audio")
            raise

    def _combine_video_audio(self, temp_video: Path, temp_audio: Path, 
                           output_path: Path) -> bool:
        """Combine video and audio into final clip."""
        try:
            command = self._create_ffmpeg_command(temp_video, temp_audio, output_path)
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"Clip saved successfully: {output_path}")
                return True
            else:
                raise Exception(f"FFmpeg error: {result.stderr}")
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Combining video and audio")
            return False

    def _create_ffmpeg_command(self, temp_video: Path, temp_audio: Path, 
                             output_path: Path) -> List[str]:
        """Create FFmpeg command for combining video and audio."""
        width, height = map(int, BASE_CANVAS_RESOLUTION.split('x'))
        
        command = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}',
            '-pix_fmt', 'rgb24',
            '-framerate', str(DEFAULT_FPS),
            '-i', str(temp_video)
        ]
        
        if temp_audio.exists():
            command.extend([
                '-i', str(temp_audio),
                '-c:a', 'aac',
                '-b:a', '192k'
            ])

        command.extend([
            '-c:v', 'h264',
            '-preset', DEFAULT_VIDEO_PRESET,
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-y',
            str(output_path)
        ])
        
        return command

    def _cleanup_temp_files(self, *files: Path):
        """Clean up temporary files."""
        for file in files:
            try:
                if file and file.exists():
                    file.unlink()
            except Exception as e:
                self.error_handler.handle_error(e, context=f"Cleaning up {file}")

    def show_notification(self, message: str):
        """Show system notification."""
        try:
            notification.notify(
                title=APP_NAME,
                message=message,
                app_icon=None,
                timeout=2
            )
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")

    def update_settings(self, settings: Dict):
        """Update clipper settings."""
        try:
            if "duration" in settings:
                self.buffer_duration = settings["duration"]
                # Update buffer sizes
                with self.sync_lock:
                    self.frame_buffer = deque(
                        self.frame_buffer, 
                        maxlen=int(self.buffer_duration * DEFAULT_FPS)
                    )
                    self.audio_buffer = deque(
                        self.audio_buffer,
                        maxlen=int(self.buffer_duration * AUDIO_SAMPLE_RATE * AUDIO_CHANNELS)
                    )
                
            if "format" in settings:
                self.format = settings["format"].lower()
                
            if "save_path" in settings:
                new_path = Path(settings["save_path"])
                new_path.mkdir(parents=True, exist_ok=True)
                self.output_folder = new_path
                
            self.logger.info("Clipper settings updated successfully")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Updating settings")

    def get_statistics(self) -> Dict:
        """Get clipper statistics."""
        return {
            "clips_created": self.clips_created,
            "average_duration": np.mean(self.clip_durations) if self.clip_durations else 0,
            "total_duration": sum(self.clip_durations) if self.clip_durations else 0,
            "last_clip_time": self.last_clip_time,
            "buffer_usage": {
                "video": len(self.frame_buffer) / self.frame_buffer.maxlen if self.frame_buffer.maxlen else 0,
                "audio": len(self.audio_buffer) / self.audio_buffer.maxlen if self.audio_buffer.maxlen else 0
            }
        }

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop_listening()
            if hasattr(self, 'audio_stream'):
                self.audio_stream.terminate()
            if hasattr(self, 'hotkey'):
                self.hotkey.stop()
            
            self.logger.info("Clipper cleanup completed")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Clipper cleanup")