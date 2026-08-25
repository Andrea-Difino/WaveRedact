import logging
import os
import sys
import urllib.request
import zipfile

import torch

from waveredact.utils.console import console
from waveredact.utils.path_utils import get_app_data_dir

logger = logging.getLogger(__name__)

class GPUEnvironmentManager:
    """
    Manage the setup and configuration of the GPU environment for model inference.

    Attributes:
        dll_folder      - Path to the folder where DLLs will be stored
        device          - The selected hardware device (e.g., cuda or cpu)
    """
    def __init__(self) -> None:
        self.dll_folder = str(get_app_data_dir() / "files" / "server")
        self.device: str = self.get_device()

    def ensure_gpu_ready(self) -> None:
        """
        Verify the GPU environment is ready, downloading and injecting necessary DLLs if needed.
        """
        if sys.platform.startswith('win') and self.device == "cuda":
            os.makedirs(self.dll_folder, exist_ok=True)
            dll_path = os.path.join(self.dll_folder, "cublas64_12.dll")
            if not os.path.exists(dll_path):
                self._download_and_extract_dlls()
            self._inject_dlls()

        device = self.device
        print(f"Hardware detected for inference: {device.upper()}\n")

    def _download_and_extract_dlls(self) -> None:
        with console.status("Downloading NVIDIA libraries (CUDA 12) for the GPU...", spinner="dots") as status:
            url_dll = "https://github.com/ggml-org/llama.cpp/releases/download/b9538/cudart-llama-bin-win-cuda-12.4-x64.zip"
            zip_dll_path = os.path.join(self.dll_folder, "cuda_dlls.zip")

            urllib.request.urlretrieve(url_dll, zip_dll_path)

            status.update("Extracting libraries...")
            with zipfile.ZipFile(zip_dll_path, 'r') as zip_ref:
                zip_ref.extractall(self.dll_folder)

            os.remove(zip_dll_path)
            console.print("[success]✅ NVIDIA libraries downloaded![/success]")

    def _inject_dlls(self) -> None:
        try:
            os.add_dll_directory(self.dll_folder)
            os.environ["PATH"] = f"{self.dll_folder};{os.environ.get('PATH', '')}"
            logger.info("[success]✅ [GPU Setup] DLL NVIDIA injected and ready to use.[/success]")
        except Exception as e:
            console.print(f"[warning]⚠️ Failed to inject DLLs: {e}[/warning]")

    def get_device(self) -> str:
        """Detect best hardware available"""
        if torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"        

    def get_compute_type(self, device: str) -> str:
        """Return data format supported by the hardware."""
        if device == "cuda":
            return "int8_float16"
        else:
            return "int8"