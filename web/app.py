import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from web.api.audio_api import AudioAPI
from web.services.audio_processing_service import AudioProcessingService

def create_app() -> FastAPI:
    project_root = Path(__file__).resolve().parent.parent
    static_dir = project_root / "web" / "static"

    app = FastAPI(title="waveredact API", description="Local Data Privacy Pipeline API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    audio_service = AudioProcessingService()
    audio_api = AudioAPI(audio_service, static_dir)
    app.include_router(audio_api.router)

    return app


app = create_app()

def start_server():
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=True)