# src/ui/audio_mixer_widget.py
import tkinter as tk
import ttkbootstrap as ttkbs
from typing import Dict

class AudioMixerWidget(ttkbs.LabelFrame):
    """Audio mixer widget for controlling audio sources."""
    
    def __init__(self, master, audio_mixer, **kwargs):
        super().__init__(master, text="Audio Mixer", **kwargs)
        self.audio_mixer = audio_mixer
        self.channels: Dict[str, Dict] = {}
        self.setup_ui()

    def setup_ui(self):
        """Create audio mixer UI."""
        # Main container
        self.mixer_frame = ttkbs.Frame(self)
        self.mixer_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Add default channels
        self.add_channel("Desktop Audio")
        self.add_channel("Microphone")

        # Add button for new sources
        add_btn = ttkbs.Button(
            self,
            text="+ Add Audio Source",
            command=self.add_audio_source,
            bootstyle="secondary-outline"
        )
        add_btn.pack(fill='x', padx=5, pady=5)

    def add_channel(self, name: str):
        """Add new audio channel."""
        if name in self.channels:
            return

        # Channel frame
        channel = ttkbs.Frame(self.mixer_frame)
        channel.pack(fill='x', pady=2)

        # Channel label
        label = ttkbs.Label(channel, text=name)
        label.pack(side='left', padx=5)

        # Volume slider
        volume = ttkbs.Scale(
            channel,
            from_=0,
            to=100,
            orient='horizontal',
            command=lambda v: self.update_volume(name, v)
        )
        volume.set(75)  # Default volume
        volume.pack(side='left', fill='x', expand=True, padx=5)

        # Mute button
        mute_var = tk.BooleanVar(value=False)
        mute_btn = ttkbs.Checkbutton(
            channel,
            text="🔇",
            variable=mute_var,
            command=lambda: self.toggle_mute(name),
            bootstyle="danger-round-toggle"
        )
        mute_btn.pack(side='left', padx=5)

        # Settings button
        settings_btn = ttkbs.Button(
            channel,
            text="⚙",
            command=lambda: self.open_channel_settings(name),
            width=3
        )
        settings_btn.pack(side='left', padx=5)

        # Store channel controls
        self.channels[name] = {
            'frame': channel,
            'volume': volume,
            'mute': mute_var,
            'settings': settings_btn
        }

    def add_audio_source(self):
        """Add new audio source dialog."""
        dialog = AudioSourceDialog(self)
        if dialog.result:
            self.add_channel(dialog.result)

    def update_volume(self, channel: str, volume: float):
        """Update channel volume."""
        if channel in self.channels:
            try:
                volume = float(volume)
                self.audio_mixer.set_source_volume(channel, volume / 100.0)
            except ValueError:
                pass

    def toggle_mute(self, channel: str):
        """Toggle channel mute state."""
        if channel in self.channels:
            muted = self.channels[channel]['mute'].get()
            self.audio_mixer.toggle_source_mute(channel)
            # Update volume slider state
            self.channels[channel]['volume'].configure(
                state='disabled' if muted else 'normal'
            )

    def open_channel_settings(self, channel: str):
        """Open channel settings dialog."""
        AudioChannelSettings(self, channel, self.audio_mixer)

    def update_levels(self, levels: Dict[str, float]):
        """Update audio level indicators."""
        for channel, level in levels.items():
            if channel in self.channels:
                # Update level indicator (if implemented)
                pass

class AudioSourceDialog(ttkbs.Toplevel):
    """Dialog for adding new audio source."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Audio Source")
        self.result = None
        self.setup_ui()

    def setup_ui(self):
        """Create dialog UI."""
        self.geometry("300x150")
        
        # Name entry
        ttkbs.Label(self, text="Source Name:").pack(pady=5)
        self.name_entry = ttkbs.Entry(self)
        self.name_entry.pack(fill='x', padx=20)

        # Device selection
        ttkbs.Label(self, text="Audio Device:").pack(pady=5)
        self.device_combo = ttkbs.Combobox(
            self,
            values=self.get_available_devices()
        )
        self.device_combo.pack(fill='x', padx=20)

        # Buttons
        btn_frame = ttkbs.Frame(self)
        btn_frame.pack(fill='x', pady=20)
        
        ttkbs.Button(
            btn_frame,
            text="Add",
            command=self.add_source,
            bootstyle="success"
        ).pack(side='right', padx=5)
        
        ttkbs.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            bootstyle="secondary"
        ).pack(side='right', padx=5)

    def get_available_devices(self):
        """Get list of available audio devices."""
        # Implement audio device detection
        return ["Default", "System Audio", "Microphone"]

    def add_source(self):
        """Add new audio source."""
        name = self.name_entry.get().strip()
        if name:
            self.result = name
            self.destroy()

class AudioChannelSettings(ttkbs.Toplevel):
    """Settings dialog for audio channel."""
    
    def __init__(self, parent, channel: str, audio_mixer):
        super().__init__(parent)
        self.channel = channel
        self.audio_mixer = audio_mixer
        self.title(f"{channel} Settings")
        self.setup_ui()

    def setup_ui(self):
        """Create settings UI."""
        self.geometry("400x300")
        
        # Device selection
        ttkbs.Label(self, text="Audio Device:").pack(pady=5)
        self.device_combo = ttkbs.Combobox(
            self,
            values=self.get_available_devices()
        )
        self.device_combo.pack(fill='x', padx=20)

        # Audio filters
        filters_frame = ttkbs.LabelFrame(self, text="Audio Filters")
        filters_frame.pack(fill='x', padx=20, pady=10)
        
        # Noise Suppression
        ttkbs.Checkbutton(
            filters_frame,
            text="Noise Suppression",
            bootstyle="round-toggle"
        ).pack(anchor='w', padx=10, pady=5)
        
        # Gain
        gain_frame = ttkbs.Frame(filters_frame)
        gain_frame.pack(fill='x', padx=10, pady=5)
        ttkbs.Label(gain_frame, text="Gain:").pack(side='left')
        ttkbs.Scale(
            gain_frame,
            from_=-20,
            to=20,
            orient='horizontal'
        ).pack(side='left', fill='x', expand=True)

        # Monitoring
        monitor_frame = ttkbs.LabelFrame(self, text="Monitoring")
        monitor_frame.pack(fill='x', padx=20, pady=10)
        ttkbs.Radiobutton(
            monitor_frame,
            text="Off",
            value="off"
        ).pack(side='left', padx=10)
        ttkbs.Radiobutton(
            monitor_frame,
            text="Monitor Only",
            value="monitor"
        ).pack(side='left', padx=10)
        ttkbs.Radiobutton(
            monitor_frame,
            text="Monitor and Output",
            value="both"
        ).pack(side='left', padx=10)

        # Apply button
        ttkbs.Button(
            self,
            text="Apply",
            command=self.apply_settings,
            bootstyle="success"
        ).pack(side='bottom', pady=20)

    def get_available_devices(self):
        """Get list of available audio devices."""
        # Implement audio device detection
        return ["Default", "System Audio", "Microphone"]

    def apply_settings(self):
        """Apply channel settings."""
        # Implement settings application
        self.destroy()