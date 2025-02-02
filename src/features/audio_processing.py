# src/features/audio_processing.py

import numpy as np
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from scipy import signal
import threading
import queue
import pyaudio

class AudioFilter(ABC):
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.parameters = {}
        self.setup_parameters()

    @abstractmethod
    def setup_parameters(self):
        """Setup filter parameters."""
        pass

    @abstractmethod
    def process(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Process audio data."""
        pass

class AudioProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.filters: Dict[str, AudioFilter] = {}
        self.processing = False
        self.input_queue = queue.Queue(maxsize=10)
        self.output_queue = queue.Queue(maxsize=10)
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.channels = 2
        
        self.register_default_filters()

    def register_default_filters(self):
        """Register built-in audio filters."""
        self.register_filter(NoiseGateFilter("Noise Gate"))
        self.register_filter(CompressorFilter("Compressor"))
        self.register_filter(EqualizerFilter("Equalizer"))

    def register_filter(self, filter: AudioFilter):
        """Register new audio filter."""
        self.filters[filter.name] = filter

    def start_processing(self):
        """Start audio processing."""
        if self.processing:
            return

        self.processing = True
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.processing_thread.start()

    def stop_processing(self):
        """Stop audio processing."""
        self.processing = False
        if hasattr(self, 'processing_thread'):
            self.processing_thread.join()

    def _processing_loop(self):
        """Main processing loop."""
        while self.processing:
            try:
                # Get audio data from input queue
                audio_data = self.input_queue.get(timeout=0.1)
                
                # Process through filters
                for filter in self.filters.values():
                    if filter.enabled:
                        audio_data = filter.process(
                            audio_data,
                            self.sample_rate
                        )
                
                # Put processed data in output queue
                self.output_queue.put(audio_data)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in audio processing: {e}")

    def process_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio data through all enabled filters."""
        try:
            processed_data = audio_data.copy()
            
            for filter in self.filters.values():
                if filter.enabled:
                    processed_data = filter.process(
                        processed_data,
                        self.sample_rate
                    )
            
            return processed_data

        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            return audio_data

class NoiseGateFilter(AudioFilter):
    def setup_parameters(self):
        self.parameters.update({
            "threshold": -50.0,  # dB
            "attack": 10.0,      # ms
            "release": 100.0,    # ms
            "hold": 200.0        # ms
        })

    def process(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        try:
            threshold = 10 ** (self.parameters["threshold"] / 20)
            attack_samples = int(self.parameters["attack"] * sample_rate / 1000)
            release_samples = int(self.parameters["release"] * sample_rate / 1000)
            hold_samples = int(self.parameters["hold"] * sample_rate / 1000)

            # Calculate RMS levels
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Apply gate
            gate_mask = (rms > threshold).astype(float)
            
            # Apply attack/release
            for i in range(1, len(gate_mask)):
                if gate_mask[i] > gate_mask[i-1]:
                    gate_mask[i] = min(1.0, gate_mask[i-1] + 1/attack_samples)
                else:
                    gate_mask[i] = max(0.0, gate_mask[i-1] - 1/release_samples)

            return audio_data * gate_mask.reshape(-1, 1)

        except Exception as e:
            logging.error(f"Error in noise gate: {e}")
            return audio_data

class CompressorFilter(AudioFilter):
    def setup_parameters(self):
        self.parameters.update({
            "threshold": -20.0,   # dB
            "ratio": 4.0,        # compression ratio
            "attack": 5.0,       # ms
            "release": 50.0,     # ms
            "makeup_gain": 0.0   # dB
        })

    def process(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        try:
            threshold = 10 ** (self.parameters["threshold"] / 20)
            ratio = self.parameters["ratio"]
            attack_samples = int(self.parameters["attack"] * sample_rate / 1000)
            release_samples = int(self.parameters["release"] * sample_rate / 1000)
            makeup_gain = 10 ** (self.parameters["makeup_gain"] / 20)

            # Calculate envelope
            envelope = np.abs(audio_data)
            
            # Apply compression
            gain_reduction = np.where(
                envelope > threshold,
                (envelope / threshold) ** (1/ratio - 1),
                1.0
            )
            
            # Apply attack/release
            for i in range(1, len(gain_reduction)):
                if gain_reduction[i] < gain_reduction[i-1]:
                    gain_reduction[i] = min(
                        1.0,
                        gain_reduction[i-1] + 1/attack_samples
                    )
                else:
                    gain_reduction[i] = max(
                        gain_reduction[i],
                        gain_reduction[i-1] - 1/release_samples
                    )

            return audio_data * gain_reduction * makeup_gain

        except Exception as e:
            logging.error(f"Error in compressor: {e}")
            return audio_data

class EqualizerFilter(AudioFilter):
    def setup_parameters(self):
        self.parameters.update({
            "bands": {
                "32": 0.0,
                "64": 0.0,
                "125": 0.0,
                "250": 0.0,
                "500": 0.0,
                "1k": 0.0,
                "2k": 0.0,
                "4k": 0.0,
                "8k": 0.0,
                "16k": 0.0
            },
            "q_factor": 1.4
        })

    def process(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        try:
            # Create butterworth filters for each band
            filtered_data = np.zeros_like(audio_data)
            
            for freq, gain in self.parameters["bands"].items():
                if gain == 0.0:
                    continue
                    
                # Convert frequency string to number
                center_freq = float(freq.replace('k', '000'))
                
                # Calculate filter parameters
                w0 = 2 * np.pi * center_freq / sample_rate
                alpha = np.sin(w0) / (2 * self.parameters["q_factor"])
                
                # Create biquad filter coefficients
                A = 10 ** (gain / 40)
                b0 = 1 + alpha * A
                b1 = -2 * np.cos(w0)
                b2 = 1 - alpha * A
                a0 = 1 + alpha / A
                a1 = -2 * np.cos(w0)
                a2 = 1 - alpha / A
                
                # Apply filter
                filtered = signal.lfilter(
                    [b0, b1, b2],
                    [a0, a1, a2],
                    audio_data
                )
                filtered_data += filtered

            return filtered_data

        except Exception as e:
            logging.error(f"Error in equalizer: {e}")
            return audio_data