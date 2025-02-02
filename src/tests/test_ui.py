# tests/test_ui.py
import tkinter as tk
import pytest
from src.ui.main_window import MainWindow

@pytest.fixture
def root():
    """Provide tkinter root window."""
    root = tk.Tk()
    yield root
    root.destroy()

class TestUI:
    def test_window_creation(self, root, config, clipper):
        """Test main window creation."""
        window = MainWindow(root, clipper, config)
        assert window is not None
        assert window.preview is not None
        assert window.recording_manager is not None

    def test_recording_controls(self, root, config, clipper):
        """Test recording control buttons."""
        window = MainWindow(root, clipper, config)
        assert window.record_button['state'] == 'normal'
        assert window.stop_button['state'] == 'disabled'
        
        window.toggle_recording()
        assert window.record_button['state'] == 'disabled'
        assert window.stop_button['state'] == 'normal'
        
        window.toggle_recording()
        assert window.record_button['state'] == 'normal'
        assert window.stop_button['state'] == 'disabled'