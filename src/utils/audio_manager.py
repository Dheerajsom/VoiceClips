# src/utils/audio_manager.py
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
import pyaudio
import wave
import numpy as np
import logging
from typing import Optional, Dict, List, Tuple, Any
import threading
import queue
from dataclasses import dataclass
import time
from pathlib import Path
import audioop

from src.constants import *
from src.utils.error_handler import ErrorHandler
from src.utils.performance import PerformanceUtils

@dataclass
class AudioFrame:
    """Represents an audio frame with metadata."""
    data: bytes
    timestamp: float
    frame_number: int
    channels: int
    sample_width: int
    sample_rate: int

class AudioDevice:
    """Represents an audio device."""
    def __init__(self, index: int, name: str, max_channels: int, 
                 default_sample_rate: int, is_input: bool = True):
        self.index = index
        self.name = name
        self.max_channels = max_channels
        self.default_sample_rate = default_sample_rate
        self.is_input = is_input
        self.is_default = False
        self.capabilities: Dict[str, Any] = {}

class AudioManager:
    """Manages audio capture and processing."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)
        self.performance = PerformanceUtils()
        
        # Initialize components
        self.init_components()
        
        # Setup buffers and queues
        self.setup_buffers()
        
        # Performance monitoring
        self.stats = {
            'frames_captured': 0,
            'frames_dropped': 0,
            'current_latency': 0,
            'peak_level': 0.0
        }

    def init_components(self):
        """Initialize audio components."""
        try:
            # PyAudio instance
            self.audio = pyaudio.PyAudio()
            
            # Current settings
            self.sample_rate = AUDIO_SAMPLE_RATE
            self.channels = AUDIO_CHANNELS
            self.chunk_size = AUDIO_CHUNK_SIZE
            self.format = pyaudio.paFloat32
            
            # Streams
            self.input_stream = None
            self.output_stream = None
            
            # Threading control
            self.is_capturing = False
            self.is_monitoring = False
            self.capture_thread: Optional[threading.Thread] = None
            self.monitor_thread: Optional[threading.Thread] = None
            
            # Volume control
            self.input_volume = 1.0
            self.output_volume = 1.0
            self.is_muted = False
            
            # Available devices
            self.devices = self.discover_devices()
            
            # Current devices
            self.current_input = None
            self.current_output = None
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Initializing audio components")
            raise

    def setup_buffers(self):
        """Setup audio buffers and queues."""
        try:
            # Calculate buffer sizes
            buffer_duration = 5  # 5 seconds buffer
            buffer_size = int(self.sample_rate * buffer_duration)
            
            # Create buffers
            self.input_buffer = queue.Queue(maxsize=buffer_size)
            self.output_buffer = queue.Queue(maxsize=buffer_size)
            self.monitor_buffer = queue.Queue(maxsize=self.sample_rate)  # 1 second monitor buffer
            
            # Processing queues
            self.processing_queue = queue.Queue(maxsize=buffer_size)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Setting up audio buffers")
            raise

    def discover_devices(self) -> Dict[int, AudioDevice]:
        """Discover available audio devices."""
        devices = {}
        try:
            default_input = self.audio.get_default_input_device_info()
            default_output = self.audio.get_default_output_device_info()
            
            for i in range(self.audio.get_device_count()):
                try:
                    info = self.audio.get_device_info_by_index(i)
                    
                    # Create input device if available
                    if info['maxInputChannels'] > 0:
                        device = AudioDevice(
                            index=i,
                            name=info['name'],
                            max_channels=info['maxInputChannels'],
                            default_sample_rate=int(info['defaultSampleRate']),
                            is_input=True
                        )
                        device.is_default = (i == default_input['index'])
                        devices[i] = device
                    
                    # Create output device if available
                    if info['maxOutputChannels'] > 0:
                        device = AudioDevice(
                            index=i,
                            name=info['name'],
                            max_channels=info['maxOutputChannels'],
                            default_sample_rate=int(info['defaultSampleRate']),
                            is_input=False
                        )
                        device.is_default = (i == default_output['index'])
                        devices[i] = device
                        
                except Exception as e:
                    self.logger.warning(f"Error getting device {i}: {e}")
                    continue
            
            return devices
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Discovering audio devices")
            return {}

    def start_capture(self, device_index: Optional[int] = None) -> bool:
        """Start audio capture."""
        try:
            if self.is_capturing:
                return False
            
            # Select input device
            if device_index is not None:
                if device_index not in self.devices:
                    raise ValueError(f"Invalid device index: {device_index}")
                self.current_input = self.devices[device_index]
            elif not self.current_input:
                # Use default input device
                default_info = self.audio.get_default_input_device_info()
                self.current_input = self.devices[default_info['index']]

            # Try to open stream with proper channel configuration
            try:
                self.input_stream = self.audio.open(
                    format=pyaudio.paFloat32,
                    channels=1,  # Start with mono
                    rate=AUDIO_SAMPLE_RATE,
                    input=True,
                    input_device_index=self.current_input.index,
                    frames_per_buffer=AUDIO_CHUNK_SIZE,
                    stream_callback=self._audio_callback
                )
            except:
                # If mono fails, try stereo
                self.input_stream = self.audio.open(
                    format=pyaudio.paFloat32,
                    channels=2,
                    rate=AUDIO_SAMPLE_RATE,
                    input=True,
                    input_device_index=self.current_input.index,
                    frames_per_buffer=AUDIO_CHUNK_SIZE,
                    stream_callback=self._audio_callback
                )
            
            # Start capture thread
            self.is_capturing = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.capture_thread.start()
            
            self.logger.info(f"Started audio capture on device: {self.current_input.name}")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Starting audio capture")
            return False
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for input stream."""
        try:
            if status:
                self.logger.warning(f"Audio callback status: {status}")
            
            # Create audio frame
            frame = AudioFrame(
                data=in_data,
                timestamp=time.time(),
                frame_number=self.stats['frames_captured'],
                channels=self.channels,
                sample_width=pyaudio.get_sample_size(self.format),
                sample_rate=self.sample_rate
            )
            
            # Add to buffers
            self._add_to_buffers(frame)
            
            return (None, pyaudio.paContinue)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Audio callback")
            return (None, pyaudio.paAbort)

    def _capture_loop(self):
        """Main capture loop."""
        try:
            while self.is_capturing:
                # Process audio in processing queue
                try:
                    frame = self.processing_queue.get_nowait()
                    processed_frame = self._process_audio(frame)
                    if processed_frame:
                        self.output_buffer.put(processed_frame)
                except queue.Empty:
                    time.sleep(0.001)  # Prevent CPU overuse
                    
        except Exception as e:
            self.error_handler.handle_error(e, context="Audio capture loop")
            self.is_capturing = False

    def _process_audio(self, frame: AudioFrame) -> Optional[AudioFrame]:
        """Process audio frame."""
        try:
            # Convert to numpy array for processing
            audio_data = np.frombuffer(frame.data, dtype=np.float32)
            
            # Apply volume
            if not self.is_muted:
                audio_data *= self.input_volume
            else:
                audio_data *= 0
            
            # Update peak level
            self.stats['peak_level'] = float(np.max(np.abs(audio_data)))
            
            # Convert back to bytes
            frame.data = audio_data.tobytes()
            
            return frame
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Processing audio")
            return None

    def _add_to_buffers(self, frame: AudioFrame):
        """Add frame to buffers."""
        try:
            # Add to input buffer
            if not self.input_buffer.full():
                self.input_buffer.put(frame)
            else:
                self.stats['frames_dropped'] += 1
            
            # Add to monitor buffer
            if self.is_monitoring:
                if not self.monitor_buffer.full():
                    self.monitor_buffer.put(frame)
                else:
                    try:
                        self.monitor_buffer.get_nowait()
                    except queue.Empty:
                        pass
                    self.monitor_buffer.put(frame)
            
            # Add to processing queue
            if not self.processing_queue.full():
                self.processing_queue.put(frame)
            
            # Update statistics
            self.stats['frames_captured'] += 1
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Adding to buffers")

    def start_monitoring(self) -> bool:
        """Start audio monitoring."""
        try:
            if self.is_monitoring:
                return False
            
            # Create output stream if needed
            if not self.output_stream:
                self.output_stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    output=True,
                    frames_per_buffer=self.chunk_size
                )
            
            # Start monitor thread
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
            self.logger.info("Started audio monitoring")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Starting audio monitoring")
            return False

    def _monitor_loop(self):
        """Audio monitoring loop."""
        try:
            while self.is_monitoring:
                try:
                    frame = self.monitor_buffer.get(timeout=0.1)
                    if self.output_stream and not self.is_muted:
                        # Apply output volume
                        audio_data = np.frombuffer(frame.data, dtype=np.float32)
                        audio_data *= self.output_volume
                        self.output_stream.write(audio_data.tobytes())
                except queue.Empty:
                    continue
                    
        except Exception as e:
            self.error_handler.handle_error(e, context="Audio monitoring loop")
            self.is_monitoring = False

    def set_volume(self, volume: float, is_input: bool = True):
        """Set volume level."""
        try:
            volume = max(0.0, min(1.0, volume))
            if is_input:
                self.input_volume = volume
            else:
                self.output_volume = volume
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Setting volume")

    def toggle_mute(self):
        """Toggle mute state."""
        self.is_muted = not self.is_muted

    def switch_device(self, device_index: int, is_input: bool = True) -> bool:
        """Switch audio device."""
        try:
            if device_index not in self.devices:
                return False
            
            device = self.devices[device_index]
            if device.is_input != is_input:
                return False
            
            # Stop current capture/monitoring
            was_capturing = self.is_capturing
            was_monitoring = self.is_monitoring
            
            if is_input:
                self.stop_capture()
                self.current_input = device
                if was_capturing:
                    self.start_capture()
            else:
                self.stop_monitoring()
                self.current_output = device
                if was_monitoring:
                    self.start_monitoring()
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Switching device")
            return False

    def get_audio_data(self, duration: float) -> Optional[bytes]:
        """Get audio data for specified duration."""
        try:
            frames = []
            frame_count = int(duration * self.sample_rate / self.chunk_size)
            
            for _ in range(frame_count):
                try:
                    frame = self.output_buffer.get_nowait()
                    frames.append(frame.data)
                except queue.Empty:
                    break
            
            return b''.join(frames) if frames else None
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting audio data")
            return None

    def save_audio(self, filepath: str, duration: float) -> bool:
        """Save audio to file."""
        try:
            audio_data = self.get_audio_data(duration)
            if not audio_data:
                return False
            
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(pyaudio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Saving audio")
            return False

    def get_statistics(self) -> Dict:
        """Get audio statistics."""
        try:
            return {
                'frames_captured': self.stats['frames_captured'],
                'frames_dropped': self.stats['frames_dropped'],
                'current_latency': self.stats['current_latency'],
                'peak_level': self.stats['peak_level'],
                'buffer_usage': {
                    'input': self.input_buffer.qsize() / self.input_buffer.maxsize,
                    'output': self.output_buffer.qsize() / self.output_buffer.maxsize,
                    'monitor': self.monitor_buffer.qsize() / self.monitor_buffer.maxsize
                }
            }
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting statistics")
            return {}

    def stop_capture(self):
        """Stop audio capture."""
        try:
            self.is_capturing = False
            if self.capture_thread:
                self.capture_thread.join()
            
            if self.input_stream:
                self.input_stream.stop_stream()
                self.input_stream.close()
                self.input_stream = None
            
            self.clear_buffers()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Stopping capture")

    def stop_monitoring(self):
        """Stop audio monitoring."""
        try:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
            
            if self.output_stream:
                self.output_stream.stop_stream()
                self.output_stream.close()
                self.output_stream = None
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Stopping monitoring")

    def clear_buffers(self):
        """Clear all audio buffers."""
        try:
            for buffer in [self.input_buffer, self.output_buffer, 
                          self.monitor_buffer, self.processing_queue]:
                while not buffer.empty():
                    buffer.get_nowait()
                    
        except Exception as e:
            self.error_handler.handle_error(e, context="Clearing buffers")

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop_capture()
            self.stop_monitoring()
            
            if self.audio:
                self.audio.terminate()
            
            self.logger.info("Audio manager cleanup completed")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Audio manager cleanup")