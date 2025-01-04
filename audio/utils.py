import os
import wave

def save_audio_to_file(audio_data, file_path='output.wav', audio_settings=None):
    """Save raw audio data to a WAV file using specified audio settings."""
    if audio_settings is None:
        audio_settings = {
            'channels': 1,
            'sampwidth': 2,  # Sample width in bytes
            'framerate': 44100,
        }
    
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(audio_settings['channels'])
        wf.setsampwidth(audio_settings['sampwidth'])
        wf.setframerate(audio_settings['framerate'])
        wf.writeframes(audio_data)
        print(f"Audio saved to {file_path}")

def ensure_directory_exists(directory_path):
    """Ensure that a directory exists, and if not, create it."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory created: {directory_path}")

def log(message, log_file='application.log'):
    """Simple logging function to write messages to a log file."""
    with open(log_file, 'a') as f:
        f.write(f"{message}\n")

# Example usage
if __name__ == "__main__":
    # Assuming `audio_data` is obtained from somewhere else in the application
    audio_data = b"fake_audio_data_for_demo_purposes"  # This would be actual audio data
    save_audio_to_file(audio_data)
    ensure_directory_exists('logs')
    log("Application started.")