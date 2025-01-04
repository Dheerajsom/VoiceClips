import pytest
import tkinter as tk
from UI.app import run_app

def test_gui_load():
    try:
        run_app()
        assert True
    except:
        assert False
