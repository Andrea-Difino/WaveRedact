import logging
from faster_whisper import WhisperModel
from gliner2 import GLiNER2
from waveredact.factories.gliner_factory import GlinerFactory
from waveredact.factories.whisper_factory import WhisperFactory
from waveredact.core.gpu_setup import GPUEnvironmentManager


logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self._whisper_model: WhisperModel = None
        self._gliner_model: GLiNER2 = None

    def load_models(self):
        logger.info("Loading models in VRAM...")
        
        gpu_setup = GPUEnvironmentManager()
        gpu_setup.ensure_gpu_ready()

        whisper_factory = WhisperFactory(gpu_setup)
        self._whisper_model = whisper_factory.build()

        gliner_factory = GlinerFactory(target_labels=[]) 
        self._gliner_model = gliner_factory.build()
        logger.info("Models loaded successfully.")

    def get_whisper_model(self):
        return self._whisper_model

    def get_gliner_model(self):
        return self._gliner_model
