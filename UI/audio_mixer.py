import os
import platform
import subprocess

def set_mic_volume(level):
    """Set the microphone volume level."""
    if platform.system() == "Windows":
        # Use Windows specific commands (requires third-party libraries like pycaw)
        try:
            import comtypes.client
            from ctypes import cast, POINTER
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetMicrophone()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None
            )
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100, None)
        except Exception as e:
            print(f"Error setting microphone volume on Windows: {e}")

    elif platform.system() == "Darwin":
        # macOS - Use osascript
        try:
            subprocess.call(["osascript", "-e", f"set volume input volume {int(level)}"])
        except Exception as e:
            print(f"Error setting microphone volume on macOS: {e}")

    elif platform.system() == "Linux":
        # Linux - Use amixer (ALSA)
        try:
            subprocess.call(["amixer", "set", "Capture", f"{level}%"])
        except Exception as e:
            print(f"Error setting microphone volume on Linux: {e}")


def set_system_volume(level):
    """Set the system volume level."""
    if platform.system() == "Windows":
        # Use Windows specific commands (requires third-party libraries like pycaw)
        try:
            import comtypes.client
            from ctypes import cast, POINTER
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None
            )
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100, None)
        except Exception as e:
            print(f"Error setting system volume on Windows: {e}")

    elif platform.system() == "Darwin":
        # macOS - Use osascript
        try:
            subprocess.call(["osascript", "-e", f"set volume output volume {int(level)}"])
        except Exception as e:
            print(f"Error setting system volume on macOS: {e}")

    elif platform.system() == "Linux":
        # Linux - Use amixer (ALSA)
        try:
            subprocess.call(["amixer", "set", "Master", f"{level}%"])
        except Exception as e:
            print(f"Error setting system volume on Linux: {e}")


if __name__ == "__main__":
    set_mic_volume(50)  # Example usage
    set_system_volume(70)
