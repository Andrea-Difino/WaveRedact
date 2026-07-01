from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from web.services.audio_processing_service import AudioProcessingService
from web.schemas.audio import AudioProcessingResponse


class AudioAPI:
    def __init__(self, service: AudioProcessingService, static_dir: Path) -> None:
        self.service = service
        self.static_dir = static_dir
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route("/", self.serve_frontend, methods=["GET"])
        self.router.add_api_route(
            "/api/v1/process-audio",
            self.process_audio,
            methods=["POST"],
            response_model=AudioProcessingResponse,
        )
        self.router.add_api_route("/api/v1/redacted/{filename}", self.download_redacted_file, methods=["GET"])

    async def serve_frontend(self):
        index_path = self.static_dir / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail="index.html not found.")

        return FileResponse(index_path)

    async def process_audio(self, file: UploadFile = File(...)):
        try:
            result = self.service.process_upload(file)
            return {
                "status": result.status,
                "filename": result.filename,
                "sensitive_words": result.sensitive_words,
                "censored_file": result.censored_file,
                "download_url": result.download_url,
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Errore interno: {str(exc)}") from exc

    async def download_redacted_file(self, filename: str):
        censored_path = self.service.censored_dir / Path(filename).name
        if not censored_path.exists():
            raise HTTPException(status_code=404, detail="Redacted file not found.")

        return FileResponse(censored_path, filename=censored_path.name)
