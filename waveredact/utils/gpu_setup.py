import os
import sys
import urllib.request
import zipfile
import torch
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class GPUEnvironmentManager:

    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent.parent.parent

        self.dll_folder = str(project_root / "files" / "server")
        self.device: str = self.get_device()

    def ensure_gpu_ready(self) -> None:
        if sys.platform.startswith('win') and self.device == "cuda":
            os.makedirs(self.dll_folder, exist_ok=True)
            dll_path = os.path.join(self.dll_folder, "cublas64_12.dll")
            if not os.path.exists(dll_path):
                self._download_and_extract_dlls()
            self._inject_dlls()

        device = self.device
        logger.info(f"Hardware detected for inference: {device.upper()}")

    def _download_and_extract_dlls(self) -> None:
        logger.info("Downloading NVIDIA libraries (CUDA 12) for the GPU...")

        url_dll = "https://github.com/ggml-org/llama.cpp/releases/download/b9538/cudart-llama-bin-win-cuda-12.4-x64.zip"
        zip_dll_path = os.path.join(self.dll_folder, "cuda_dlls.zip")

        urllib.request.urlretrieve(url_dll, zip_dll_path)

        logger.info("Extracting libraries...")
        with zipfile.ZipFile(zip_dll_path, 'r') as zip_ref:
            zip_ref.extractall(self.dll_folder)

        os.remove(zip_dll_path)
        logger.info("NVIDIA libraries downloaded!")

    def _inject_dlls(self) -> None:
        try:
            os.add_dll_directory(self.dll_folder)
            os.environ["PATH"] = f"{self.dll_folder};{os.environ.get('PATH', '')}"
            logger.info("✅ [GPU Setup] DLL NVIDIA injected and ready to use.")
        except Exception as e:
            logger.warning(f"Impossible to inject DLLs : {e}")

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