import urllib.request
import zipfile
import os
import subprocess
import time
import requests
import atexit
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(datefmt=FORMAT,level=logging.WARNING, force=True)


class LlamaServerService:

    def __init__(self, model_file_name: str, server_port: int = 8080):
        project_root = Path(__file__).resolve().parent.parent.parent
        self.destination_folder = str(project_root / "files" / "server")
        self.model_dir = str(project_root / "files" / "gguf_models")
        
        self.file_gguf = model_file_name
        self.path = os.path.join(self.model_dir, self.file_gguf)

        self.process = None
        self.server_port = server_port

        self._init_server()
        atexit.register(self.stop_server)

    def _find_executable(self) -> str | None:
        if os.path.exists(self.destination_folder):
            for root, _, files in os.walk(self.destination_folder):
                if "llama-server.exe" in files:
                    return os.path.join(root, "llama-server.exe")
        return None
    
    def _init_server(self) -> None:
        self.exe_path = self._find_executable()
        if self.exe_path:
            return None
            
        logger.info("Downloading AI engine...")
        os.makedirs(self.destination_folder, exist_ok=True)

        url_exe = "https://github.com/ggml-org/llama.cpp/releases/download/b9538/llama-b9538-bin-win-cuda-12.4-x64.zip"
        zip_exe_path = os.path.join(self.destination_folder, "llama_exe.zip")
        urllib.request.urlretrieve(url_exe, zip_exe_path)

        logger.info("Extracting Llama engine...")
        with zipfile.ZipFile(zip_exe_path, 'r') as zip_ref:
            zip_ref.extractall(self.destination_folder)

        os.remove(zip_exe_path)
        logger.info("Llama engine downloaded!")

        self.exe_path = self._find_executable()
        if not self.exe_path:
            raise FileNotFoundError("Critical error: llama-server.exe not found even after extraction.")
            
        logger.info("Llama server ready to run!")

    def start_server(self):
        logger.info("Starting Llama server...")

        command = [
            self.exe_path,
            "--model", self.path,
            "-ngl", "99",
            "--port", f"{self.server_port}"
        ]

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        logger.info("Waiting for server...")
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
