# In src/features/audio_mixer.py

# ADD THESE IMPORTS AT THE TOP OF THE FILE
from typing import Dict, Optional, List, Tuple, Any
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
import time
import numpy as np
import pyaudio
import threading
import logging
import queue
from dataclasses import dataclass
from src.constants import *
from src.utils.error_handler import ErrorHandler

# ADD THIS CLASS BEFORE THE AudioMixer CLASS
@dataclass
class AudioDevice:
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: int
    is_default: bool = False

# REPLACE THE EXISTING AudioMixer CLASS WITH THIS ENHANCED VERSION
class AudioMixer:
    """Manages audio mixing and device control."""
    
    def __init__(self, config: Dict):
        # State tracking
        self.state = type('AudioState', (), {
            'start_time': None,
            'is_recording': False,
            'is_paused': False
        })()
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)
        self.config = config
        
        self.audio = pyaudio.PyAudio()
        self.devices = {}  # Add this line

        self.sources: Dict[str, Dict] = {}
        self.master_volume = 1.0
        self.is_monitoring = False
        
        # Audio processing
        self.processing_queue = queue.Queue(maxsize=100)
        self.output_queue = queue.Queue(maxsize=100)
        
        # Initialize devices
        self.setup_audio_devices()
        
        # Start processing thread
        self.start_processing()

    # ADD THESE NEW METHODS TO THE AudioMixer CLASS
    def start_processing(self):
        """Start audio processing thread."""
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.processing_thread.start()

    def _processing_loop(self):
        """Main audio processing loop."""
        while True:
            try:
                # Get audio data from queue
                audio_data = self.processing_queue.get(timeout=0.1)
                
                # Process audio
                processed_data = self._process_audio(audio_data)
                
                # Put processed data in output queue
                self.output_queue.put(processed_data)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.error_handler.handle_error(e, context="Audio processing")

    def _process_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio data with effects and mixing."""
        try:
            # Convert to float32 for processing
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # Apply source-specific processing
            for source in self.sources.values():
                if not source['muted']:
                    # Apply volume
                    audio_float *= source['volume']
                    
                    # Apply effects if any
                    if 'effects' in source:
                        for effect in source['effects']:
                            audio_float = effect.process(audio_float)
            
            # Apply master volume
            audio_float *= self.master_volume
            
            # Clip to prevent distortion
            audio_float = np.clip(audio_float, -1.0, 1.0)
            
            # Convert back to int16
            return (audio_float * 32768.0).astype(np.int16)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Audio processing")
            return audio_data

    # MODIFY THE EXISTING setup_audio_devices METHOD
    def setup_audio_devices(self):
        """Initialize audio devices."""
        try:
            # Get device settings from config
            desktop_device = self.config.get("audio.desktop_device", "Default")
            mic_device = self.config.get("audio.mic_device", "Default")
            
            # Get available devices first
            self.devices = self._get_available_devices()
            
            if not self.devices:
                self.logger.error("No audio devices found")
                return False

            # Setup desktop audio
            desktop_info = self._get_device_info(desktop_device) or self._get_default_output_device()
            if desktop_info:
                self.add_source(
                    "Desktop Audio",
                    desktop_info['index'],
                    self.config.get("audio.desktop_volume", DEFAULT_DESKTOP_VOLUME) / 100.0,
                    False
                )

            # Setup microphone
            mic_info = self._get_device_info(mic_device) or self._get_default_input_device()
            if mic_info:
                self.add_source(
                    "Microphone",
                    mic_info['index'],
                    self.config.get("audio.mic_volume", DEFAULT_MIC_VOLUME) / 100.0,
                    False
                )

            return True

        except Exception as e:
            self.error_handler.handle_error(e, context="Audio device setup")
            return False

    def _get_available_devices(self):
        """Get list of available audio devices."""
        devices = {}
        try:
            for i in range(self.audio.get_device_count()):
                try:
                    info = self.audio.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0 or info['maxOutputChannels'] > 0:
                        devices[i] = info
                except Exception as e:
                    self.logger.warning(f"Error getting device {i}: {e}")
                    continue
            return devices
        except Exception as e:
            self.logger.error(f"Error getting audio devices: {e}")
            return {}

    def _get_default_input_device(self):
        """Get default input device info."""
        try:
            return self.audio.get_default_input_device_info()
        except Exception as e:
            self.logger.error(f"Error getting default input device: {e}")
            return None

    def _get_default_output_device(self):
        """Get default output device info."""
        try:
            return self.audio.get_default_output_device_info()
        except Exception as e:
            self.logger.error(f"Error getting default output device: {e}")
            return None

    # ADD THESE NEW METHODS TO THE AudioMixer CLASS
    def update_settings(self, settings: Dict):
        """Update audio mixer settings."""
        try:
            if "desktop_device" in settings or "mic_device" in settings:
                self.stop_monitoring()
                self._cleanup_streams()
                self.setup_audio_devices()
                if self.is_monitoring:
                    self.start_monitoring()
            
            if "desktop_volume" in settings:
                self.set_source_volume(
                    "Desktop Audio",
                    settings["desktop_volume"] / 100.0
                )
            
            if "mic_volume" in settings:
                self.set_source_volume(
                    "Microphone",
                    settings["mic_volume"] / 100.0
                )
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Updating audio settings")

    def get_audio_devices(self) -> List[AudioDevice]:
        """Get list of available audio devices."""
        devices = []
        try:
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                devices.append(AudioDevice(
                    index=i,
                    name=info['name'],
                    max_input_channels=info['maxInputChannels'],
                    max_output_channels=info['maxOutputChannels'],
                    default_sample_rate=int(info['defaultSampleRate']),
                    is_default=(i == self.audio.get_default_input_device_info()['index'])
                ))
            return devices
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting audio devices")
            return []
    def _get_device_info(self, device: str) -> Optional[Dict]:
        """Get device info by name or index."""
        try:
            # If device is an index
            if isinstance(device, int):
                return self.audio.get_device_info_by_index(device)

            # If device is "Default"
            if device == "Default":
                return self.audio.get_default_input_device_info()

            # Search by name
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['name'] == device:
                    return info

            return None

        except Exception as e:
            self.logger.error(f"Error getting device info: {e}")
            return None

    def get_audio_levels(self) -> Dict[str, float]:
        """Get current audio levels for all sources."""
        return {name: source['peak_level'] 
                for name, source in self.sources.items()}
    # ADD THESE METHODS TO THE AudioMixer CLASS
    def start_monitoring(self):
        """Start audio monitoring."""
        try:
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Starting audio monitoring")
    def toggle_source_mute(self, name: str) -> bool:
        """Toggle mute state for audio source."""
        try:
            if name not in self.sources:
                return False
                
            source = self.sources[name]
            source['muted'] = not source.get('muted', False)
            
            return True
        except Exception as e:
            self.error_handler.handle_error(e, context="Toggling source mute")
            return False

    def set_source_volume(self, name: str, volume: float) -> bool:
        """Set volume for audio source."""
        try:
            if name not in self.sources:
                return False
                
            volume = max(0.0, min(1.0, volume))
            self.sources[name]['volume'] = volume
            
            return True
        except Exception as e:
            self.error_handler.handle_error(e, context="Setting source volume")
            return False

    def _monitoring_loop(self):
        """Monitoring loop for audio analysis."""
        while True:
            try:
                # Get audio levels
                audio_buffer = self.get_audio_buffer()
                if audio_buffer is not None:
                    # Perform peak level analysis
                    peak_level = np.max(np.abs(audio_buffer))
                    
                    # Update source volumes
                    for source in self.sources.values():
                        source['peak_level'] = peak_level
                
                time.sleep(0.1)  # Prevent CPU overuse
                
            except Exception as e:
                self.error_handler.handle_error(e, context="Audio monitoring loop")
                time.sleep(1)
    def stop_monitoring(self):
        """Stop audio monitoring."""
        try:
            # Stop processing thread
            self.processing = False
            if hasattr(self, 'processing_thread'):
                self.processing_thread.join(timeout=1.0)
            
            # Clear buffers
            self.clear_buffers()
        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {e}")

    def add_effect_to_source(self, source_name: str, effect: Any) -> bool:
        """Add audio effect to source."""
        try:
            if source_name not in self.sources:
                return False
                
            source = self.sources[source_name]
            if 'effects' not in source:
                source['effects'] = []
                
            source['effects'].append(effect)
            self.logger.info(f"Added effect to {source_name}")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Adding audio effect")
            return False

    def remove_effect_from_source(self, source_name: str, effect_index: int) -> bool:
        """Remove audio effect from source."""
        try:
            if source_name not in self.sources:
                return False
                
            source = self.sources[source_name]
            if 'effects' not in source or effect_index >= len(source['effects']):
                return False
                
            source['effects'].pop(effect_index)
            self.logger.info(f"Removed effect from {source_name}")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Removing audio effect")
            return False

    def get_source_effects(self, source_name: str) -> List[Any]:
        """Get list of effects applied to source."""
        try:
            if source_name not in self.sources:
                return []
                
            source = self.sources[source_name]
            return source.get('effects', [])
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting source effects")
            return []

    def set_master_volume(self, volume: float) -> bool:
        """Set master volume level."""
        try:
            self.master_volume = max(0.0, min(1.0, volume))
            self.logger.info(f"Master volume set to {volume}")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Setting master volume")
            return False

    def get_master_volume(self) -> float:
        """Get master volume level."""
        return self.master_volume

    def get_source_info(self, name: str) -> Optional[Dict]:
        """Get information about audio source."""
        try:
            if name not in self.sources:
                return None
                
            source = self.sources[name]
            return {
                'name': name,
                'device': source['device'],
                'volume': source['volume'],
                'muted': source['muted'],
                'peak_level': source['peak_level'],
                'effects': len(source.get('effects', [])),
                'active': source['stream'] is not None if 'stream' in source else False
            }
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting source info")
            return None
    # Add this method to the AudioMixer class in src/features/audio_mixer.py

    def add_source(self, name: str, device: str, volume: float = 1.0, 
                muted: bool = False) -> bool:
        """Add new audio source."""
        try:
            device_info = self._get_device_info(device)
            if not device_info:
                self.logger.warning(f"Audio device not found: {device}")
                return False

            self.sources[name] = {
                'device': device,
                'device_info': device_info,
                'volume': volume,
                'muted': muted,
                'peak_level': 0.0,
                'stream': None,
                'effects': []
            }
            
            self.logger.info(f"Added audio source: {name}")
            return True

        except Exception as e:
            self.error_handler.handle_error(e, context="Adding audio source")
            return False

    def get_audio_buffer(self) -> Optional[np.ndarray]:
        """Get processed audio buffer."""
        try:
            return self.output_queue.get_nowait()
        except queue.Empty:
            return None
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting audio buffer")
            return None

    def clear_buffers(self):
        """Clear audio buffers."""
        try:
            while not self.processing_queue.empty():
                self.processing_queue.get_nowait()
            while not self.output_queue.empty():
                self.output_queue.get_nowait()
        except Exception as e:
            self.error_handler.handle_error(e, context="Clearing audio buffers")
    def get_current_timestamp(self) -> float:
        """Get current audio timestamp."""
        return time.time() - (self.state.start_time or 0)

    def reset_timestamp(self):
        """Reset audio timestamp."""
        self.state.start_time = time.time()

    # ADD THESE UTILITY METHODS
    def _create_stream(self, device_index: int, is_input: bool = True) -> Optional[pyaudio.Stream]:
        """Create new audio stream."""
        try:
            return self.audio.open(
                format=pyaudio.paFloat32,
                channels=AUDIO_CHANNELS,
                rate=AUDIO_SAMPLE_RATE,
                input=is_input,
                output=not is_input,
                input_device_index=device_index if is_input else None,
                output_device_index=device_index if not is_input else None,
                frames_per_buffer=AUDIO_CHUNK_SIZE,
                stream_callback=self._audio_callback if is_input else None
            )
        except Exception as e:
            self.error_handler.handle_error(e, context="Creating audio stream")
            return None

    def get_status(self) -> Dict:
        """Get current status of audio mixer."""
        return {
            'is_monitoring': self.is_monitoring,
            'master_volume': self.master_volume,
            'active_sources': len([s for s in self.sources.values() 
                                if s.get('stream') is not None]),
            'total_sources': len(self.sources),
            'processing_queue_size': self.processing_queue.qsize(),
            'output_queue_size': self.output_queue.qsize()
        }

    def get_device_capabilities(self, device_index: int) -> Dict:
        """Get detailed device capabilities."""
        try:
            info = self.audio.get_device_info_by_index(device_index)
            return {
                'name': info['name'],
                'max_input_channels': info['maxInputChannels'],
                'max_output_channels': info['maxOutputChannels'],
                'default_sample_rate': info['defaultSampleRate'],
                'supported_sample_rates': self._get_supported_rates(device_index),
                'is_default_input': device_index == self.audio.get_default_input_device_info()['index'],
                'is_default_output': device_index == self.audio.get_default_output_device_info()['index']
            }
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting device capabilities")
            return {}

    def _get_supported_rates(self, device_index: int) -> List[int]:
        """Get supported sample rates for device."""
        standard_rates = [44100, 48000, 88200, 96000]
        supported = []
        
        try:
            for rate in standard_rates:
                try:
                    # Try to open stream with rate
                    stream = self.audio.open(
                        format=pyaudio.paFloat32,
                        channels=AUDIO_CHANNELS,
                        rate=rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=AUDIO_CHUNK_SIZE,
                        start=False
                    )
                    stream.close()
                    supported.append(rate)
                except:
                    continue
                    
            return supported
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting supported rates")
            return [AUDIO_SAMPLE_RATE]  # Return default rate as fallback
    def _cleanup_streams(self):
        """Clean up audio streams."""
        try:
            for source in self.sources.values():
                if 'stream' in source and source['stream']:
                    stream = source['stream']
                    if stream.is_active():
                        stream.stop_stream()
                    stream.close()
                    source['stream'] = None
        except Exception as e:
            self.error_handler.handle_error(e, context="Cleaning up streams")
        

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop_monitoring()
            self._cleanup_streams()
            self.clear_buffers()
            
            if hasattr(self, 'processing_thread'):
                self.processing_thread.join(timeout=1.0)
                
            if self.audio:
                self.audio.terminate()
                
            self.logger.info("Audio mixer cleanup completed")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Audio mixer cleanup")