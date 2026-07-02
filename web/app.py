import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from web.services.audio_processing_service import AudioProcessingService
from web.api.routers import frontend_router, audio_router

audio_service = AudioProcessingService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    audio_service.load_models()
    yield

    print("Shutting down server and cleaning VRAM...")

def create_app() -> FastAPI:
    project_root = Path(__file__).resolve().parent.parent
    static_dir = project_root / "web" / "static"

    app = FastAPI(
        title="WaveRedact API", 
        description="Local Data Privacy Pipeline",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(frontend_router.router)
    app.include_router(audio_router.router)

    return app

app = create_app()

def start_server():
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000)