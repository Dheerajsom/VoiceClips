# src/ui/scene_manager_ui.py

import tkinter as tk
import ttkbootstrap as ttkbs
from typing import Optional, Dict, Any
import logging
from PIL import Image, ImageTk
import cv2
from tkinter import filedialog, messagebox, colorchooser
from typing import List, Dict, Any, Optional
import cv2
import mss
from src.features.scene_composition import SceneItem


class SourceDialog(ttkbs.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Source")
        self.result = None
        self.setup_ui()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()

    def setup_ui(self):
        self.geometry("400x300")
        
        # Source name
        name_frame = ttkbs.Frame(self)
        name_frame.pack(fill='x', padx=20, pady=5)
        
        ttkbs.Label(name_frame, text="Source Name:").pack(side='left')
        self.name_entry = ttkbs.Entry(name_frame)
        self.name_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Source type
        type_frame = ttkbs.Frame(self)
        type_frame.pack(fill='x', padx=20, pady=5)
        
        ttkbs.Label(type_frame, text="Source Type:").pack(side='left')
        self.type_var = tk.StringVar(value="Video Capture")
        self.type_combo = ttkbs.Combobox(
            type_frame,
            textvariable=self.type_var,
            values=[
                "Video Capture",
                "Game Capture",
                "Screen Capture",
                "Image",
                "Color Source",
                "Media Source"
            ]
        )
        self.type_combo.pack(side='left', fill='x', expand=True, padx=5)
        
        # Bind type selection
        self.type_combo.bind('<<ComboboxSelected>>', self.on_type_change)

        # Source-specific settings frame
        self.settings_frame = ttkbs.LabelFrame(self, text="Source Settings")
        self.settings_frame.pack(fill='both', expand=True, padx=20, pady=5)
        
        # Initial settings UI
        self.show_settings_ui()

        # Buttons
        btn_frame = ttkbs.Frame(self)
        btn_frame.pack(fill='x', padx=20, pady=10)
        
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

    def on_type_change(self, event=None):
        """Handle source type change."""
        self.show_settings_ui()

    def show_settings_ui(self):
        """Show settings UI for selected source type."""
        # Clear current settings
        for widget in self.settings_frame.winfo_children():
            widget.destroy()

        source_type = self.type_var.get()

        if source_type == "Video Capture":
            self.setup_video_capture_ui()
        elif source_type == "Screen Capture":
            self.setup_screen_capture_ui()
        elif source_type == "Image":
            self.setup_image_ui()
        elif source_type == "Color Source":
            self.setup_color_source_ui()
        elif source_type == "Media Source":
            self.setup_media_source_ui()

    def setup_video_capture_ui(self):
        """Setup UI for video capture source."""
        # Device selection
        device_frame = ttkbs.Frame(self.settings_frame)
        device_frame.pack(fill='x', pady=5)
        
        ttkbs.Label(device_frame, text="Device:").pack(side='left')
        self.device_var = tk.StringVar()
        
        # Get available devices
        devices = self.get_video_devices()
        
        device_combo = ttkbs.Combobox(
            device_frame,
            textvariable=self.device_var,
            values=devices
        )
        device_combo.pack(side='left', fill='x', expand=True, padx=5)
        
        if devices:
            device_combo.set(devices[0])

        # Resolution
        res_frame = ttkbs.Frame(self.settings_frame)
        res_frame.pack(fill='x', pady=5)
        
        ttkbs.Label(res_frame, text="Resolution:").pack(side='left')
        self.resolution_var = tk.StringVar(value="1920x1080")
        resolution_combo = ttkbs.Combobox(
            res_frame,
            textvariable=self.resolution_var,
            values=["1920x1080", "1280x720", "854x480"]
        )
        resolution_combo.pack(side='left', fill='x', expand=True, padx=5)

    def setup_screen_capture_ui(self):
        """Setup UI for screen capture source."""
        # Monitor selection
        monitor_frame = ttkbs.Frame(self.settings_frame)
        monitor_frame.pack(fill='x', pady=5)
        
        ttkbs.Label(monitor_frame, text="Monitor:").pack(side='left')
        self.monitor_var = tk.StringVar(value="Primary Monitor")
        monitor_combo = ttkbs.Combobox(
            monitor_frame,
            textvariable=self.monitor_var,
            values=self.get_monitors()
        )
        monitor_combo.pack(side='left', fill='x', expand=True, padx=5)

        # Capture cursor checkbox
        self.capture_cursor_var = tk.BooleanVar(value=True)
        ttkbs.Checkbutton(
            self.settings_frame,
            text="Capture Cursor",
            variable=self.capture_cursor_var
        ).pack(anchor='w', pady=5)

    def setup_image_ui(self):
        """Setup UI for image source."""
        # Image path
        path_frame = ttkbs.Frame(self.settings_frame)
        path_frame.pack(fill='x', pady=5)
        
        self.image_path_var = tk.StringVar()
        path_entry = ttkbs.Entry(
            path_frame,
            textvariable=self.image_path_var
        )
        path_entry.pack(side='left', fill='x', expand=True)
        
        ttkbs.Button(
            path_frame,
            text="Browse",
            command=self.browse_image
        ).pack(side='left', padx=5)

    def setup_color_source_ui(self):
        """Setup UI for color source."""
        # Color picker
        color_frame = ttkbs.Frame(self.settings_frame)
        color_frame.pack(fill='x', pady=5)
        
        self.color_var = tk.StringVar(value="#000000")
        color_entry = ttkbs.Entry(
            color_frame,
            textvariable=self.color_var
        )
        color_entry.pack(side='left', fill='x', expand=True)
        
        ttkbs.Button(
            color_frame,
            text="Pick Color",
            command=self.pick_color
        ).pack(side='left', padx=5)

    def setup_media_source_ui(self):
        """Setup UI for media source."""
        # Media path
        path_frame = ttkbs.Frame(self.settings_frame)
        path_frame.pack(fill='x', pady=5)
        
        self.media_path_var = tk.StringVar()
        path_entry = ttkbs.Entry(
            path_frame,
            textvariable=self.media_path_var
        )
        path_entry.pack(side='left', fill='x', expand=True)
        
        ttkbs.Button(
            path_frame,
            text="Browse",
            command=self.browse_media
        ).pack(side='left', padx=5)

        # Loop playback
        self.loop_var = tk.BooleanVar(value=True)
        ttkbs.Checkbutton(
            self.settings_frame,
            text="Loop Playback",
            variable=self.loop_var
        ).pack(anchor='w', pady=5)

    def get_video_devices(self) -> List[str]:
        """Get list of available video devices."""
        try:
            import cv2
            devices = []
            for i in range(10):  # Check first 10 indexes
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    devices.append(f"Video Device {i}")
                    cap.release()
            return devices
        except:
            return ["Default Camera"]

    def get_monitors(self) -> List[str]:
        """Get list of available monitors."""
        try:
            import mss
            with mss.mss() as sct:
                return [f"Monitor {i+1}" for i in range(len(sct.monitors))]
        except:
            return ["Primary Monitor"]

    def browse_image(self):
        """Open file browser for image."""
        path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if path:
            self.image_path_var.set(path)

    def browse_media(self):
        """Open file browser for media."""
        path = filedialog.askopenfilename(
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("Audio files", "*.mp3 *.wav *.aac"),
                ("All files", "*.*")
            ]
        )
        if path:
            self.media_path_var.set(path)

    def pick_color(self):
        """Open color picker."""
        color = ttkbs.colorchooser.askcolor(self.color_var.get())[1]
        if color:
            self.color_var.set(color)

    def add_source(self):
        """Add the source."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a source name")
            return

        source_type = self.type_var.get()
        source_data = None

        try:
            if source_type == "Video Capture":
                source_data = {
                    'device': self.device_var.get(),
                    'resolution': self.resolution_var.get()
                }
            elif source_type == "Screen Capture":
                source_data = {
                    'monitor': self.monitor_var.get(),
                    'capture_cursor': self.capture_cursor_var.get()
                }
            elif source_type == "Image":
                source_data = {
                    'path': self.image_path_var.get()
                }
            elif source_type == "Color Source":
                source_data = {
                    'color': self.color_var.get()
                }
            elif source_type == "Media Source":
                source_data = {
                    'path': self.media_path_var.get(),
                    'loop': self.loop_var.get()
                }

            self.result = {
                'name': name,
                'type': source_type,
                'source': source_data
            }
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add source: {str(e)}")

class SceneListWidget(ttkbs.Frame):
    def __init__(self, master, scene_manager):
        super().__init__(master)
        self.scene_manager = scene_manager
        self.selected_scene = None
        self.setup_ui()

    def setup_ui(self):
        # Toolbar
        toolbar = ttkbs.Frame(self)
        toolbar.pack(fill='x', pady=(0, 5))

        # Add scene button
        ttkbs.Button(
            toolbar,
            text="+ Add Scene",
            command=self.add_scene,
            bootstyle="success-outline"
        ).pack(side='left', padx=2)

        # Delete scene button
        ttkbs.Button(
            toolbar,
            text="- Remove Scene",
            command=self.remove_scene,
            bootstyle="danger-outline"
        ).pack(side='left', padx=2)

        # Scene list
        self.scene_list = ttkbs.Treeview(
            self,
            columns=("status",),
            show="tree",
            selectmode="browse"
        )
        self.scene_list.pack(fill='both', expand=True)
        
        # Bind selection
        self.scene_list.bind('<<TreeviewSelect>>', self.on_scene_select)
        
        # Refresh scenes
        self.refresh_scenes()

    def add_scene(self):
        """Add new scene."""
        dialog = SceneDialog(self)
        if dialog.result:
            scene = self.scene_manager.create_scene(dialog.result)
            if scene:
                self.refresh_scenes()
                self.select_scene(scene.name)

    def remove_scene(self):
        """Remove selected scene."""
        if self.selected_scene:
            if self.scene_manager.delete_scene(self.selected_scene):
                self.refresh_scenes()
                self.selected_scene = None

    def refresh_scenes(self):
        """Refresh scene list."""
        self.scene_list.delete(*self.scene_list.get_children())
        
        for name, scene in self.scene_manager.scenes.items():
            status = "✓" if scene.active else ""
            self.scene_list.insert(
                "",
                "end",
                text=name,
                values=(status,)
            )

    def select_scene(self, name: str):
        """Select scene in list."""
        for item in self.scene_list.get_children():
            if self.scene_list.item(item)["text"] == name:
                self.scene_list.selection_set(item)
                self.scene_list.see(item)
                break

    def on_scene_select(self, event):
        """Handle scene selection."""
        selection = self.scene_list.selection()
        if selection:
            name = self.scene_list.item(selection[0])["text"]
            self.selected_scene = name
            self.scene_manager.switch_scene(name)
            self.refresh_scenes()

class ScenePropertiesPanel(ttkbs.LabelFrame):
    def __init__(self, master, scene_manager):
        super().__init__(master, text="Scene Properties")
        self.scene_manager = scene_manager
        self.current_scene = None
        self.setup_ui()

    def setup_ui(self):
        # Properties container
        self.properties_frame = ttkbs.Frame(self)
        self.properties_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Size settings
        size_frame = ttkbs.LabelFrame(self.properties_frame, text="Size")
        size_frame.pack(fill='x', pady=5)

        # Width
        width_frame = ttkbs.Frame(size_frame)
        width_frame.pack(fill='x', pady=2)
        ttkbs.Label(width_frame, text="Width:").pack(side='left')
        self.width_var = tk.StringVar()
        ttkbs.Entry(
            width_frame,
            textvariable=self.width_var,
            width=10
        ).pack(side='left', padx=5)

        # Height
        height_frame = ttkbs.Frame(size_frame)
        height_frame.pack(fill='x', pady=2)
        ttkbs.Label(height_frame, text="Height:").pack(side='left')
        self.height_var = tk.StringVar()
        ttkbs.Entry(
            height_frame,
            textvariable=self.height_var,
            width=10
        ).pack(side='left', padx=5)

        # Background color
        color_frame = ttkbs.LabelFrame(self.properties_frame, text="Background")
        color_frame.pack(fill='x', pady=5)

        self.color_var = tk.StringVar()
        color_entry = ttkbs.Entry(
            color_frame,
            textvariable=self.color_var
        )
        color_entry.pack(side='left', fill='x', expand=True, padx=5)

        ttkbs.Button(
            color_frame,
            text="Pick Color",
            command=self.pick_color
        ).pack(side='right', padx=5)

    def update_scene(self, scene):
        """Update properties for scene."""
        self.current_scene = scene
        if scene:
            self.width_var.set(str(scene.size[0]))
            self.height_var.set(str(scene.size[1]))
            self.color_var.set(self._rgb_to_hex(scene.background_color))
        else:
            self.width_var.set("")
            self.height_var.set("")
            self.color_var.set("#000000")

    def pick_color(self):
        """Open color picker."""
        color = ttkbs.colorchooser.askcolor(self.color_var.get())[1]
        if color:
            self.color_var.set(color)
            if self.current_scene:
                self.current_scene.background_color = self._hex_to_rgb(color)

    def _rgb_to_hex(self, rgb):
        """Convert RGB to hex color."""
        return f"#{rgb[2]:02x}{rgb[1]:02x}{rgb[0]:02x}"

    def _hex_to_rgb(self, hex_color):
        """Convert hex to RGB color."""
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (4, 2, 0))

class SceneItemList(ttkbs.Frame):
    def __init__(self, master, scene_manager):
        super().__init__(master)
        self.scene_manager = scene_manager
        self.selected_item = None
        self.setup_ui()

    def setup_ui(self):
        # Toolbar
        toolbar = ttkbs.Frame(self)
        toolbar.pack(fill='x', pady=(0, 5))

        # Add item button
        ttkbs.Button(
            toolbar,
            text="+ Add Source",
            command=self.add_item,
            bootstyle="success-outline"
        ).pack(side='left', padx=2)

        # Remove item button
        ttkbs.Button(
            toolbar,
            text="- Remove Source",
            command=self.remove_item,
            bootstyle="danger-outline"
        ).pack(side='left', padx=2)

        # Item list
        self.item_list = ttkbs.Treeview(
            self,
            columns=("type", "visible"),
            show="tree"
        )
        self.item_list.pack(fill='both', expand=True)

        # Bind selection
        self.item_list.bind('<<TreeviewSelect>>', self.on_item_select)

    def refresh_items(self, scene):
        """Refresh items for scene."""
        self.item_list.delete(*self.item_list.get_children())
        
        if scene:
            for item in scene.items:
                visible = "👁" if item.visible else ""
                self.item_list.insert(
                    "",
                    "end",
                    text=item.name,
                    values=(item.type, visible)
                )

    def add_item(self):
        """Add new source item."""
        dialog = SourceDialog(self)
        if dialog.result:
            scene = self.scene_manager.get_active_scene()
            if scene:
                item = SceneItem(
                    dialog.result["name"],
                    dialog.result["source"],
                    dialog.result["type"]
                )
                scene.add_item(item)
                self.refresh_items(scene)

    def remove_item(self):
        """Remove selected item."""
        if self.selected_item:
            scene = self.scene_manager.get_active_scene()
            if scene:
                scene.remove_item(self.selected_item)
                self.refresh_items(scene)
                self.selected_item = None

    def on_item_select(self, event):
        """Handle item selection."""
        selection = self.item_list.selection()
        if selection:
            name = self.item_list.item(selection[0])["text"]
            scene = self.scene_manager.get_active_scene()
            if scene:
                self.selected_item = next(
                    (item for item in scene.items if item.name == name),
                    None
                )

class ScenePreview(ttkbs.LabelFrame):
    def __init__(self, master, scene_manager):
        super().__init__(master, text="Preview")
        self.scene_manager = scene_manager
        self.setup_ui()
        self.start_preview()

    def setup_ui(self):
        self.canvas = tk.Canvas(
            self,
            width=640,
            height=360,
            bg='black'
        )
        self.canvas.pack(padx=5, pady=5)

    def start_preview(self):
        """Start preview updates."""
        self.update_preview()

    def update_preview(self):
        """Update preview image."""
        try:
            # Get frame from active scene
            frame = self.scene_manager.render_active_scene()
            if frame is not None:
                # Resize for preview
                frame = cv2.resize(frame, (640, 360))
                
                # Convert to PhotoImage
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                photo = ImageTk.PhotoImage(image)
                
                # Update canvas
                self.canvas.create_image(
                    0, 0,
                    image=photo,
                    anchor='nw'
                )
                self.canvas.image = photo
            
            # Schedule next update
            self.after(33, self.update_preview)  # ~30 FPS
            
        except Exception as e:
            logging.error(f"Error updating preview: {e}")
            self.after(1000, self.update_preview)  # Retry after 1 second

class SceneManagerUI(ttkbs.Frame):
    def __init__(self, master, scene_manager):
        super().__init__(master)
        self.scene_manager = scene_manager
        self.setup_ui()

    def setup_ui(self):
        # Create main layout
        paned = ttkbs.PanedWindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True)

        # Left side (Scene list and properties)
        left_frame = ttkbs.Frame(paned)
        paned.add(left_frame, weight=1)

        # Scene list
        self.scene_list = SceneListWidget(left_frame, self.scene_manager)
        self.scene_list.pack(fill='both', expand=True, pady=(0, 5))

        # Scene properties
        self.properties = ScenePropertiesPanel(left_frame, self.scene_manager)
        self.properties.pack(fill='x')

        # Center (Preview)
        center_frame = ttkbs.Frame(paned)
        paned.add(center_frame, weight=2)

        self.preview = ScenePreview(center_frame, self.scene_manager)
        self.preview.pack(fill='both', expand=True)

        # Right side (Sources list)
        right_frame = ttkbs.Frame(paned)
        paned.add(right_frame, weight=1)

        self.sources = SceneItemList(right_frame, self.scene_manager)
        self.sources.pack(fill='both', expand=True)

class SceneDialog(ttkbs.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Scene")
        self.result = None
        self.setup_ui()

    def setup_ui(self):
        self.geometry("300x150")
        
        # Name entry
        ttkbs.Label(self, text="Scene Name:").pack(pady=5)
        self.name_entry = ttkbs.Entry(self)
        self.name_entry.pack(fill='x', padx=20)

        # Buttons
        btn_frame = ttkbs.Frame(self)
        btn_frame.pack(fill='x', pady=20)
        
        ttkbs.Button(
            btn_frame,
            text="Add",
            command=self.add_scene,
            bootstyle="success"
        ).pack(side='right', padx=5)
        
        ttkbs.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            bootstyle="secondary"
        ).pack(side='right', padx=5)

    def add_scene(self):
        name = self.name_entry.get().strip()
        if name:
            self.result = name
            self.destroy()