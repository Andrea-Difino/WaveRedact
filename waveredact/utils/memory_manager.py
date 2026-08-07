import gc

import torch


class MemoryManager():

    def __init__(self):
        pass

    def clean_memory(self) -> None:
        gc.collect()

        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
