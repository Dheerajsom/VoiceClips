import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

import ttkbootstrap as ttkbs
from src.app import StreamStudio

if __name__ == "__main__":
    root = ttkbs.Window(themename="darkly")
    app = StreamStudio()
    root.mainloop()
