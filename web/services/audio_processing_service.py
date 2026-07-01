from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from waveredact.factories.gliner_factory import GlinerFactory
from waveredact.factories.whisper_factory import WhisperFactory
from waveredact.pipeline.extractors.gliner_extractor import GlinerExtractor
from waveredact.pipeline.mapper import ChunkMapper
from waveredact.pipeline.orchestrator import Orchestrator
from waveredact.pipeline.privacy_pipeline import DataPrivacyPipeline
from waveredact.services.transcribe import TranscribeService
from waveredact.utils.audio_censor import AudioCensor
from waveredact.utils.audio_manager import IOAudioManager
from waveredact.utils.chunk import Chunker
from waveredact.utils.gpu_setup import GPUEnvironmentManager
from waveredact.utils.level import LevelSetter

logger = logging.getLogger(__name__)

@dataclass(slots=True)
class AudioProcessingResult:
    status: str
    filename: str
    sensitive_words: list[str]
    censored_file: str

    @property
    def download_url(self) -> str:
        return f"/api/v1/redacted/{Path(self.censored_file).name}"


class AudioProcessingService:
    def __init__(self, level_name: str = "total") -> None:
        project_root = Path(__file__).resolve().parent.parent.parent
        self.upload_dir = project_root / "files" / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.censored_dir = project_root / "audio" / "censored"
        self.censored_dir.mkdir(parents=True, exist_ok=True)

        self.levels_setter = LevelSetter(interactive=False, level_name=level_name)
        self._whisper_model = None
        self._data_pipeline: DataPrivacyPipeline | None = None
        self._chunker = Chunker()

    def _get_whisper_model(self):
        if self._whisper_model is None:
            gpu_setup = GPUEnvironmentManager()
            whisper_factory = WhisperFactory(gpu_setup)
            self._whisper_model = whisper_factory.build()

        return self._whisper_model

    def _get_data_pipeline(self) -> DataPrivacyPipeline:
        if self._data_pipeline is None:
            gliner_factory = GlinerFactory(target_labels=self.levels_setter.target_labels)
            gliner_model = gliner_factory.build()

            self._data_pipeline = DataPrivacyPipeline(
                GlinerExtractor(
                    gliner_model,
                    gliner_factory.target_labels,
                    gliner_factory.threshold,
                ),
            )

        return self._data_pipeline

    def process_upload(self, upload_file: UploadFile) -> AudioProcessingResult:
        if not upload_file.filename:
            raise ValueError("Missing filename.")

        filename = Path(upload_file.filename).name
        file_extension = Path(filename).suffix.lower()
        if file_extension not in IOAudioManager.SUPPORTED_EXTENSIONS:
            raise ValueError("Formato audio non supportato.")

        temp_file_path = self.upload_dir / filename

        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

            transcribe_service = TranscribeService(self._get_whisper_model())
            transcribe_service.transcribe_audio(str(temp_file_path))

            chunks = self._chunker.chunk_text(transcribe_service.iw_pair)
            mappers = [ChunkMapper(chunk) for chunk in chunks]

            orchestrator = Orchestrator(
                index_word_pair=transcribe_service.iw_pair,
                mappers=mappers,
                data_pipeline=self._get_data_pipeline(),
                auto_llm=False,
                interactive_mode=False,
            )

            full_idx = orchestrator.run_audio_chunks()
            sensitive_words = [transcribe_service.iw_pair[idx] for idx in sorted(full_idx)]

            censor_manager = AudioCensor(transcribe_service.ival_pair, full_idx)
            censored_file = censor_manager.censor_file(str(temp_file_path))

            return AudioProcessingResult(
                status="success",
                filename=filename,
                sensitive_words=sensitive_words,
                censored_file=censored_file,
            )
        except Exception:
            logger.exception("Error while processing uploaded audio")
            raise
        finally:
            if temp_file_path.exists():
                temp_file_path.unlink()
