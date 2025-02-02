# src/features/scene_composition.py

import cv2
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import threading

class BlendMode(Enum):
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    ADD = "add"

@dataclass
class Transform:
    position: Tuple[float, float] = (0.0, 0.0)
    scale: Tuple[float, float] = (1.0, 1.0)
    rotation: float = 0.0
    crop: Tuple[int, int, int, int] = (0, 0, 0, 0)  # left, top, right, bottom

class SceneItem:
    def __init__(self, name: str, source: Any, item_type: str):
        self.name = name
        self.source = source
        self.type = item_type
        self.transform = Transform()
        self.blend_mode = BlendMode.NORMAL
        self.opacity = 1.0
        self.visible = True
        self.filters = []
        self.locked = False
        self.z_index = 0

    def get_transform_matrix(self) -> np.ndarray:
        """Get transformation matrix."""
        # Translation matrix
        tx, ty = self.transform.position
        translation = np.array([
            [1, 0, tx],
            [0, 1, ty],
            [0, 0, 1]
        ])

        # Rotation matrix (around center)
        angle = np.radians(self.transform.rotation)
        c, s = np.cos(angle), np.sin(angle)
        rotation = np.array([
            [c, -s, 0],
            [s, c, 0],
            [0, 0, 1]
        ])

        # Scale matrix
        sx, sy = self.transform.scale
        scale = np.array([
            [sx, 0, 0],
            [0, sy, 0],
            [0, 0, 1]
        ])

        # Combine transformations
        return translation @ rotation @ scale

class Scene:
    def __init__(self, name: str):
        self.name = name
        self.items: List[SceneItem] = []
        self.size = (1920, 1080)
        self.background_color = (0, 0, 0)
        self.active = False
        self.lock = threading.Lock()

    def add_item(self, item: SceneItem) -> bool:
        """Add item to scene."""
        with self.lock:
            try:
                item.z_index = len(self.items)
                self.items.append(item)
                self._sort_items()
                return True
            except Exception as e:
                logging.error(f"Error adding scene item: {e}")
                return False

    def remove_item(self, item: SceneItem) -> bool:
        """Remove item from scene."""
        with self.lock:
            try:
                self.items.remove(item)
                self._sort_items()
                return True
            except Exception as e:
                logging.error(f"Error removing scene item: {e}")
                return False

    def _sort_items(self):
        """Sort items by z-index."""
        self.items.sort(key=lambda x: x.z_index)

    def render(self) -> np.ndarray:
        """Render scene."""
        with self.lock:
            try:
                # Create base canvas
                canvas = np.zeros((*self.size, 3), dtype=np.uint8)
                canvas[:] = self.background_color

                # Render each item
                for item in self.items:
                    if not item.visible:
                        continue

                    # Get source frame
                    frame = self._get_source_frame(item)
                    if frame is None:
                        continue

                    # Apply transformations
                    frame = self._apply_transform(frame, item)

                    # Apply filters
                    frame = self._apply_filters(frame, item)

                    # Composite onto canvas
                    canvas = self._composite_frame(canvas, frame, item)

                return canvas

            except Exception as e:
                logging.error(f"Error rendering scene: {e}")
                return np.zeros((*self.size, 3), dtype=np.uint8)

    def _get_source_frame(self, item: SceneItem) -> Optional[np.ndarray]:
        """Get frame from source."""
        try:
            if item.type == "video":
                return item.source.get_frame()
            elif item.type == "image":
                return item.source
            elif item.type == "color":
                return np.full((*self.size, 3), item.source, dtype=np.uint8)
            return None
        except Exception as e:
            logging.error(f"Error getting source frame: {e}")
            return None

    def _apply_transform(self, frame: np.ndarray, item: SceneItem) -> np.ndarray:
        """Apply transformations to frame."""
        try:
            # Apply crop
            l, t, r, b = item.transform.crop
            if any((l, t, r, b)):
                frame = frame[t:-b if b else None, l:-r if r else None]

            # Get transform matrix
            matrix = item.get_transform_matrix()

            # Apply transform
            return cv2.warpAffine(
                frame,
                matrix[:2],
                self.size,
                flags=cv2.INTER_LINEAR
            )

        except Exception as e:
            logging.error(f"Error applying transform: {e}")
            return frame

    def _apply_filters(self, frame: np.ndarray, item: SceneItem) -> np.ndarray:
        """Apply filters to frame."""
        try:
            for filter in item.filters:
                if filter.enabled:
                    frame = filter.process(frame)
            return frame
        except Exception as e:
            logging.error(f"Error applying filters: {e}")
            return frame

    def _composite_frame(self, canvas: np.ndarray, frame: np.ndarray, 
                        item: SceneItem) -> np.ndarray:
        """Composite frame onto canvas."""
        try:
            # Create alpha mask
            alpha = np.full(frame.shape[:2], item.opacity * 255, dtype=np.uint8)

            # Apply blend mode
            if item.blend_mode == BlendMode.NORMAL:
                return self._blend_normal(canvas, frame, alpha)
            elif item.blend_mode == BlendMode.MULTIPLY:
                return self._blend_multiply(canvas, frame, alpha)
            elif item.blend_mode == BlendMode.SCREEN:
                return self._blend_screen(canvas, frame, alpha)
            elif item.blend_mode == BlendMode.OVERLAY:
                return self._blend_overlay(canvas, frame, alpha)
            elif item.blend_mode == BlendMode.ADD:
                return self._blend_add(canvas, frame, alpha)

            return canvas

        except Exception as e:
            logging.error(f"Error compositing frame: {e}")
            return canvas

    def _blend_normal(self, bg: np.ndarray, fg: np.ndarray, 
                     alpha: np.ndarray) -> np.ndarray:
        """Normal blend mode."""
        alpha = alpha.astype(float) / 255
        alpha = np.expand_dims(alpha, axis=2)
        return (bg * (1 - alpha) + fg * alpha).astype(np.uint8)

    def _blend_multiply(self, bg: np.ndarray, fg: np.ndarray, 
                       alpha: np.ndarray) -> np.ndarray:
        """Multiply blend mode."""
        alpha = alpha.astype(float) / 255
        alpha = np.expand_dims(alpha, axis=2)
        blended = (bg.astype(float) * fg.astype(float)) / 255
        return (bg * (1 - alpha) + blended * alpha).astype(np.uint8)

    def _blend_screen(self, bg: np.ndarray, fg: np.ndarray, 
                     alpha: np.ndarray) -> np.ndarray:
        """Screen blend mode."""
        alpha = alpha.astype(float) / 255
        alpha = np.expand_dims(alpha, axis=2)
        blended = 255 - ((255 - bg.astype(float)) * 
                        (255 - fg.astype(float))) / 255
        return (bg * (1 - alpha) + blended * alpha).astype(np.uint8)

    def _blend_overlay(self, bg: np.ndarray, fg: np.ndarray, 
                      alpha: np.ndarray) -> np.ndarray:
        """Overlay blend mode."""
        alpha = alpha.astype(float) / 255
        alpha = np.expand_dims(alpha, axis=2)
        
        bg_f = bg.astype(float)
        fg_f = fg.astype(float)
        
        mask = bg_f <= 127.5
        blended = np.where(
            mask,
            (2 * bg_f * fg_f) / 255,
            255 - (2 * (255 - bg_f) * (255 - fg_f)) / 255
        )
        
        return (bg * (1 - alpha) + blended * alpha).astype(np.uint8)

    def _blend_add(self, bg: np.ndarray, fg: np.ndarray, 
                  alpha: np.ndarray) -> np.ndarray:
        """Add blend mode."""
        alpha = alpha.astype(float) / 255
        alpha = np.expand_dims(alpha, axis=2)
        blended = np.minimum(bg.astype(float) + fg.astype(float), 255)
        return (bg * (1 - alpha) + blended * alpha).astype(np.uint8)

class SceneManager:
    def __init__(self):
        self.scenes: Dict[str, Scene] = {}
        self.active_scene: Optional[Scene] = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def create_scene(self, name: str) -> Optional[Scene]:
        """Create new scene."""
        with self.lock:
            try:
                if name in self.scenes:
                    return None
                
                scene = Scene(name)
                self.scenes[name] = scene
                
                if not self.active_scene:
                    self.active_scene = scene
                    scene.active = True
                
                return scene
                
            except Exception as e:
                self.logger.error(f"Error creating scene: {e}")
                return None

    def delete_scene(self, name: str) -> bool:
        """Delete scene."""
        with self.lock:
            try:
                if name not in self.scenes:
                    return False
                
                scene = self.scenes[name]
                if scene == self.active_scene:
                    self.active_scene = None
                    
                del self.scenes[name]
                return True
                
            except Exception as e:
                self.logger.error(f"Error deleting scene: {e}")
                return False

    def switch_scene(self, name: str) -> bool:
        """Switch to scene."""
        with self.lock:
            try:
                if name not in self.scenes:
                    return False
                
                if self.active_scene:
                    self.active_scene.active = False
                    
                self.active_scene = self.scenes[name]
                self.active_scene.active = True
                return True
                
            except Exception as e:
                self.logger.error(f"Error switching scene: {e}")
                return False

    def get_scene(self, name: str) -> Optional[Scene]:
        """Get scene by name."""
        return self.scenes.get(name)

    def get_active_scene(self) -> Optional[Scene]:
        """Get active scene."""
        return self.active_scene

    def render_active_scene(self) -> Optional[np.ndarray]:
        """Render active scene."""
        if self.active_scene:
            return self.active_scene.render()
        return None