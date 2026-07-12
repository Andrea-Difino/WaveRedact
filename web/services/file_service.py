import shutil
from pathlib import Path
from fastapi import UploadFile
from waveredact.utils.path_utils import get_project_root

class FileService:
    def __init__(self):
        project_root = get_project_root()
        self.upload_dir = project_root / "files" / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.censored_dir = self.upload_dir / "censored"
        self.censored_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload_file: UploadFile) -> Path:
        if not upload_file.filename:
            raise ValueError("Missing filename.")
        
        filename = Path(upload_file.filename).name
        temp_file_path = self.upload_dir / filename

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        return temp_file_path

    def cleanup(self, path: Path):
        if path.exists():
            path.unlink()

    def get_censored_dir(self) -> Path:
        return self.censored_dir
