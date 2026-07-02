from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path

from web.services.audio_processing_service import AudioProcessingService

router = APIRouter(prefix="/api/v1/audio", tags=["Audio Processing"])

def get_audio_service():
    from web.app import audio_service 
    return audio_service

@router.post("/process")
async def process_audio(
    file: UploadFile = File(...),
    level: str = Form("base"),       
    censor_mode: str = Form("muted"), 
    service: AudioProcessingService = Depends(get_audio_service)
):
    try:
        result = service.process_upload(file, level, censor_mode)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/redact/{filename}")
async def download_redact_file(
    filename: str,
    service: AudioProcessingService = Depends(get_audio_service)
):
    censored_path = service.censored_dir / Path(filename).name
    if not censored_path.exists():
        raise HTTPException(status_code=404, detail="File non trovato.")
    return FileResponse(censored_path, filename=censored_path.name)