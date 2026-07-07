import urllib.request
import zipfile
import os
import subprocess
import time
import requests
import atexit
import logging
import platform
import json
import stat
from pathlib import Path

FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(datefmt=FORMAT,level=logging.WARNING, force=True)
logger = logging.getLogger(__name__)

class LlamaServerService:

    def __init__(self, model_file_name: str, server_port: int = 8080):
        project_root = Path(__file__).resolve().parent.parent.parent
        self.destination_folder = str(project_root / "files" / "server")
        self.model_dir = str(project_root / "files" / "gguf_models")
        
        self.file_gguf = model_file_name
        self.path = os.path.join(self.model_dir, self.file_gguf)

        self.process = None
        self.server_port = server_port

        self.exe_name, self.download_url = self._get_os_config()

        self._init_server()
        atexit.register(self.stop_server)

    def _get_os_config(self) -> tuple[str, str]:
        """Interroga le API di GitHub per ottenere l'eseguibile e l'URL dell'ultima release disponibile."""
        api_url = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
        
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            latest_tag = data.get("tag_name")
            if not latest_tag:
                raise ValueError("Tag della release non trovato nel JSON di GitHub.")
                
        except Exception as e:
            print(f"\n[WARNING] Impossible to contact Github API ({e}). Using version b9895 as fallback.")
            latest_tag = "b9895"

        # 2. Rileviamo l'hardware
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        base_url = f"https://github.com/ggml-org/llama.cpp/releases/download/{latest_tag}"
  
        if system == "windows":
            return "llama-server.exe", f"{base_url}/llama-{latest_tag}-bin-win-vulkan-x64.zip"
        elif system == "darwin":
            if machine in ["arm64", "aarch64"]:
                return "llama-server", f"{base_url}/llama-{latest_tag}-bin-macos-arm64.zip"
            else:
                return "llama-server", f"{base_url}/llama-{latest_tag}-bin-macos-x64.zip"   
        else:
            return "llama-server", f"{base_url}/llama-{latest_tag}-bin-ubuntu-x64.zip"

    def _find_executable(self) -> str | None:
        if os.path.exists(self.destination_folder):
            for root, _, files in os.walk(self.destination_folder):
                if self.exe_name in files:
                    return os.path.join(root, self.exe_name)
        return None
    
    def _make_executable(self, path: str) -> None:
        """Add execution permission (chmod +x), a must for Mac/Linux."""
        if platform.system().lower() != "windows":
            st = os.stat(path)
            os.chmod(path, st.st_mode | stat.S_IEXEC)
    
    def _init_server(self) -> None:
        self.exe_path = self._find_executable()
        
        if self.exe_path:
            self._make_executable(self.exe_path)
            return None
            
        logger.info("Downloading AI engine...")
        os.makedirs(self.destination_folder, exist_ok=True)

        zip_exe_path = os.path.join(self.destination_folder, "llama_exe.zip")
        urllib.request.urlretrieve(self.download_url, zip_exe_path)

        logger.info("Extracting Llama engine...")
        with zipfile.ZipFile(zip_exe_path, 'r') as zip_ref:
            zip_ref.extractall(self.destination_folder)

        os.remove(zip_exe_path)
        logger.info("Llama engine downloaded!")

        self.exe_path = self._find_executable()
        if not self.exe_path:
            raise FileNotFoundError(f"Critical error: {self.exe_name} not found even after extraction.")

        self._make_executable(self.exe_path)
        
        logger.info("Llama server ready to run!")

    def start_server(self):
        print("Starting Llama server...")

        command = [
            self.exe_path,
            "--model", self.path,
            "-ngl", "99",
            "--port", f"{self.server_port}",
            "--flash-attn", "auto",
            "-c", "4096"
        ]

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print("Waiting for server...")
        server_ready = False
        for _ in range(30):
            try:
                logger.info(f"Try number {_ + 1}")
                res = requests.get(f"http://localhost:{self.server_port}/health")
                if res.status_code == 200:
                    server_ready = True
                    break
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        
        if not server_ready:
            logger.error("Server didn't start in time")
            raise RuntimeError("Server didn't start in time")

        logger.info("Server ready")

    def stop_server(self):
        if self.process:
            logger.info("\nClosing LLM server...")
            self.process.terminate()
            self.process.wait()
            self.process = None
            logger.info("Server closed.")