from __future__ import annotations

from pydantic import BaseModel


class AudioProcessingResponse(BaseModel):
    status: str
    filename: str
    sensitive_words: list[str]
    censored_file: str
    download_url: str
