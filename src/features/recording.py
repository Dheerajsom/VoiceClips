# src/features/recording.py
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
from pathlib import Path
import threading
import subprocess
import logging
from typing import Optional, Dict, Any, Tuple, List
import time
from datetime import datetime
import json
import shutil
import numpy as np
from queue import Queue, Empty
from src.constants import *
from src.utils.error_handler import ErrorHandler
from src.utils.video_manager import VideoManager, VideoFrame
from src.utils.audio_manager import AudioManager, AudioFrame
from src.utils.performance import PerformanceUtils

class RecordingState:
    """Recording state management."""
    def __init__(self):
        self.is_recording = False
        self.is_paused = False
        self.start_time: Optional[float] = None
        self.pause_time: Optional[float] = None
        self.total_pause_duration = 0.0
        self.frame_count = 0
        self.error: Optional[str] = None

class RecordingManager:
    """Manages video recording functionality."""
    
    def __init__(self, config: Dict):
        """Initialize recording manager."""
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)
        self.config = config
        
        # Initialize state first
        self.state = RecordingState()
        
        # Format and save path
        self.format = config.get("recording.format", DEFAULT_FILE_EXTENSION)
        self.save_path = Path(config.get("recording.save_path", DEFAULT_RECORDINGS_FOLDER))
        self.quality = config.get("video.quality", "High")
        
        # Create directories
        self.save_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize paths
        self.temp_video = None
        self.temp_audio = None
        self.output_file = None
        self.encoding_process = None
        
        # Initialize statistics
        self.stats = {
            'total_recordings': 0,
            'total_duration': 0.0,
            'failed_recordings': 0,
            'current_filesize': 0,
            'current_duration': 0.0,
            'encoding_speed': 0.0
        }
        
        # Initialize buffers
        self.setup_buffers()
        
        # Initialize managers after buffers are setup
        self.video_manager = VideoManager()
        self.audio_manager = AudioManager()
        
        # Initialize threads
        self.record_thread = None
        self.encoding_thread = None
        
        self.logger.info("Recording manager initialized successfully")
    def init_components(self):
        """Initialize recording components."""
        try:
            # Create managers
            self.video_manager = VideoManager()
            self.audio_manager = AudioManager()
            
            # Recording state
            self.state = RecordingState()
            
            # Current settings
            self.format = self.config.get("recording.format", DEFAULT_FILE_EXTENSION)
            self.save_path = Path(self.config.get("recording.save_path", 
                                                DEFAULT_RECORDINGS_FOLDER))
            self.quality = self.config.get("video.quality", "High")
            
            # Ensure save directory exists
            self.save_path.mkdir(parents=True, exist_ok=True)
            
            # Threading
            self.record_thread: Optional[threading.Thread] = None
            self.encoding_thread: Optional[threading.Thread] = None
            
            # Statistics
            self.stats = {
                'total_recordings': 0,
                'total_duration': 0.0,
                'failed_recordings': 0,
                'current_filesize': 0,
                'current_duration': 0.0,
                'encoding_speed': 0.0
            }
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Initializing recording components")
            raise

    def setup_buffers(self):
        """Setup recording buffers and queues."""
        try:
            # Calculate buffer sizes based on FPS and duration
            buffer_duration = 5  # 5 seconds buffer
            video_buffer_size = int(DEFAULT_FPS * buffer_duration)
            audio_buffer_size = int(AUDIO_SAMPLE_RATE * buffer_duration)

            # Initialize frame queues
            self.video_queue = Queue(maxsize=video_buffer_size)
            self.audio_queue = Queue(maxsize=audio_buffer_size)
            
            # Initialize processing queues
            self.processing_queue = Queue(maxsize=video_buffer_size)
            
            # Initialize preview buffer with smaller size
            self.preview_buffer = Queue(maxsize=30)  # 1 second at 30fps
            
            # Initialize output queue
            self.output_queue = Queue(maxsize=video_buffer_size)
            
            # Clear any existing data in queues
            self._clear_queues()
            
            self.logger.info("Recording buffers initialized successfully")
            return True

        except Exception as e:
            self.error_handler.handle_error(e, context="Setting up recording buffers")
            return False

    def _clear_queues(self):
        """Clear all recording queues."""
        try:
            queues = [
                self.video_queue,
                self.audio_queue,
                self.processing_queue,
                self.preview_buffer,
                self.output_queue
            ]
            
            for q in queues:
                while not q.empty():
                    try:
                        q.get_nowait()
                    except Queue.Empty:
                        continue
                        
        except Exception as e:
            self.error_handler.handle_error(e, context="Clearing queues")


    def start_recording(self) -> bool:
        """Start recording."""
        try:
            if self.state.is_recording:
                return False
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file = self.save_path / f"recording_{timestamp}.{self.format}"
            
            # Create temporary files
            self.temp_video = self.save_path / f"temp_video_{timestamp}.raw"
            self.temp_audio = self.save_path / f"temp_audio_{timestamp}.wav"
            
            # Start video and audio capture
            if not self.video_manager.start_capture():
                raise Exception("Failed to start video capture")
            if not self.audio_manager.start_capture():
                raise Exception("Failed to start audio capture")
            
            # Update state
            self.state.is_recording = True
            self.state.start_time = time.time()
            self.state.frame_count = 0
            
            # Start recording thread
            self.record_thread = threading.Thread(
                target=self._recording_loop,
                daemon=True
            )
            self.record_thread.start()
            
            self.logger.info(f"Started recording to {self.output_file}")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Starting recording")
            self.cleanup()
            return False

    def _recording_loop(self):
        """Main recording loop."""
        video_file = None
        audio_file = None
        
        try:
            # Open temporary files
            video_file = open(self.temp_video, 'wb')
            audio_file = open(self.temp_audio, 'wb')
            
            # Write WAV header
            self._write_wav_header(audio_file)
            
            while self.state.is_recording:
                if not self.state.is_paused:
                    # Process video
                    video_frame = self.video_manager.get_frame()
                    if video_frame:
                        video_file.write(video_frame.data.tobytes())
                        self.state.frame_count += 1
                    
                    # Process audio
                    audio_frame = self.audio_manager.get_audio_data(1/30)  # Match video FPS
                    if audio_frame:
                        audio_file.write(audio_frame)
                    
                    # Update statistics
                    self._update_recording_stats()
                
                time.sleep(0.001)  # Prevent CPU overuse
            
        except Exception as e:
            self.state.error = str(e)
            self.error_handler.handle_error(e, context="Recording loop")
            
        finally:
            # Close files
            if video_file:
                video_file.close()
            if audio_file:
                self._update_wav_header(audio_file)
                audio_file.close()
            
            # Start encoding if recording was successful
            if not self.state.error:
                self._start_encoding()
    def _start_encoding(self):
        """Start encoding process."""
        try:
            # Create encoding command
            command = self._create_ffmpeg_command()
            
            # Start encoding process
            self.encoding_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Start encoding monitor thread
            self.encoding_thread = threading.Thread(
                target=self._monitor_encoding,
                daemon=True
            )
            self.encoding_thread.start()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Starting encoding")
            self.state.error = str(e)

    def _create_ffmpeg_command(self) -> List[str]:
        """Create FFmpeg encoding command."""
        try:
            # Get video dimensions
            width, height = map(int, BASE_CANVAS_RESOLUTION.split('x'))
            
            # Base command
            command = [
                'ffmpeg',
                # Video input
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-s', f'{width}x{height}',
                '-pix_fmt', 'rgb24',
                '-framerate', str(DEFAULT_FPS),
                '-i', str(self.temp_video),
                
                # Audio input
                '-i', str(self.temp_audio),
                
                # Video encoding settings
                '-c:v', 'h264',
                '-preset', self._get_encoding_preset(),
                '-crf', self._get_quality_crf(),
                
                # Audio encoding settings
                '-c:a', 'aac',
                '-b:a', '192k',
                
                # Output settings
                '-pix_fmt', 'yuv420p',  # For compatibility
                '-movflags', '+faststart',  # For streaming
                '-y',  # Overwrite output
                str(self.output_file)
            ]
            
            # Add quality-specific settings
            if self.quality == "High":
                command.extend(['-x264-params', 'ref=4:me=umh:subme=7:trellis=2'])
            
            return command
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Creating FFmpeg command")
            raise

    def _get_encoding_preset(self) -> str:
        """Get encoding preset based on quality setting."""
        presets = {
            "Low": "veryfast",
            "Medium": "medium",
            "High": "slow"
        }
        return presets.get(self.quality, "medium")

    def _get_quality_crf(self) -> str:
        """Get CRF value based on quality setting."""
        crf_values = {
            "Low": "28",
            "Medium": "23",
            "High": "18"
        }
        return crf_values.get(self.quality, "23")

    def _monitor_encoding(self):
        """Monitor encoding progress."""
        try:
            while self.encoding_process and self.encoding_process.poll() is None:
                # Read encoding progress
                line = self.encoding_process.stderr.readline()
                if line:
                    # Parse FFmpeg output for progress
                    if 'speed' in line:
                        try:
                            speed = float(line.split('speed=')[1].split('x')[0])
                            self.stats['encoding_speed'] = speed
                        except:
                            pass
                
                time.sleep(0.1)
            
            # Check encoding result
            if self.encoding_process.returncode != 0:
                error_output = self.encoding_process.stderr.read()
                raise Exception(f"Encoding failed: {error_output}")
            
            # Update statistics
            self.stats['total_recordings'] += 1
            self.stats['total_duration'] += self.get_recording_duration()
            
            # Cleanup temporary files
            self.cleanup_temp_files()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Monitoring encoding")
            self.stats['failed_recordings'] += 1
            self.state.error = str(e)

    def stop_recording(self) -> bool:
        """Stop recording."""
        try:
            if not self.state.is_recording:
                return False
            
            # Update state
            self.state.is_recording = False
            self.state.is_paused = False
            
            # Stop capture
            self.video_manager.stop_capture()
            self.audio_manager.stop_capture()
            
            # Wait for recording thread
            if self.record_thread:
                self.record_thread.join()
            
            # Wait for encoding if needed
            if self.encoding_thread:
                self.encoding_thread.join()
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Stopping recording")
            return False

    def toggle_pause(self) -> bool:
        """Toggle recording pause state."""
        try:
            if not self.state.is_recording:
                return False
            
            if self.state.is_paused:
                # Resume recording
                pause_duration = time.time() - self.state.pause_time
                self.state.total_pause_duration += pause_duration
                self.state.pause_time = None
                self.state.is_paused = False
            else:
                # Pause recording
                self.state.pause_time = time.time()
                self.state.is_paused = True
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Toggling pause")
            return False

    def get_recording_duration(self) -> float:
        """Get current recording duration in seconds."""
        try:
            if not self.state.start_time:
                return 0.0
            
            duration = time.time() - self.state.start_time
            return duration - self.state.total_pause_duration
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting duration")
            return 0.0

    def _write_wav_header(self, file):
        """Write initial WAV header."""
        try:
            # Standard WAV header with placeholder size values
            header = bytes([
                # RIFF header
                0x52, 0x49, 0x46, 0x46,  # "RIFF"
                0x00, 0x00, 0x00, 0x00,  # Size (placeholder)
                0x57, 0x41, 0x56, 0x45,  # "WAVE"
                # Format chunk
                0x66, 0x6D, 0x74, 0x20,  # "fmt "
                0x10, 0x00, 0x00, 0x00,  # Chunk size (16 bytes)
                0x01, 0x00,              # Audio format (1 = PCM)
                0x02, 0x00,              # Number of channels (2)
                0x44, 0xAC, 0x00, 0x00,  # Sample rate (44100)
                0x10, 0xB1, 0x02, 0x00,  # Byte rate
                0x04, 0x00,              # Block align
                0x10, 0x00,              # Bits per sample (16)
                # Data chunk
                0x64, 0x61, 0x74, 0x61,  # "data"
                0x00, 0x00, 0x00, 0x00   # Size (placeholder)
            ])
            file.write(header)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Writing WAV header")

    def _update_wav_header(self, file):
        """Update WAV header with final size values."""
        try:
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            
            # Update RIFF chunk size
            file.seek(4)
            file.write((size - 8).to_bytes(4, 'little'))
            
            # Update data chunk size
            file.seek(40)
            file.write((size - 44).to_bytes(4, 'little'))
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Updating WAV header")

    def _update_recording_stats(self):
        """Update recording statistics."""
        try:
            # Update current file size
            if self.temp_video and self.temp_video.exists():
                self.stats['current_filesize'] = self.temp_video.stat().st_size
            
            # Update current duration
            self.stats['current_duration'] = self.get_recording_duration()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Updating stats")

    def get_statistics(self) -> Dict:
        """Get recording statistics."""
        return {
            'is_recording': self.state.is_recording,
            'is_paused': self.state.is_paused,
            'current_duration': self.stats['current_duration'],
            'current_filesize': self.stats['current_filesize'],
            'total_recordings': self.stats['total_recordings'],
            'total_duration': self.stats['total_duration'],
            'failed_recordings': self.stats['failed_recordings'],
            'encoding_speed': self.stats['encoding_speed'],
            'frame_count': self.state.frame_count,
            'error': self.state.error
        }
    def _sync_streams(self):
        """Synchronize audio and video streams."""
        try:
            audio_time = self.audio_manager.get_current_timestamp()
            video_time = self.video_manager.get_current_timestamp()
            
            # Calculate drift
            drift = abs(audio_time - video_time)
            if drift > 0.1:  # More than 100ms drift
                self.logger.warning(f"A/V sync drift: {drift:.3f}s")
                # Adjust timestamps
                self._adjust_sync(audio_time, video_time)
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Syncing streams")

    def _adjust_sync(self, audio_time: float, video_time: float):
        """Adjust stream synchronization."""
        try:
            if audio_time > video_time:
                # Drop audio frames to catch up
                while not self.audio_queue.empty():
                    self.audio_queue.get_nowait()
            else:
                # Drop video frames to catch up
                while not self.video_queue.empty():
                    self.video_queue.get_nowait()
                    
        except Exception as e:
            self.error_handler.handle_error(e, context="Adjusting sync")

    def cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            for temp_file in [self.temp_video, self.temp_audio]:
                if temp_file and temp_file.exists():
                    temp_file.unlink()
        except Exception as e:
            self.error_handler.handle_error(e, context="Cleaning temp files")

    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop recording if active
            if self.state.is_recording:
                self.stop_recording()
            
            # Stop encoding process if running
            if self.encoding_process:
                self.encoding_process.terminate()
                self.encoding_process.wait()
            
            # Clean up managers
            self.video_manager.cleanup()
            self.audio_manager.cleanup()
            
            # Remove temporary files
            self.cleanup_temp_files()
            
            self.logger.info("Recording manager cleanup completed")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Recording manager cleanup")