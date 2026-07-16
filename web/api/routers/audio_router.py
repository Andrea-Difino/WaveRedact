from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional

from web.services.audio_processing_service import AudioProcessingService
from web.services.file_service import FileService
from web.core.dependencies import get_audio_service, get_file_service

router = APIRouter(prefix="/api/v1/audio", tags=["Audio Processing"])

@router.post("/process")
async def process_audio(
    file: UploadFile = File(...),
    level: str = Form("base"),       
    censor_mode: str = Form("muted"), 
    use_llm: bool = Form(False),
    client_id: Optional[str] = Form(None),
    service: AudioProcessingService = Depends(get_audio_service)
):
    try:
        result = await service.process_upload(file, level, censor_mode, use_llm, client_id)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/redact/{filename}")
async def download_redact_file(
    filename: str,
    file_service: FileService = Depends(get_file_service)
):
    censored_path = file_service.get_censored_dir() / Path(filename).name
    if not censored_path.exists():
        raise HTTPException(status_code=404, detail="File non trovato.")
    return FileResponse(censored_path, filename=censored_path.name)