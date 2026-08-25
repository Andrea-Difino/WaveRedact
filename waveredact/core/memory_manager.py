import gc
import psutil

import torch


class MemoryManager:
    def __init__(self):
        pass

    def clean_memory(self) -> None:
        gc.collect()

        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def get_available_ram(self) -> float:
        try:
            return psutil.virtual_memory().available / (1024**3)
        except Exception:
            return 8.0
