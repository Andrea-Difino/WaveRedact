from __future__ import annotations
import logging
import shutil
from pathlib import Path
from fastapi import UploadFile

from waveredact.factories.gliner_factory import GlinerFactory
from waveredact.factories.whisper_factory import WhisperFactory
from waveredact.pipeline.extractors.gliner_extractor import GlinerExtractor
from waveredact.pipeline.mapper import ChunkMapper
from waveredact.pipeline.orchestrator import Orchestrator
from waveredact.pipeline.privacy_pipeline import DataPrivacyPipeline
from waveredact.services.transcribe import TranscribeService
from waveredact.utils.audio_censor import AudioCensor, AudioMaskTypes
from waveredact.utils.chunk import Chunker
from waveredact.utils.gpu_setup import GPUEnvironmentManager
from waveredact.utils.level import LevelSetter

logger = logging.getLogger(__name__)

class AudioProcessingService:
    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent.parent.parent
        self.upload_dir = project_root / "files" / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.censored_dir = project_root / "audio" / "censored"
        self.censored_dir.mkdir(parents=True, exist_ok=True)

        self._chunker = Chunker()

    def load_models(self) -> None:
        """Method called once at server start"""
        logger.info("Loading models in VRAM...")
        
        gpu_setup = GPUEnvironmentManager()
        gpu_setup.ensure_gpu_ready()

        whisper_factory = WhisperFactory(gpu_setup)
        self._whisper_model = whisper_factory.build()

        gliner_factory = GlinerFactory(target_labels=[]) 
        self._gliner_model = gliner_factory.build()


    def process_upload(self, upload_file: UploadFile, level_name: str, censor_mode: str) -> dict:
        if not upload_file.filename:
            raise ValueError("Missing filename.")

        filename = Path(upload_file.filename).name
        temp_file_path = self.upload_dir / filename

        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

            levels_setter = LevelSetter(interactive=False, level_name=level_name)
            
            pipeline = DataPrivacyPipeline(
                GlinerExtractor(
                    self._gliner_model,
                    levels_setter.target_labels,
                    0.90
                )
            )

            transcribe_service = TranscribeService(self._whisper_model)
            transcribe_service.transcribe_audio(str(temp_file_path))


            chunks = self._chunker.chunk_text(transcribe_service.iw_pair)
            mappers = [ChunkMapper(chunk) for chunk in chunks]

            orchestrator = Orchestrator(
                index_word_pair=transcribe_service.iw_pair,
                mappers=mappers,
                data_pipeline=pipeline,
                auto_llm=False,
                interactive_mode=False,
            )

            full_idx = orchestrator.run_audio_chunks()
            sensitive_words = [transcribe_service.iw_pair[idx] for idx in sorted(full_idx)]

            censor_manager = AudioCensor(transcribe_service.ival_pair, full_idx)

            if censor_mode.lower() == "beep":
                censor_mode_enum = AudioMaskTypes.BEEP
            else:
                censor_mode_enum = AudioMaskTypes.SILENCE
            censored_file = censor_manager.censor_file(str(temp_file_path), mode=censor_mode_enum) 

            return {
                "status": "success",
                "filename": filename,
                "sensitive_words": sensitive_words,
                "censored_file": censored_file,
                "download_url": f"/api/v1/audio/redact/{Path(censored_file).name}"
            }
        except Exception:
            logger.exception("Error while processing uploaded audio")
            raise
        finally:
            if temp_file_path.exists():
                temp_file_path.unlink()
