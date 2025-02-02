# src/utils/device_manager.py
import sys
import subprocess
import logging
from typing import List, Dict, Optional
import pyaudio

class DeviceManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.audio = pyaudio.PyAudio()
        self.refresh_devices()

    def refresh_devices(self):
        """Refresh device lists."""
        self.video_devices = self._get_video_devices()
        self.audio_devices = self._get_audio_devices()

    def _get_video_devices(self) -> List[Dict]:
        """Get list of video devices."""
        devices = [
            {
                'id': 'screen',
                'name': 'Screen Capture',
                'type': 'screen',
                'default': True
            }
        ]
        
        try:
            # For macOS
            if sys.platform == 'darwin':
                result = subprocess.run(
                    ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                    capture_output=True,
                    text=True
                )
                
                for line in result.stderr.split('\n'):
                    if '[video]' in line and ']' in line:
                        try:
                            index = line.split(']')[0].split('[')[1]
                            name = line.split(']')[1].strip()
                            devices.append({
                                'id': index,
                                'name': name,
                                'type': 'camera',
                                'default': False
                            })
                        except:
                            continue
            
            # For Windows (DirectShow)
            elif sys.platform == 'win32':
                result = subprocess.run(
                    ['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
                    capture_output=True,
                    text=True
                )
                
                capturing = False
                for line in result.stderr.split('\n'):
                    if 'DirectShow video devices' in line:
                        capturing = True
                    elif 'DirectShow audio devices' in line:
                        capturing = False
                    elif capturing and ']' in line:
                        try:
                            name = line.split('"')[1]
                            devices.append({
                                'id': name,
                                'name': name,
                                'type': 'camera',
                                'default': False
                            })
                        except:
                            continue

        except Exception as e:
            self.logger.error(f"Error getting video devices: {e}")
            
        return devices

    def _get_audio_devices(self) -> List[Dict]:
        """Get list of audio devices."""
        devices = []
        
        try:
            for i in range(self.audio.get_device_count()):
                try:
                    device_info = self.audio.get_device_info_by_index(i)
                    if device_info['maxInputChannels'] > 0:
                        devices.append({
                            'id': i,
                            'name': device_info['name'],
                            'type': 'input',
                            'channels': device_info['maxInputChannels'],
                            'default': device_info['index'] == self.audio.get_default_input_device_info()['index']
                        })
                    if device_info['maxOutputChannels'] > 0:
                        devices.append({
                            'id': i,
                            'name': device_info['name'],
                            'type': 'output',
                            'channels': device_info['maxOutputChannels'],
                            'default': device_info['index'] == self.audio.get_default_output_device_info()['index']
                        })
                except:
                    continue

        except Exception as e:
            self.logger.error(f"Error getting audio devices: {e}")
            
        return devices

    def get_default_devices(self) -> Dict[str, str]:
        """Get default devices."""
        return {
            'video': next((d['id'] for d in self.video_devices if d['default']), 'screen'),
            'audio_input': next((str(d['id']) for d in self.audio_devices 
                               if d['default'] and d['type'] == 'input'), '0'),
            'audio_output': next((str(d['id']) for d in self.audio_devices 
                                if d['default'] and d['type'] == 'output'), '0')
        }

    def get_device_info(self, device_id: str, device_type: str) -> Optional[Dict]:
        """Get device information."""
        if device_type == 'video':
            return next((d for d in self.video_devices if str(d['id']) == str(device_id)), None)
        else:
            return next((d for d in self.audio_devices if str(d['id']) == str(device_id)), None)

    def cleanup(self):
        """Clean up resources."""
        if self.audio:
            self.audio.terminate()