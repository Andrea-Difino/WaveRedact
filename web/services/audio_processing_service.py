import logging
import asyncio
from pathlib import Path
from fastapi import UploadFile

from waveredact.pipeline.extractors.gliner_extractor import GlinerExtractor
from waveredact.pipeline.mapper import ChunkMapper
from waveredact.pipeline.orchestrator import Orchestrator
from waveredact.pipeline.privacy_pipeline import DataPrivacyPipeline
from waveredact.services.transcribe import TranscribeService
from waveredact.utils.audio_censor import AudioCensor, AudioMaskTypes
from waveredact.utils.chunk import Chunker
from waveredact.utils.level import LevelSetter

from web.services.file_service import FileService
from web.services.model_manager import ModelManager
from web.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

class AudioProcessingService:
    def __init__(self, file_service: FileService, model_manager: ModelManager, ws_manager: WebSocketManager):
        self.file_service = file_service
        self.model_manager = model_manager
        self.ws_manager = ws_manager
        self._chunker = Chunker()

    async def _send_ws_progress(self, client_id: str, message: str, percent: int = 0):
        if client_id:
            await self.ws_manager.send_message(client_id, {"status": "progress", "message": message, "percent": percent})

    def _process_audio_sync(self, temp_file_path: Path, level_name: str, censor_mode: str, client_id: str, loop: asyncio.AbstractEventLoop) -> dict:
        """Synchronous method to run the heavy ML models"""
        
        def progress_callback(msg: str, percent: int = 0):
            asyncio.run_coroutine_threadsafe(self._send_ws_progress(client_id, msg, percent), loop)
        
        progress_callback("Transcribing audio... (this may take a while)", 10)

        levels_setter = LevelSetter(interactive=False, level_name=level_name)
        
        pipeline = DataPrivacyPipeline(
            GlinerExtractor(
                self.model_manager.get_gliner_model(),
                levels_setter.target_labels,
                0.90
            )
        )

        transcribe_service = TranscribeService(self.model_manager.get_whisper_model())
        transcribe_service.transcribe_audio(str(temp_file_path))

        progress_callback("Transcription complete. Chunking text...", 40)

        chunks = self._chunker.chunk_text(transcribe_service.iw_pair)
        mappers = [ChunkMapper(chunk) for chunk in chunks]

        orchestrator = Orchestrator(
            index_word_pair=transcribe_service.iw_pair,
            mappers=mappers,
            data_pipeline=pipeline,
            use_llm=False,
            interactive_mode=False,
            progress_callback=progress_callback
        )

        full_idx = orchestrator.run_audio_chunks()
        sensitive_words = [transcribe_service.iw_pair[idx] for idx in sorted(full_idx)]

        progress_callback(f"Identified {len(sensitive_words)} sensitive words. Censoring audio...", 90)

        censor_manager = AudioCensor(transcribe_service.ival_pair, full_idx)

        if censor_mode.lower() == "beep":
            censor_mode_enum = AudioMaskTypes.BEEP
        else:
            censor_mode_enum = AudioMaskTypes.SILENCE
        censored_file = censor_manager.censor_file(str(temp_file_path), mode=censor_mode_enum) 

        return {
            "status": "success",
            "filename": temp_file_path.name,
            "sensitive_words": sensitive_words,
            "censored_file": censored_file,
            "download_url": f"/api/v1/audio/redact/{Path(censored_file).name}"
        }

    async def process_upload(self, upload_file: UploadFile, level_name: str, censor_mode: str, client_id: str = None) -> dict:
        temp_file_path = self.file_service.save_upload(upload_file)
        
        await self._send_ws_progress(client_id, "File uploaded successfully.", 5)
        loop = asyncio.get_running_loop()

        try:
            result = await asyncio.to_thread(self._process_audio_sync, temp_file_path, level_name, censor_mode, client_id, loop)
            await self._send_ws_progress(client_id, "Process completed!", 100)
            return result
        except Exception as e:
            logger.exception("Error while processing uploaded audio")
            await self._send_ws_progress(client_id, f"Error: {str(e)}", 100)
            raise
        finally:
            self.file_service.cleanup(temp_file_path)
