from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import shutil
import os
from pathlib import Path

from safewave.utils.gpu_setup import GPUEnvironmentManager
from safewave.utils.chunk import Chunker
from safewave.pipeline.orchestrator import DataPrivacyPipeline
from safewave.services.transcribe import TranscribeService
from faster_whisper import WhisperModel
from fastapi.middleware.cors import CORSMiddleware

gpu_manager = GPUEnvironmentManager()
gpu_manager.ensure_gpu_ready()

app = FastAPI(title="SafeWave API", description="Local Data Privacy Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

project_root = Path(__file__).resolve().parent.parent
static_dir = project_root / "web" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def serve_frontend():
    """Restituisce l'interfaccia utente al caricamento della pagina."""
    index_path = static_dir / "index.html"
    
    if not index_path.exists():
        return {"error": "File index.html non trovato nella cartella static!"}
        
    return FileResponse(index_path)

@app.post("/api/v1/process-audio")
async def process_audio(file: UploadFile = File(...)):
    """Endpoint per caricare un file audio ed eseguire la pipeline di censura."""
    # Controllo formato (usando la stessa logica del tuo AudioManager)

    SUPPORTED_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.mp4'}
    if file.filename:
        file_extension = Path(file.filename).suffix.lower()
    else:
        return {
            "status": "fail",
            "filename": file.filename,
            "sensitive_words": []
        }

    if file_extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato audio non supportato.")
    
    pipeline = DataPrivacyPipeline()

    upload_dir = Path("./files/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = upload_dir / file.filename

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        model_name = "large-v3-turbo"
        model = WhisperModel(model_name, device="cuda", compute_type="int8_float16")

        transcribe_serv = TranscribeService(model)
        transcribe_serv.transcribe_audio(str(temp_file_path))
        # chunks = chunk_man.chunk_text(segments)
        # Per ora simuliamo un dizionario di chunk inviato alla pipeline

        chunk_man = Chunker()
        chunks = chunk_man.chunk_text(transcribe_serv.iw_pair)


        words_finded_all = []
        
        for i, chunk in enumerate(chunks):
            res = pipeline.extract_sensitive_data(chunk)

            words_finded = [transcribe_serv.iw_pair[idx] for idx in sorted(res)]
            words_finded_all.append(words_finded)
            
        
        return {
            "status": "success",
            "filename": file.filename,
            "sensitive_words": words_finded_all
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")
        
    finally:
        if temp_file_path.exists():
            os.remove(temp_file_path)

def start_server():
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=True)