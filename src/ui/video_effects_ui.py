# src/ui/video_effects_ui.py

import tkinter as tk
import ttkbootstrap as ttkbs
from typing import Dict, Any, Optional, Callable
from tkinter import colorchooser
import logging
from pathlib import Path

class VideoEffectsPanel(ttkbs.LabelFrame):
    """Video effects control panel."""
    
    def __init__(self, master, effects_manager, **kwargs):
        super().__init__(master, text="Video Effects", **kwargs)
        self.effects_manager = effects_manager
        self.effect_frames: Dict[str, Dict[str, Any]] = {}
        self.setup_ui()

    def setup_ui(self):
        """Create effects panel UI."""
        # Main container with scrollbar
        container = ttkbs.Frame(self)
        container.pack(fill='both', expand=True, padx=5, pady=5)

        # Canvas and scrollbar
        canvas = tk.Canvas(container)
        scrollbar = ttkbs.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttkbs.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack elements
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add effects button
        add_btn = ttkbs.Button(
            self,
            text="+ Add Effect",
            command=self.show_add_effect_dialog,
            bootstyle="success-outline"
        )
        add_btn.pack(fill='x', padx=5, pady=5)

        # Add default effects
        self.add_color_correction()
        self.add_chroma_key()

    def add_color_correction(self):
        """Add color correction controls."""
        frame = self.create_effect_frame("Color Correction")
        
        # Brightness
        self.add_slider(frame, "Brightness", -100, 100, 0,
                       lambda v: self.update_effect("color_correction", "brightness", v))
        
        # Contrast
        self.add_slider(frame, "Contrast", -100, 100, 0,
                       lambda v: self.update_effect("color_correction", "contrast", v))
        
        # Saturation
        self.add_slider(frame, "Saturation", -100, 100, 0,
                       lambda v: self.update_effect("color_correction", "saturation", v))
        
        # Temperature
        self.add_slider(frame, "Temperature", -100, 100, 0,
                       lambda v: self.update_effect("color_correction", "temperature", v))

    def add_chroma_key(self):
        """Add chroma key controls."""
        frame = self.create_effect_frame("Chroma Key")
        
        # Color picker
        color_frame = ttkbs.Frame(frame)
        color_frame.pack(fill='x', pady=2)
        
        ttkbs.Label(color_frame, text="Key Color:").pack(side='left')
        
        self.color_btn = ttkbs.Button(
            color_frame,
            text="Pick Color",
            command=lambda: self.pick_color("chroma_key"),
            width=10
        )
        self.color_btn.pack(side='left', padx=5)
        
        # Similarity
        self.add_slider(frame, "Similarity", 1, 100, 40,
                       lambda v: self.update_effect("chroma_key", "similarity", v))
        
        # Smoothness
        self.add_slider(frame, "Smoothness", 1, 100, 30,
                       lambda v: self.update_effect("chroma_key", "smoothness", v))
        
        # Spill reduction
        self.add_slider(frame, "Spill Reduction", 0, 100, 50,
                       lambda v: self.update_effect("chroma_key", "spill", v))

    def create_effect_frame(self, name: str) -> ttkbs.LabelFrame:
        """Create frame for effect controls."""
        frame = ttkbs.LabelFrame(self.scrollable_frame, text=name)
        frame.pack(fill='x', pady=5)
        
        # Header with enable/disable toggle
        header = ttkbs.Frame(frame)
        header.pack(fill='x', padx=5, pady=2)
        
        enabled_var = tk.BooleanVar(value=True)
        toggle = ttkbs.Checkbutton(
            header,
            text="Enable",
            variable=enabled_var,
            command=lambda: self.toggle_effect(name, enabled_var.get()),
            bootstyle="round-toggle"
        )
        toggle.pack(side='left')
        
        # Remove button
        remove_btn = ttkbs.Button(
            header,
            text="×",
            command=lambda: self.remove_effect(name),
            width=3
        )
        remove_btn.pack(side='right')
        
        # Store frame references
        self.effect_frames[name] = {
            'frame': frame,
            'enabled': enabled_var
        }
        
        return frame

    def add_slider(self, parent: ttkbs.Frame, name: str, min_val: int, 
                  max_val: int, default: int, callback: Callable):
        """Add slider control."""
        frame = ttkbs.Frame(parent)
        frame.pack(fill='x', pady=2)
        
        ttkbs.Label(frame, text=f"{name}:").pack(side='left')
        
        value_var = tk.StringVar(value=str(default))
        value_label = ttkbs.Label(frame, textvariable=value_var, width=5)
        value_label.pack(side='right')
        
        slider = ttkbs.Scale(
            frame,
            from_=min_val,
            to=max_val,
            orient='horizontal',
            command=lambda v: self.update_slider(value_var, callback, v)
        )
        slider.set(default)
        slider.pack(side='left', fill='x', expand=True, padx=5)

    def update_slider(self, value_var: tk.StringVar, callback: Callable, value: str):
        """Update slider value and trigger callback."""
        try:
            value = float(value)
            value_var.set(f"{value:.0f}")
            callback(value)
        except ValueError:
            pass

    def pick_color(self, effect: str):
        """Open color picker dialog."""
        color = colorchooser.askcolor(title="Choose Key Color")
        if color[1]:  # color is ((R, G, B), hex_value)
            self.update_effect(effect, "key_color", color[0])
            self.color_btn.configure(bg=color[1])

    def show_add_effect_dialog(self):
        """Show dialog to add new effect."""
        dialog = AddEffectDialog(self)
        if dialog.result:
            self.add_effect(dialog.result)

    def add_effect(self, effect_type: str):
        """Add new effect to panel."""
        if effect_type == "Color Correction":
            self.add_color_correction()
        elif effect_type == "Chroma Key":
            self.add_chroma_key()
        # Add more effect types here

    def remove_effect(self, name: str):
        """Remove effect from panel."""
        if name in self.effect_frames:
            self.effect_frames[name]['frame'].destroy()
            del self.effect_frames[name]
            self.effects_manager.remove_effect(name)

    def toggle_effect(self, name: str, enabled: bool):
        """Toggle effect enabled state."""
        effect = self.effects_manager.get_effect(name)
        if effect:
            effect.enabled = enabled

    def update_effect(self, effect: str, parameter: str, value: Any):
        """Update effect parameter."""
        effect_obj = self.effects_manager.get_effect(effect)
        if effect_obj:
            effect_obj.set_parameter(parameter, value)

class AddEffectDialog(ttkbs.Toplevel):
    """Dialog for adding new effects."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Effect")
        self.result = None
        self.setup_ui()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()

    def setup_ui(self):
        """Create dialog UI."""
        self.geometry("300x400")
        
        # Effect categories
        categories = {
            "Color": ["Color Correction", "Color Balance", "LUT"],
            "Keys": ["Chroma Key", "Luma Key", "Alpha Key"],
            "Filters": ["Blur", "Sharpen", "Noise Reduction"],
            "Stylize": ["Vignette", "Film Grain", "Color Grading"]
        }
        
        # Create notebook for categories
        notebook = ttkbs.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add tabs for each category
        self.effect_vars = {}
        for category, effects in categories.items():
            frame = ttkbs.Frame(notebook)
            notebook.add(frame, text=category)
            
            for effect in effects:
                var = tk.BooleanVar()
                self.effect_vars[effect] = var
                
                ttkbs.Checkbutton(
                    frame,
                    text=effect,
                    variable=var,
                    bootstyle="round-toggle"
                ).pack(anchor='w', padx=10, pady=5)
        
        # Buttons
        btn_frame = ttkbs.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        ttkbs.Button(
            btn_frame,
            text="Add",
            command=self.add_effects,
            bootstyle="success"
        ).pack(side='right', padx=5)
        
        ttkbs.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            bootstyle="secondary"
        ).pack(side='right', padx=5)

    def add_effects(self):
        """Add selected effects."""
        selected = [effect for effect, var in self.effect_vars.items() 
                   if var.get()]
        if selected:
            self.result = selected[0]  # For now, just return first selected effect
        self.destroy()