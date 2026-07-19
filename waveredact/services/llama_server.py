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
import math
import stat
import tarfile
import multiprocessing
from waveredact.utils.path_utils import get_app_data_dir

FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(datefmt=FORMAT,level=logging.WARNING, force=True)
logger = logging.getLogger(__name__)

class LlamaServerService:
    """
    Manage the downloading and execution of the Llama model server.

    Attributes:
        destination_folder  - Path where the server executable is saved
        model_dir           - Path where the model is saved
        file_gguf           - Model filename
        path                - Full path to the model file
        process             - Subprocess instance of the server
        server_port         - Port for the server
        device              - Device to run the server on (e.g. cpu, cuda)
        exe_name            - Name of the server executable
        download_url        - URL to download the server executable
        exe_path            - Full path to the server executable
    """

    def __init__(self, model_file_name: str, server_port: int = 8080, device: str = "cpu"):
        self.destination_folder = str(get_app_data_dir() / "files" / "server")
        self.model_dir = str(get_app_data_dir() / "files" / "gguf_models")
        
        self.file_gguf = model_file_name
        self.path = os.path.join(self.model_dir, self.file_gguf)

        self.process = None
        self.server_port = server_port 
        self.device = device

        self.exe_name, self.download_url = self._get_os_config()

        self._init_server()
        atexit.register(self.stop_server)

    def _get_os_config(self) -> tuple[str, str]:
        """Use Github API to obtain the exe file and the URL for the last available release"""
        api_url = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
        
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            latest_tag = data.get("tag_name")
            if not latest_tag:
                raise ValueError("Release tag not found")
                
        except Exception as e:
            print(f"\n[WARNING] Impossible to contact Github API ({e}). Using version b9895 as fallback.")
            latest_tag = "b9895"

        system = platform.system().lower()
        machine = platform.machine().lower()
        
        base_url = f"https://github.com/ggml-org/llama.cpp/releases/download/{latest_tag}"
  
        if system == "windows":
            if self.device == "cuda":
                return "llama-server.exe", f"{base_url}/llama-{latest_tag}-bin-win-cuda-12.4-x64.zip"
            else:
                return "llama-server.exe", f"{base_url}/llama-{latest_tag}-bin-win-vulkan-x64.zip"
        elif system == "darwin":
            if machine in ["arm64", "aarch64"]:
                return "llama-server", f"{base_url}/llama-{latest_tag}-bin-macos-arm64.tar.gz"
            else:
                return "llama-server", f"{base_url}/llama-{latest_tag}-bin-macos-x64.tar.gz"   
        else:
            return "llama-server", f"{base_url}/llama-{latest_tag}-bin-ubuntu-x64.tar.gz"

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

        is_zip = self.download_url.endswith('.zip')
        archive_name = "llama_exe.zip" if is_zip else "llama_exe.tar.gz"
        archive_path = os.path.join(self.destination_folder, archive_name)
        
        urllib.request.urlretrieve(self.download_url, archive_path)

        logger.info("Extracting Llama engine...")
        if is_zip:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(self.destination_folder)
        else:
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(self.destination_folder)

        os.remove(archive_path)
        logger.info("Llama engine downloaded!")

        self.exe_path = self._find_executable()
        if not self.exe_path:
            raise FileNotFoundError(f"Critical error: {self.exe_name} not found even after extraction.")

        self._make_executable(self.exe_path)
        
        logger.info("Llama server ready to run!")

    def start_server(self):
        """
        Start the Llama model server in a separate process.
        """
        print("Starting Llama server...")

        ngl = self._get_optimal_ngl()

        threads = "4"
        
        if platform.system().lower() == "darwin" and platform.machine().lower() in ["arm64", "aarch64"]:
            threads = "4" 
        else:
            threads = str(max(1, multiprocessing.cpu_count() // 2))

        command = [
            self.exe_path,
            "--model", self.path,
            "-ngl", ngl,
            "-t", threads,
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

    def _get_optimal_ngl(self) -> str:
        """Dinamically process the number of layer to load in the GPU"""
        system = platform.system().lower()

        if system == "darwin":
            try:
                mem_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip())
                ram_gb = mem_bytes / (1024**3)
                
                if ram_gb <= 8:
                    logger.warning("[AUTO-NGL] Mac 8GB detected. Limiting layers")
                    return "15"
                else:
                    return "99" 
            except Exception:
                return "15" 

        if self.device != "cuda":
            return "0"

        try:
            kwargs = {}
            if platform.system().lower() == "windows":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            result = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,nounits,noheader"],
                encoding="utf-8",
                **kwargs
            )
            free_vram_mb = int(result.strip().split('\n')[0])

            mb_per_layer = 140
            buffer_mb = 800 
            safe_vram_mb = free_vram_mb - buffer_mb

            if safe_vram_mb <= 0:
                logger.warning("VRAM almost full, model will run on CPU.")
                return "0"

            calculated_layers = math.floor(safe_vram_mb / mb_per_layer)

            optimal_ngl = min(calculated_layers, 99)

            logger.info(f"[AUTO-NGL] VRAM free: {free_vram_mb}MB. Layer calculated: {optimal_ngl}")
            return str(optimal_ngl)
            
        except Exception as e:
            logger.warning(f"[AUTO-NGL] Impossible to read nvidia-smi ({e}). Using 25 as fallback.")
            return "25"

    def stop_server(self):
        """
        Stop the Llama model server process.
        """
        if self.process:
            logger.info("\nClosing LLM server...")
            self.process.terminate()
            self.process.wait()
            self.process = None
            logger.info("Server closed.")