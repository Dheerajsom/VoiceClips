import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import cv2
import numpy as np
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import threading
import queue
from dataclasses import dataclass

from src.constants import *
from src.utils.error_handler import ErrorHandler
from src.features.effects import BaseVideoEffect, ChromaKeyEffect, ColorCorrectionEffect, BlurEffect

@dataclass
class EffectConfig:
    name: str
    type: str
    parameters: Dict[str, Any]
    enabled: bool = True
    order: int = 0

class SharpnessEffect(BaseVideoEffect):
    """Sharpness adjustment effect."""
    
    def setup_parameters(self):
        self.parameters.update({
            "amount": 0.5  # 0 to 2
        })

    def process(self, frame: np.ndarray) -> np.ndarray:
        try:
            amount = self.parameters["amount"]
            if amount == 0:
                return frame
                
            blurred = cv2.GaussianBlur(frame, (0, 0), 3)
            return cv2.addWeighted(frame, 1.0 + amount, blurred, -amount, 0)
        except Exception as e:
            self.error_handler.handle_error(e, context="Sharpness effect")
            return frame

class NoiseReductionEffect(BaseVideoEffect):
    """Noise reduction effect."""
    
    def setup_parameters(self):
        self.parameters.update({
            "strength": 5,  # 1 to 10
            "method": "gaussian"  # gaussian or median
        })

    def process(self, frame: np.ndarray) -> np.ndarray:
        try:
            strength = self.parameters["strength"]
            method = self.parameters["method"]
            
            if method == "gaussian":
                return cv2.GaussianBlur(frame, (0, 0), strength)
            else:
                kernel_size = 2 * strength + 1
                return cv2.medianBlur(frame, kernel_size)
        except Exception as e:
            self.error_handler.handle_error(e, context="Noise reduction effect")
            return frame

class ColorBalanceEffect(BaseVideoEffect):
    """Color balance adjustment effect."""
    
    def setup_parameters(self):
        self.parameters.update({
            "red": 1.0,    # 0.5 to 1.5
            "green": 1.0,  # 0.5 to 1.5
            "blue": 1.0    # 0.5 to 1.5
        })

    def process(self, frame: np.ndarray) -> np.ndarray:
        try:
            # Split channels
            b, g, r = cv2.split(frame)
            
            # Apply color balance
            r = cv2.multiply(r, self.parameters["red"])
            g = cv2.multiply(g, self.parameters["green"])
            b = cv2.multiply(b, self.parameters["blue"])
            
            # Merge channels
            return cv2.merge([b, g, r])
        except Exception as e:
            self.error_handler.handle_error(e, context="Color balance effect")
            return frame

class VignetteEffect(BaseVideoEffect):
    """Vignette effect."""
    
    def setup_parameters(self):
        self.parameters.update({
            "intensity": 0.5,  # 0 to 1
            "radius": 1.0      # 0.5 to 1.5
        })
        self._cached_mask = None
        self._cached_size = None

    def process(self, frame: np.ndarray) -> np.ndarray:
        try:
            height, width = frame.shape[:2]
            
            # Create or update mask if needed
            if (self._cached_mask is None or 
                self._cached_size != (width, height)):
                
                # Create radial gradient
                center_x, center_y = width/2, height/2
                Y, X = np.ogrid[:height, :width]
                dist_from_center = np.sqrt(
                    (X - center_x)**2 + (Y - center_y)**2
                )
                
                # Normalize distances
                max_dist = np.sqrt(center_x**2 + center_y**2)
                norm_dist = dist_from_center / max_dist
                
                # Create mask
                mask = 1 - norm_dist * self.parameters["intensity"]
                mask = np.clip(mask * self.parameters["radius"], 0, 1)
                
                # Cache mask
                self._cached_mask = mask
                self._cached_size = (width, height)
            
            # Apply mask
            return (frame * self._cached_mask[..., np.newaxis]).astype(np.uint8)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Vignette effect")
            return frame

class FilmGrainEffect(BaseVideoEffect):
    """Film grain effect."""
    
    def setup_parameters(self):
        self.parameters.update({
            "amount": 0.1,    # 0 to 0.5
            "colored": False  # Monochrome or colored grain
        })

    def process(self, frame: np.ndarray) -> np.ndarray:
        try:
            height, width = frame.shape[:2]
            amount = self.parameters["amount"]
            
            if self.parameters["colored"]:
                # Colored grain
                noise = np.random.randn(height, width, 3) * 255 * amount
            else:
                # Monochrome grain
                noise = np.random.randn(height, width) * 255 * amount
                noise = np.stack([noise] * 3, axis=-1)
            
            # Add noise to frame
            noisy_frame = frame + noise
            return np.clip(noisy_frame, 0, 255).astype(np.uint8)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Film grain effect")
            return frame

class RotationEffect(BaseVideoEffect):
    """Rotation and flip effect."""
    
    def setup_parameters(self):
        self.parameters.update({
            "angle": 0,      # -180 to 180
            "flip_h": False,  # Horizontal flip
            "flip_v": False   # Vertical flip
        })

    def process(self, frame: np.ndarray) -> np.ndarray:
        try:
            # Apply flips
            if self.parameters["flip_h"]:
                frame = cv2.flip(frame, 1)
            if self.parameters["flip_v"]:
                frame = cv2.flip(frame, 0)
            
            # Apply rotation if needed
            angle = self.parameters["angle"]
            if angle != 0:
                height, width = frame.shape[:2]
                center = (width/2, height/2)
                rotation_matrix = cv2.getRotationMatrix2D(
                    center, angle, 1.0
                )
                frame = cv2.warpAffine(
                    frame, 
                    rotation_matrix, 
                    (width, height),
                    flags=cv2.INTER_LINEAR
                )
            
            return frame
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Rotation effect")
            return frame

class EffectChain:
    """Manages a chain of video effects."""
    
    def __init__(self):
        self.effects: List[BaseVideoEffect] = []
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)

    def add_effect(self, effect: BaseVideoEffect, position: Optional[int] = None) -> bool:
        """Add effect to chain."""
        try:
            if position is None:
                self.effects.append(effect)
            else:
                self.effects.insert(position, effect)
            return True
        except Exception as e:
            self.error_handler.handle_error(e, context="Adding effect")
            return False

    def remove_effect(self, index: int) -> bool:
        """Remove effect from chain."""
        try:
            if 0 <= index < len(self.effects):
                self.effects.pop(index)
                return True
            return False
        except Exception as e:
            self.error_handler.handle_error(e, context="Removing effect")
            return False

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process frame through effect chain."""
        try:
            result = frame.copy()
            for effect in self.effects:
                if effect.enabled:
                    result = effect.process(result)
            return result
        except Exception as e:
            self.error_handler.handle_error(e, context="Processing frame")
            return frame

    def get_chain_config(self) -> List[Dict]:
        """Get configuration of all effects in chain."""
        return [effect.get_config() for effect in self.effects]

class EffectPreset:
    """Manages effect presets."""
    
    def __init__(self, name: str, effects: List[Dict]):
        self.name = name
        self.effects = effects
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)

    def apply_to_chain(self, chain: EffectChain) -> bool:
        """Apply preset to effect chain."""
        try:
            # Clear existing effects
            chain.effects.clear()
            
            # Mapping of effect types
            effect_classes = {
                'color_correction': ColorCorrectionEffect,
                'chroma_key': ChromaKeyEffect,
                'blur': BlurEffect,
                'sharpness': SharpnessEffect,
                'noise_reduction': NoiseReductionEffect,
                'color_balance': ColorBalanceEffect,
                'vignette': VignetteEffect,
                'film_grain': FilmGrainEffect,
                'rotation': RotationEffect
            }
            
            # Add preset effects
            for effect_config in self.effects:
                # Normalize effect type
                effect_type = effect_config.get('type', '').lower()
                effect_type = effect_type.replace(' ', '_')
                
                # Find matching effect class
                effect_class = next((cls for key, cls in effect_classes.items() 
                                     if effect_type in key), None)
                
                if effect_class:
                    # Create effect instance
                    name = effect_config.get('name', effect_type)
                    effect = effect_class(name)
                    
                    # Configure parameters
                    for param, value in effect_config.items():
                        if param not in ['type', 'name']:
                            effect.set_parameter(param, value)
                    
                    # Add to chain
                    chain.add_effect(effect)
                else:
                    self.logger.warning(f"Unknown effect type: {effect_type}")
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Applying preset")
            return False

class VideoProcessor:
    """Manages video processing and effects."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)
        self.effect_chains: Dict[str, EffectChain] = {}
        self.processing = False
        self.input_queue = queue.Queue(maxsize=10)
        self.output_queue = queue.Queue(maxsize=10)
        
        # Performance monitoring
        self.processing_times: List[float] = []
        self.dropped_frames = 0
        
        self.register_default_chains()

    def register_default_chains(self):
        """Register default effect chains."""
        try:
            # Main processing chain
            self.effect_chains['main'] = EffectChain()
            
            # Preview chain (lighter effects for preview)
            self.effect_chains['preview'] = EffectChain()
            
            # Recording chain (optimized for recording)
            self.effect_chains['recording'] = EffectChain()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Registering default chains")

    def add_effect_to_chain(self, chain_name: str, effect: BaseVideoEffect, 
                          position: Optional[int] = None) -> bool:
        """Add effect to specified chain."""
        try:
            if chain_name in self.effect_chains:
                return self.effect_chains[chain_name].add_effect(effect, position)
            return False
        except Exception as e:
            self.error_handler.handle_error(e, context="Adding effect to chain")
            return False

    def process_frame(self, frame: np.ndarray, chain_name: str = 'main') -> np.ndarray:
        """Process frame through specified effect chain."""
        try:
            if chain_name in self.effect_chains:
                return self.effect_chains[chain_name].process_frame(frame)
            return frame
        except Exception as e:
            self.error_handler.handle_error(e, context="Processing frame")
            return frame

    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop any ongoing processing
            self.processing = False
            
            # Clear queues
            while not self.input_queue.empty():
                self.input_queue.get()
            while not self.output_queue.empty():
                self.output_queue.get()
            
            # Reset statistics
            self.processing_times.clear()
            self.dropped_frames = 0
            
        except Exception as e:
            self.logger.error(f"Error during video processor cleanup: {e}")