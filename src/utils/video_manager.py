# src/utils/video_manager.py
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
import cv2
import numpy as np
import mss
import logging
from typing import Optional, Dict, List, Tuple, Any
import threading
import queue
from dataclasses import dataclass
import time
from pathlib import Path

from src.constants import *
from src.utils.error_handler import ErrorHandler
from src.utils.performance import PerformanceUtils
from src.features.video_effects import VideoProcessor

@dataclass
class VideoFrame:
    """Represents a video frame with metadata."""
    data: np.ndarray
    timestamp: float
    frame_number: int
    resolution: Tuple[int, int]
    format: str = 'BGR'

    def copy(self):
        """Create a copy of the frame."""
        return VideoFrame(
            data=self.data.copy(),
            timestamp=self.timestamp,
            frame_number=self.frame_number,
            resolution=self.resolution,
            format=self.format
    )

class VideoDevice:
    """Represents a video capture device."""
    def __init__(self, id: str, name: str, type: str = 'camera'):
        self.id = id
        self.name = name
        self.type = type  # camera, screen, custom
        self.capabilities: Dict[str, Any] = {}
        self.current_settings: Dict[str, Any] = {}

class VideoManager:
    """Manages video capture and processing."""
    
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
            'current_fps': 0,
            'average_frame_time': 0
        }

    def init_components(self):
        """Initialize video components."""
        try:
            # Screen capture
            self.sct = mss.mss()
            
            # Video processor for effects
            self.video_processor = VideoProcessor()
            
            # Threading control
            self.is_capturing = False
            self.capture_thread: Optional[threading.Thread] = None
            
            # Current settings
            self.current_device: Optional[VideoDevice] = None
            self.frame_size = tuple(map(int, BASE_CANVAS_RESOLUTION.split('x')))
            self.target_fps = DEFAULT_FPS
            self.quality = "High"
            
            # Available devices
            self.devices = self.discover_devices()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Initializing video components")
            raise

    def setup_buffers(self):
        """Setup frame buffers and queues."""
        try:
            # Frame buffers
            buffer_size = self.target_fps * 5  # 5 seconds buffer
            self.frame_buffer = queue.Queue(maxsize=buffer_size)
            self.preview_buffer = queue.Queue(maxsize=30)  # 1 second preview buffer
            
            # Processing queues
            self.processing_queue = queue.Queue(maxsize=buffer_size)
            self.output_queue = queue.Queue(maxsize=buffer_size)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Setting up buffers")
            raise

    def discover_devices(self) -> Dict[str, VideoDevice]:
        """Discover available video devices."""
        devices = {}
        try:
            # Add screen capture devices
            for i, monitor in enumerate(self.sct.monitors[1:], 1):
                device = VideoDevice(
                    id=f"screen_{i}",
                    name=f"Screen {i}",
                    type='screen'
                )
                device.capabilities = {
                    'resolution': (monitor['width'], monitor['height']),
                    'position': (monitor['left'], monitor['top'])
                }
                devices[device.id] = device

            # Add camera devices
            for i in range(10):  # Check first 10 indexes
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    device = VideoDevice(
                        id=f"camera_{i}",
                        name=f"Camera {i}",
                        type='camera'
                    )
                    device.capabilities = self._get_camera_capabilities(cap)
                    devices[device.id] = device
                    cap.release()

            return devices

        except Exception as e:
            self.error_handler.handle_error(e, context="Discovering devices")
            return {}

    def _get_camera_capabilities(self, cap: cv2.VideoCapture) -> Dict:
        """Get camera device capabilities."""
        caps = {}
        try:
            caps['resolution'] = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
            caps['fps'] = cap.get(cv2.CAP_PROP_FPS)
            caps['backend'] = cap.get(cv2.CAP_PROP_BACKEND)
            caps['auto_focus'] = cap.get(cv2.CAP_PROP_AUTOFOCUS)
            caps['auto_exposure'] = cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            return caps
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting camera capabilities")
            return {}

    def start_capture(self, device_id: str = None) -> bool:
        """Start video capture."""
        try:
            if self.is_capturing:
                return False

            # Select device
            if device_id and device_id in self.devices:
                self.current_device = self.devices[device_id]
            elif not self.current_device:
                # Default to first screen
                screen_devices = [d for d in self.devices.values() 
                                if d.type == 'screen']
                if screen_devices:
                    self.current_device = screen_devices[0]
                else:
                    raise Exception("No capture device available")

            # Start capture thread
            self.is_capturing = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.capture_thread.start()

            self.logger.info(f"Started capture on device: {self.current_device.name}")
            return True

        except Exception as e:
            self.error_handler.handle_error(e, context="Starting capture")
            return False

    def stop_capture(self):
        """Stop video capture."""
        try:
            self.is_capturing = False
            if self.capture_thread:
                self.capture_thread.join()
                self.capture_thread = None
            
            # Clear buffers
            self.clear_buffers()
            
            self.logger.info("Stopped video capture")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Stopping capture")

    def _capture_loop(self):
        """Main capture loop."""
        last_frame_time = time.time()
        frame_count = 0
        fps_update_time = last_frame_time
        
        try:
            while self.is_capturing:
                current_time = time.time()
                
                # Maintain target FPS
                if current_time - last_frame_time < 1.0 / self.target_fps:
                    continue

                # Capture frame
                frame = self._capture_frame()
                if frame is None:
                    continue

                # Create frame object
                frame_obj = VideoFrame(
                    data=frame,
                    timestamp=current_time,
                    frame_number=frame_count,
                    resolution=self.frame_size
                )

                # Add to buffers
                self._add_to_buffers(frame_obj)

                # Update statistics
                frame_count += 1
                if current_time - fps_update_time >= 1.0:
                    self.stats['current_fps'] = frame_count
                    self.stats['frames_captured'] += frame_count
                    frame_count = 0
                    fps_update_time = current_time

                last_frame_time = current_time

        except Exception as e:
            self.error_handler.handle_error(e, context="Capture loop")
            self.is_capturing = False
    def _capture_frame(self) -> Optional[np.ndarray]:
        """Capture frame from current device."""
        try:
            if self.current_device.type == 'screen':
                return self._capture_screen()
            elif self.current_device.type == 'camera':
                return self._capture_camera()
            return None
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Capturing frame")
            return None

    def _capture_screen(self) -> Optional[np.ndarray]:
        """Capture screen frame."""
        try:
            # Get monitor index
            monitor_idx = int(self.current_device.id.split('_')[1])
            monitor = self.sct.monitors[monitor_idx]
            
            # Capture screenshot
            screenshot = self.sct.grab(monitor)
            
            # Convert to numpy array
            frame = np.array(screenshot)
            
            # Convert from BGRA to BGR
            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
            # Calculate aspect ratio preserving resize
            screen_h, screen_w = frame.shape[:2]
            target_w, target_h = self.frame_size
            
            # Calculate scaling factor while maintaining aspect ratio
            scale = min(target_w/screen_w, target_h/screen_h)
            new_w = int(screen_w * scale)
            new_h = int(screen_h * scale)
            
            # Resize frame
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Create black canvas of target size
            canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            
            # Calculate position to center the frame
            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2
            
            # Place frame on canvas
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame
            
            return canvas
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Screen capture")
            return None
    def _capture_camera(self) -> Optional[np.ndarray]:
        """Capture camera frame."""
        try:
            with self.performance.timeit():
                # Get camera index
                camera_idx = int(self.current_device.id.split('_')[1])
                
                # Open camera if needed
                if not hasattr(self, 'camera') or self.camera is None:
                    self.camera = cv2.VideoCapture(camera_idx)
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])
                    self.camera.set(cv2.CAP_PROP_FPS, self.target_fps)
                
                # Read frame
                ret, frame = self.camera.read()
                if not ret:
                    raise Exception("Failed to read camera frame")
                
                # Resize if needed
                if frame.shape[:2] != self.frame_size:
                    frame = cv2.resize(frame, self.frame_size)
                
                return frame
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Camera capture")
            return None

    def _add_to_buffers(self, frame: VideoFrame):
        """Add frame to buffers."""
        try:
            # Add to main buffer
            if not self.frame_buffer.full():
                self.frame_buffer.put(frame)
            else:
                self.stats['frames_dropped'] += 1
            
            # Add to preview buffer
            if not self.preview_buffer.full():
                self.preview_buffer.put(frame)
            else:
                # Remove oldest frame
                try:
                    self.preview_buffer.get_nowait()
                except queue.Empty:
                    pass
                self.preview_buffer.put(frame)
            
            # Add to processing queue
            if not self.processing_queue.full():
                self.processing_queue.put(frame)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Adding to buffers")

    def get_frame(self) -> Optional[VideoFrame]:
        """Get latest frame."""
        try:
            return self.frame_buffer.get_nowait()
        except queue.Empty:
            return None
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting frame")
            return None

    def get_preview_frame(self) -> Optional[VideoFrame]:
        """Get frame for preview."""
        try:
            return self.preview_buffer.get_nowait()
        except queue.Empty:
            return None
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting preview frame")
            return None

    def clear_buffers(self):
        """Clear all frame buffers."""
        try:
            while not self.frame_buffer.empty():
                self.frame_buffer.get_nowait()
            while not self.preview_buffer.empty():
                self.preview_buffer.get_nowait()
            while not self.processing_queue.empty():
                self.processing_queue.get_nowait()
            while not self.output_queue.empty():
                self.output_queue.get_nowait()
        except Exception as e:
            self.error_handler.handle_error(e, context="Clearing buffers")

    def update_settings(self, settings: Dict[str, Any]):
        """Update video settings."""
        try:
            # Update resolution
            if 'resolution' in settings:
                new_size = tuple(map(int, settings['resolution'].split('x')))
                if new_size != self.frame_size:
                    self.frame_size = new_size
                    # Restart capture if active
                    if self.is_capturing:
                        self.stop_capture()
                        self.start_capture(self.current_device.id)
            
            # Update FPS
            if 'fps' in settings:
                self.target_fps = int(settings['fps'])
            
            # Update quality
            if 'quality' in settings:
                self.quality = settings['quality']
            
            # Update device
            if 'device' in settings and settings['device'] in self.devices:
                if self.is_capturing:
                    self.stop_capture()
                self.start_capture(settings['device'])
            
            self.logger.info("Video settings updated successfully")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Updating settings")

    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """Get detailed device information."""
        try:
            if device_id not in self.devices:
                return None
                
            device = self.devices[device_id]
            return {
                'id': device.id,
                'name': device.name,
                'type': device.type,
                'capabilities': device.capabilities,
                'current_settings': device.current_settings
            }
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting device info")
            return None

    def get_statistics(self) -> Dict:
        """Get capture statistics."""
        try:
            return {
                'frames_captured': self.stats['frames_captured'],
                'frames_dropped': self.stats['frames_dropped'],
                'current_fps': self.stats['current_fps'],
                'average_frame_time': self.stats['average_frame_time'],
                'buffer_usage': {
                    'main': self.frame_buffer.qsize() / self.frame_buffer.maxsize,
                    'preview': self.preview_buffer.qsize() / self.preview_buffer.maxsize,
                    'processing': self.processing_queue.qsize() / self.processing_queue.maxsize
                }
            }
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting statistics")
            return {}

    def save_frame(self, frame: VideoFrame, filepath: str) -> bool:
        """Save frame to file."""
        try:
            return cv2.imwrite(filepath, frame.data)
        except Exception as e:
            self.error_handler.handle_error(e, context="Saving frame")
            return False
    def get_current_timestamp(self) -> float:
        """Get current video timestamp."""
        return time.time() - self._start_time if hasattr(self, '_start_time') else 0

    def reset_timestamp(self):
        """Reset video timestamp."""
        self._start_time = time.time()

    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop capture
            self.stop_capture()
            
            # Release camera if used
            if hasattr(self, 'camera') and self.camera is not None:
                self.camera.release()
            
            # Close screen capture
            self.sct.close()
            
            # Clear buffers
            self.clear_buffers()
            
            # Clean up video processor
            self.video_processor.cleanup()
            
            self.logger.info("Video manager cleanup completed")
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Video manager cleanup")