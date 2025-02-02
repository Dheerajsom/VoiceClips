# src/features/transitions.py

import cv2
import numpy as np
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Type
from enum import Enum
import threading
from queue import Queue
import time

class TransitionType(Enum):
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE_LEFT = "wipe_left"
    WIPE_RIGHT = "wipe_right"
    WIPE_UP = "wipe_up"
    WIPE_DOWN = "wipe_down"
    ZOOM = "zoom"
    BLUR = "blur"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"

class Transition(ABC):
    """Base class for transitions."""
    
    def __init__(self, duration: float = 1.0):
        self.duration = duration
        self.progress = 0.0
        self.completed = False

    @abstractmethod
    def process(self, frame1: np.ndarray, frame2: np.ndarray, 
               progress: float) -> np.ndarray:
        """Process transition between two frames."""
        pass

    def reset(self):
        """Reset transition state."""
        self.progress = 0.0
        self.completed = False

class CutTransition(Transition):
    """Instant cut transition."""
    
    def process(self, frame1: np.ndarray, frame2: np.ndarray, 
               progress: float) -> np.ndarray:
        return frame2 if progress >= 0.5 else frame1

class FadeTransition(Transition):
    """Fade transition."""
    
    def process(self, frame1: np.ndarray, frame2: np.ndarray, 
               progress: float) -> np.ndarray:
        return cv2.addWeighted(frame1, 1 - progress, frame2, progress, 0)

class DissolveTransition(Transition):
    """Dissolve transition with noise pattern."""
    
    def __init__(self, duration: float = 1.0):
        super().__init__(duration)
        self.noise_pattern = None

    def process(self, frame1: np.ndarray, frame2: np.ndarray, 
               progress: float) -> np.ndarray:
        if self.noise_pattern is None or \
           self.noise_pattern.shape != frame1.shape:
            self.noise_pattern = np.random.random(frame1.shape)

        threshold = 1 - progress
        mask = (self.noise_pattern > threshold).astype(np.float32)
        return frame1 * (1 - mask) + frame2 * mask

class WipeTransition(Transition):
    """Base class for wipe transitions."""
    
    def __init__(self, duration: float = 1.0, direction: str = "left"):
        super().__init__(duration)
        self.direction = direction

    def process(self, frame1: np.ndarray, frame2: np.ndarray, 
               progress: float) -> np.ndarray:
        h, w = frame1.shape[:2]
        
        if self.direction in ["left", "right"]:
            split = int(w * (progress if self.direction == "left" else 1 - progress))
            if self.direction == "left":
                frame1[:, :split] = frame2[:, :split]
            else:
                frame1[:, split:] = frame2[:, split:]
        else:  # up or down
            split = int(h * (progress if self.direction == "up" else 1 - progress))
            if self.direction == "up":
                frame1[:split, :] = frame2[:split, :]
            else:
                frame1[split:, :] = frame2[split:, :]
                
        return frame1

class ZoomTransition(Transition):
    """Zoom transition effect."""
    
    def process(self, frame1: np.ndarray, frame2: np.ndarray, 
               progress: float) -> np.ndarray:
        h, w = frame1.shape[:2]
        
        # Zoom out first frame
        scale1 = 1 + progress
        scaled_h1 = int(h * scale1)
        scaled_w1 = int(w * scale1)
        scaled1 = cv2.resize(frame1, (scaled_w1, scaled_h1))
        
        # Zoom in second frame
        scale2 = 2 - progress
        scaled_h2 = int(h * scale2)
        scaled_w2 = int(w * scale2)
        scaled2 = cv2.resize(frame2, (scaled_w2, scaled_h2))
        
        # Crop to original size
        y1 = (scaled_h1 - h) // 2
        x1 = (scaled_w1 - w) // 2
        y2 = (scaled_h2 - h) // 2
        x2 = (scaled_w2 - w) // 2
        
        cropped1 = scaled1[y1:y1+h, x1:x1+w]
        cropped2 = scaled2[y2:y2+h, x2:x2+w]
        
        # Blend frames
        return cv2.addWeighted(cropped1, 1 - progress, cropped2, progress, 0)

class BlurTransition(Transition):
    """Blur transition effect."""
    
    def process(self, frame1: np.ndarray, frame2: np.ndarray, 
               progress: float) -> np.ndarray:
        if progress < 0.5:
            # Progressively blur first frame
            blur_amount = int(40 * (progress * 2)) * 2 + 1
            blurred = cv2.GaussianBlur(frame1, (blur_amount, blur_amount), 0)
            return cv2.addWeighted(frame1, 1 - (progress * 2), blurred, progress * 2, 0)
        else:
            # Progressively unblur second frame
            blur_amount = int(40 * ((1 - progress) * 2)) * 2 + 1
            blurred = cv2.GaussianBlur(frame2, (blur_amount, blur_amount), 0)
            progress = (progress - 0.5) * 2
            return cv2.addWeighted(blurred, 1 - progress, frame2, progress, 0)

class SlideTransition(Transition):
    """Slide transition effect."""
    
    def __init__(self, duration: float = 1.0, direction: str = "left"):
        super().__init__(duration)
        self.direction = direction

    def process(self, frame1: np.ndarray, frame2: np.ndarray, 
               progress: float) -> np.ndarray:
        h, w = frame1.shape[:2]
        result = np.zeros_like(frame1)
        
        if self.direction == "left":
            offset = int(w * progress)
            result[:, :w-offset] = frame1[:, offset:]
            result[:, w-offset:] = frame2[:, :offset]
        else:  # right
            offset = int(w * progress)
            result[:, offset:] = frame1[:, :w-offset]
            result[:, :offset] = frame2[:, w-offset:]
            
        return result

class TransitionManager:
    """Manages scene transitions."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.transitions: Dict[TransitionType, Type[Transition]] = {
            TransitionType.CUT: CutTransition,
            TransitionType.FADE: FadeTransition,
            TransitionType.DISSOLVE: DissolveTransition,
            TransitionType.WIPE_LEFT: lambda d: WipeTransition(d, "left"),
            TransitionType.WIPE_RIGHT: lambda d: WipeTransition(d, "right"),
            TransitionType.WIPE_UP: lambda d: WipeTransition(d, "up"),
            TransitionType.WIPE_DOWN: lambda d: WipeTransition(d, "down"),
            TransitionType.ZOOM: ZoomTransition,
            TransitionType.BLUR: BlurTransition,
            TransitionType.SLIDE_LEFT: lambda d: SlideTransition(d, "left"),
            TransitionType.SLIDE_RIGHT: lambda d: SlideTransition(d, "right")
        }
        
        self.current_transition: Optional[Transition] = None
        self.transition_thread: Optional[threading.Thread] = None
        self.frame_queue = Queue(maxsize=2)
        self.result_queue = Queue(maxsize=1)
        self.is_transitioning = False

    def start_transition(self, transition_type: TransitionType, 
                        duration: float = 1.0) -> bool:
        """Start a new transition."""
        try:
            if self.is_transitioning:
                return False
                
            transition_class = self.transitions.get(transition_type)
            if not transition_class:
                raise ValueError(f"Unknown transition type: {transition_type}")
                
            self.current_transition = transition_class(duration)
            self.is_transitioning = True
            
            self.transition_thread = threading.Thread(
                target=self._transition_loop,
                daemon=True
            )
            self.transition_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting transition: {e}")
            return False

    def process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Process frame through current transition."""
        try:
            if not self.is_transitioning:
                return frame
                
            if self.frame_queue.qsize() < 2:
                self.frame_queue.put(frame)
                return None
                
            try:
                return self.result_queue.get_nowait()
            except:
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            return frame

    def _transition_loop(self):
        """Main transition processing loop."""
        try:
            frame1 = self.frame_queue.get()
            frame2 = self.frame_queue.get()
            
            start_time = time.time()
            
            while self.is_transitioning:
                elapsed = time.time() - start_time
                progress = min(1.0, elapsed / self.current_transition.duration)
                
                result = self.current_transition.process(frame1, frame2, progress)
                
                try:
                    self.result_queue.put_nowait(result)
                except:
                    pass
                
                if progress >= 1.0:
                    self.is_transitioning = False
                    break
                    
                time.sleep(1/60)  # Limit to 60 FPS
                
        except Exception as e:
            self.logger.error(f"Error in transition loop: {e}")
        finally:
            self.is_transitioning = False

    def stop_transition(self):
        """Stop current transition."""
        self.is_transitioning = False
        if self.transition_thread:
            self.transition_thread.join()
            self.transition_thread = None
        
        # Clear queues
        while not self.frame_queue.empty():
            self.frame_queue.get()
        while not self.result_queue.empty():
            self.result_queue.get()

    def cleanup(self):
        """Clean up resources."""
        self.stop_transition()