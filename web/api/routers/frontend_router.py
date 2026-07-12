from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from waveredact.utils.path_utils import get_project_root

router = APIRouter()
STATIC_DIR = get_project_root() / "web" / "static"

@router.get("/")
async def serve_frontend():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found.")
    return FileResponse(index_path)