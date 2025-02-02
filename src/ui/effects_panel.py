# src/ui/effects_panel.py
import tkinter as tk
import ttkbootstrap as ttkbs
from typing import Dict, Any

class EffectsPanel(ttkbs.LabelFrame):
    """Panel for managing video effects."""
    
    def __init__(self, master, effects_manager, **kwargs):
        super().__init__(master, text="Effects", **kwargs)
        self.effects_manager = effects_manager
        self.effects: Dict[str, Dict] = {}
        self.setup_ui()

    def setup_ui(self):
        """Create effects panel UI."""
        # Main container
        self.effects_frame = ttkbs.Frame(self)
        self.effects_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Add effects button
        add_btn = ttkbs.Button(
            self,
            text="+ Add Effect",
            command=self.add_effect,
            bootstyle="secondary-outline"
        )
        add_btn.pack(fill='x', padx=5, pady=5)

        # Add default effects
        self.add_effect_item("Color Correction")
        self.add_effect_item("Chroma Key")

    def add_effect_item(self, name: str):
        """Add effect item to panel."""
        if name in self.effects:
            return

        # Effect frame
        effect = ttkbs.Frame(self.effects_frame)
        effect.pack(fill='x', pady=2)

        # Enable checkbox
        enabled_var = tk.BooleanVar(value=True)
        enabled = ttkbs.Checkbutton(
            effect,
            text=name,
            variable=enabled_var,
            command=lambda: self.toggle_effect(name),
            bootstyle="round-toggle"
        )
        enabled.pack(side='left', padx=5)

        # Settings button
        settings_btn = ttkbs.Button(
            effect,
            text="⚙",
            command=lambda: self.open_effect_settings(name),
            width=3
        )
        settings_btn.pack(side='right', padx=5)

        # Store effect controls
        self.effects[name] = {
            'frame': effect,
            'enabled': enabled_var,
            'settings': settings_btn
        }

    def add_effect(self):
        """Add new effect dialog."""
        dialog = EffectDialog(self)
        if dialog.result:
            self.add_effect_item(dialog.result)

    def toggle_effect(self, effect: str):
        """Toggle effect enabled state."""
        if effect in self.effects:
            enabled = self.effects[effect]['enabled'].get()
            if effect in self.effects_manager.effects:
                self.effects_manager.effects[effect].enabled = enabled

    def open_effect_settings(self, effect: str):
        """Open effect settings dialog."""
        if effect == "Color Correction":
            ColorCorrectionDialog(self, self.effects_manager)
        elif effect == "Chroma Key":
            ChromaKeyDialog(self, self.effects_manager)

class EffectDialog(ttkbs.Toplevel):
    """Dialog for adding new effect."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Effect")
        self.result = None
        self.setup_ui()

    def setup_ui(self):
        """Create dialog UI."""
        self.geometry("300x200")
        
        # Effect list
        ttkbs.Label(self, text="Select Effect:").pack(pady=5)
        self.effect_list = tk.Listbox(self, height=6)
        self.effect_list.pack(fill='both', padx=20, pady=5)

        # Add available effects
        effects = [
            "Color Correction",
            "Chroma Key",
            "Blur",
            "Sharpen",
            "Color Key",
            "Image Mask"
        ]
        for effect in effects:
            self.effect_list.insert(tk.END, effect)

        # Buttons
        btn_frame = ttkbs.Frame(self)
        btn_frame.pack(fill='x', pady=20)
        
        ttkbs.Button(
            btn_frame,
            text="Add",
            command=self.add_effect,
            bootstyle="success"
        ).pack(side='right', padx=5)
        
        ttkbs.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            bootstyle="secondary"
        ).pack(side='right', padx=5)

    def add_effect(self):
        """Add selected effect."""
        selection = self.effect_list.curselection()
        if selection:
            self.result = self.effect_list.get(selection[0])
            self.destroy()

class ColorCorrectionDialog(ttkbs.Toplevel):
    """Dialog for color correction settings."""
    
    def __init__(self, parent, effects_manager):
        super().__init__(parent)
        self.title("Color Correction")
        self.effects_manager = effects_manager
        self.setup_ui()

    def setup_ui(self):
        """Create settings UI."""
        self.geometry("400x300")
        
        # Brightness
        self.add_slider("Brightness", -100, 100, 0)
        
        # Contrast
        self.add_slider("Contrast", -100, 100, 0)
        
        # Saturation
        self.add_slider("Saturation", -100, 100, 0)
        
        # Temperature
        self.add_slider("Temperature", -100, 100, 0)
        
        # Apply button
        ttkbs.Button(
            self,
            text="Apply",
            command=self.apply_settings,
            bootstyle="success"
        ).pack(side='bottom', pady=20)

    def add_slider(self, name: str, min_val: int, max_val: int, default: int):
        """Add slider control."""
        frame = ttkbs.Frame(self)
        frame.pack(fill='x', padx=20, pady=5)
        
        ttkbs.Label(frame, text=f"{name}:").pack(side='left')
        slider = ttkbs.Scale(
            frame,
            from_=min_val,
            to=max_val,
            orient='horizontal'
        )
        slider.set(default)
        slider.pack(side='left', fill='x', expand=True, padx=10)

    def apply_settings(self):
        """Apply color correction settings."""
        # Implement settings application
        self.destroy()

class ChromaKeyDialog(ttkbs.Toplevel):
    """Dialog for chroma key settings."""
    
    def __init__(self, parent, effects_manager):
        super().__init__(parent)
        self.title("Chroma Key")
        self.effects_manager = effects_manager
        self.setup_ui()

    def setup_ui(self):
        """Create settings UI."""
        self.geometry("400x300")
        
        # Color selection
        color_frame = ttkbs.Frame(self)
        color_frame.pack(fill='x', padx=20, pady=10)
        ttkbs.Label(color_frame, text="Key Color:").pack(side='left')
        self.color_btn = ttkbs.Button(
            color_frame,
            text="Select Color",
            command=self.select_color
        )
        self.color_btn.pack(side='left', padx=10)
        
        # Similarity
        self.add_slider("Similarity", 1, 1000, 500)
        
        # Smoothness
        self.add_slider("Smoothness", 1, 100, 50)
        
        # Spill Reduction
        self.add_slider("Spill Reduction", 1, 100, 50)
        
        # Apply button
        ttkbs.Button(
            self,
            text="Apply",
            command=self.apply_settings,
            bootstyle="success"
        ).pack(side='bottom', pady=20)

    def add_slider(self, name: str, min_val: int, max_val: int, default: int):
        """Add slider control."""
        frame = ttkbs.Frame(self)
        frame.pack(fill='x', padx=20, pady=5)
        
        ttkbs.Label(frame, text=f"{name}:").pack(side='left')
        slider = ttkbs.Scale(
            frame,
            from_=min_val,
            to=max_val,
            orient='horizontal'
        )
        slider.set(default)
        slider.pack(side='left', fill='x', expand=True, padx=10)

    def select_color(self):
        """Open color picker."""
        # Implement color picker
        pass

    def apply_settings(self):
        """Apply chroma key settings."""
        # Implement settings application
        self.destroy()