import sys
import os
import platform
from pathlib import Path

def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    If running as a PyInstaller executable, returns the temporary _MEIPASS folder.
    Otherwise, returns the project root.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).resolve().parent.parent.parent

def get_app_data_dir() -> Path:
    """
    Returns a persistent directory to store downloaded models, servers, etc.
    On Windows: %APPDATA%/WaveRedact
    On Mac/Linux: ~/.waveredact
    """
    app_name = "WaveRedact"
    system = platform.system()
    
    if system == "Windows":
        base_dir = os.environ.get("APPDATA")
        if not base_dir:
            base_dir = Path.home() / "AppData" / "Roaming"
        app_dir = Path(base_dir) / app_name
    elif system == "Darwin":
        app_dir = Path.home() / "Library" / "Application Support" / app_name
    else:
        app_dir = Path.home() / ".waveredact"
        
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir
