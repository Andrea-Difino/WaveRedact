import logging
import asyncio
from pathlib import Path
from fastapi import UploadFile

from waveredact.app import AppConfig, WaveRedactApplication

from web.services.file_service import FileService
from web.services.model_manager import ModelManager
from web.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

class AudioProcessingService:
    def __init__(self, file_service: FileService, model_manager: ModelManager, ws_manager: WebSocketManager):
        self.file_service = file_service
        self.model_manager = model_manager
        self.ws_manager = ws_manager

    async def _send_ws_progress(self, client_id: str, message: str, percent: int = 0):
        if client_id:
            await self.ws_manager.send_message(client_id, {"status": "progress", "message": message, "percent": percent})

    def _process_audio_sync(self, temp_file_path: Path, level_name: str, censor_mode: str, use_llm: bool, client_id: str, custom_labels: str | None, loop: asyncio.AbstractEventLoop) -> dict:
        """Synchronous method to run the heavy ML models"""
        
        def progress_callback(msg: str, percent: int = 0):
            asyncio.run_coroutine_threadsafe(self._send_ws_progress(client_id, msg, percent), loop)
        
        progress_callback("Starting analysis...", 5)

        custom_labels_file = None
        if level_name == 'custom' and custom_labels:
            import json
            custom_labels_file = str(temp_file_path.parent / f"custom_labels_{client_id}.json")
            try:
                # Custom labels comes as a JSON list string from JS
                labels_list = json.loads(custom_labels)
                with open(custom_labels_file, "w") as f:
                    json.dump(labels_list, f)
            except json.JSONDecodeError:
                raise ValueError("Invalid custom labels format")

        config = AppConfig(
            level=level_name,
            auto=True,
            use_llm=use_llm,
            mode=censor_mode,
            file=str(temp_file_path),
            folder=None,
            custom_labels=custom_labels_file
        )

        app = WaveRedactApplication(
            config=config,
            progress_callback=progress_callback,
            whisper_model=self.model_manager.get_whisper_model(),
            gliner_model=self.model_manager.get_gliner_model(),
            gpu_setup=None
        )
        
        results = app.run()
        
        if not results:
            raise RuntimeError("No results returned from the pipeline")
            
        result = results[0]

        return {
            "status": "success",
            "filename": result.filename,
            "sensitive_words": result.sensitive_words,
            "censored_file": result.censored_path,
            "download_url": f"/api/v1/audio/redact/{Path(result.censored_path).name}"
        }

    async def process_upload(self, upload_file: UploadFile, level_name: str, censor_mode: str, use_llm: bool, client_id: str = None, custom_labels: str = None) -> dict:
        temp_file_path = self.file_service.save_upload(upload_file)
        
        await self._send_ws_progress(client_id, "File uploaded successfully.", 5)
        loop = asyncio.get_running_loop()

        custom_labels_file = str(temp_file_path.parent / f"custom_labels_{client_id}.json") if client_id else None

        try:
            result = await asyncio.to_thread(self._process_audio_sync, temp_file_path, level_name, censor_mode, use_llm, client_id, custom_labels, loop)
            await self._send_ws_progress(client_id, "Process completed!", 100)
            return result
        except Exception as e:
            logger.exception("Error while processing uploaded audio")
            await self._send_ws_progress(client_id, f"Error: {str(e)}", 100)
            raise
        finally:
            self.file_service.cleanup(temp_file_path)
            if custom_labels_file:
                import os
                if os.path.exists(custom_labels_file):
                    os.remove(custom_labels_file)
