import logging
from faster_whisper import WhisperModel
from waveredact.utils.gpu_setup import GPUEnvironmentManager


logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(datefmt=FORMAT, level=logging.WARNING, force=True)


class WhisperFactory:
    def __init__(
        self,
        gpu_manager: GPUEnvironmentManager,
        model_name: str = "large-v3-turbo",
    ):
        self.model_name = model_name
        self.gpu_manager = gpu_manager

    def build(self) -> WhisperModel:
        self.gpu_manager.ensure_gpu_ready()
        device = self.gpu_manager.get_device()
        return WhisperModel(
            self.model_name,
            device=device,
            compute_type=self.gpu_manager.get_compute_type(device),
        )
