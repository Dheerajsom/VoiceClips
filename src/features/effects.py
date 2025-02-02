import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


import cv2
import numpy as np
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional,List

from src.constants import DEFAULT_LOGS_PATH
from src.utils.error_handler import ErrorHandler

class BaseVideoEffect(ABC):
    """Base class for video effects."""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.parameters: Dict[str, Any] = {}
        self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)
        self.logger = logging.getLogger(__name__)
        
        # Setup initial parameters
        self.setup_parameters()

    @abstractmethod
    def setup_parameters(self):
        """Setup effect parameters."""
        pass

    @abstractmethod
    def process(self, frame: np.ndarray) -> np.ndarray:
        """Process a single frame."""
        pass

    def set_parameter(self, name: str, value: Any):
        """Set effect parameter."""
        if name in self.parameters:
            self.parameters[name] = value
        else:
            self.logger.warning(f"Parameter {name} not found in {self.name} effect")

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get effect parameter."""
        return self.parameters.get(name, default)

    def get_config(self) -> Dict:
        """Get effect configuration."""
        return {
            'name': self.name,
            'type': self.__class__.__name__.lower().replace('effect', ''),
            'enabled': self.enabled,
            'parameters': self.parameters.copy()
        }

class ChromaKeyEffect(BaseVideoEffect):
    """Chroma key (green screen) effect."""
    
    def setup_parameters(self):
        self.parameters = {
            'key_color': [0, 255, 0],  # Green
            'similarity' : 40,
            'threshold': 40,
            'blur': 5,
            'spill_reduction': 0.2
        }

    def process(self, frame: np.ndarray) -> np.ndarray:
        try:
            # Convert to HSV color space
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Get parameters
            key_color = np.uint8([[self.parameters['key_color']]])
            key_hsv = cv2.cvtColor(key_color, cv2.COLOR_BGR2HSV)
            threshold = self.parameters['threshold']
            
            # Create mask
            lower_bound = np.array([key_hsv[0][0][0] - threshold, 100, 100])
            upper_bound = np.array([key_hsv[0][0][0] + threshold, 255, 255])
            mask = cv2.inRange(hsv, lower_bound, upper_bound)
            
            # Apply blur
            mask = cv2.GaussianBlur(mask, 
                                  (self.parameters['blur']*2 + 1, 
                                   self.parameters['blur']*2 + 1), 0)
            
            # Invert mask
            mask_inv = cv2.bitwise_not(mask)
            
            # Extract foreground
            fg = cv2.bitwise_and(frame, frame, mask=mask_inv)
            
            return fg
            
        except Exception as e:
            self.logger.error(f"Error in chroma key effect: {e}")
            return frame

class ColorCorrectionEffect(BaseVideoEffect):
    """Color correction effect."""
    
    def setup_parameters(self):
        self.parameters = {
            'brightness': 1.0,
            'contrast': 1.0,
            'saturation': 1.0,
            'temperature': 0,
            'tint': 0
        }

    def process(self, frame: np.ndarray) -> np.ndarray:
        try:
            # Apply brightness and contrast
            frame = cv2.convertScaleAbs(
                frame,
                alpha=self.parameters['contrast'],
                beta=self.parameters['brightness'] * 50
            )
            
            # Apply saturation
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hsv[..., 1] = hsv[..., 1] * self.parameters['saturation']
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            
            # Apply temperature
            if self.parameters['temperature'] != 0:
                temp = self.parameters['temperature']
                frame = cv2.add(frame, np.array([temp * -1, 0, temp]))
                
            # Apply tint
            if self.parameters['tint'] != 0:
                tint = self.parameters['tint']
                frame = cv2.add(frame, np.array([0, tint, 0]))
                
            return frame
            
        except Exception as e:
            self.logger.error(f"Error in color correction effect: {e}")
            return frame

class BlurEffect(BaseVideoEffect):
    """Blur effect."""
    
    def setup_parameters(self):
        self.parameters = {
            'radius': 5,
            'type': 'gaussian'  # gaussian, box, or median
        }

    def process(self, frame: np.ndarray) -> np.ndarray:
        try:
            radius = self.parameters['radius'] * 2 + 1
            blur_type = self.parameters['type']
            
            if blur_type == 'gaussian':
                return cv2.GaussianBlur(frame, (radius, radius), 0)
            elif blur_type == 'box':
                return cv2.blur(frame, (radius, radius))
            elif blur_type == 'median':
                return cv2.medianBlur(frame, radius)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error in blur effect: {e}")
            return frame

class EffectsManager:
    """Manages video effects and processing."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.effects: Dict[str, BaseVideoEffect] = {}
        self.effect_chain: List[str] = []
        
        # Register default effects
        self.register_default_effects()

    def register_default_effects(self):
        """Register built-in effects."""
        self.register_effect(ChromaKeyEffect('Chroma Key'))
        self.register_effect(ColorCorrectionEffect('Color Correction'))
        self.register_effect(BlurEffect('Blur'))

    def register_effect(self, effect: BaseVideoEffect) -> bool:
        """Register a new effect."""
        try:
            self.effects[effect.name] = effect
            return True
        except Exception as e:
            self.logger.error(f"Error registering effect {effect.name}: {e}")
            return False

    def add_to_chain(self, effect_name: str) -> bool:
        """Add effect to processing chain."""
        if effect_name not in self.effects:
            return False
            
        if effect_name not in self.effect_chain:
            self.effect_chain.append(effect_name)
        return True

    def remove_from_chain(self, effect_name: str) -> bool:
        """Remove effect from processing chain."""
        try:
            self.effect_chain.remove(effect_name)
            return True
        except ValueError:
            return False

    def move_effect(self, effect_name: str, new_position: int) -> bool:
        """Move effect to new position in chain."""
        try:
            current_position = self.effect_chain.index(effect_name)
            self.effect_chain.pop(current_position)
            self.effect_chain.insert(new_position, effect_name)
            return True
        except ValueError:
            return False

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process frame through effect chain."""
        try:
            processed_frame = frame.copy()
            
            for effect_name in self.effect_chain:
                effect = self.effects.get(effect_name)
                if effect and effect.enabled:
                    processed_frame = effect.process(processed_frame)
                    
            return processed_frame
            
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            return frame

    def get_effect(self, name: str) -> Optional[BaseVideoEffect]:
        """Get effect by name."""
        return self.effects.get(name)

    def get_effect_chain(self) -> List[str]:
        """Get current effect chain."""
        return self.effect_chain.copy()

    def clear_chain(self):
        """Clear effect chain."""
        self.effect_chain.clear()