import urllib.request
import zipfile
import os
import subprocess
import time
import requests
import atexit
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(filename="llama_server.log", level=logging.INFO, force=True)


class LlamaServerService:

    def __init__(self, model_file_name: str, model_dir: str = "./files/gguf_models", server_dir: str = "./files/server/", server_port: int = 8080):
        self.destination_folder = os.path.abspath(server_dir)
        self.exe_path = None

        self.model_dir = os.path.abspath(model_dir)
        self.file_gguf = model_file_name
        self.path = f"{self.model_dir}/{self.file_gguf}"

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
            
        logger.info("Downloading AI engine (llama.cpp)...")
        os.makedirs(self.destination_folder, exist_ok=True)

        url_zip = "https://github.com/ggml-org/llama.cpp/releases/download/b9538/llama-b9538-bin-win-cuda-12.4-x64.zip"
        zip_path = os.path.join(self.destination_folder, "llama.zip")
        
        urllib.request.urlretrieve(url_zip, zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.destination_folder)

        os.remove(zip_path)
        logger.info("llama server downloaded!")

        self.exe_path = self._find_executable()

        if not self.exe_path:
            raise FileNotFoundError("Critical error: llama-server.exe not found even after extraction.")
            
        logger.info("llama server extracted!")

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
            logger.error("Server didn't work in time")
            raise RuntimeError("Server didn't start in time")

        logger.info("Server ready")

    def stop_server(self):
        if self.process:
            logger.info("\nClosing LLM server...")
            self.process.terminate()
            self.process.wait()
            self.process = None
            logger.info("Server closed.")
