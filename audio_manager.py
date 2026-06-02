from enum import Enum
from pathlib import Path

class AudioMaskTypes(Enum):
    BEEP = "beep"


class AudioManager:
    SUPPORTED_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.mp4', '.mkv', '.mov'}

    def __init__(self):
        self.path = "./audio/"
        self.audio_mask: AudioMaskTypes = AudioMaskTypes.BEEP

    def get_audio(self) -> list[str]:
        audio_files = []
        for file_path in Path(self.path).glob("*"):

            if not file_path.is_file():
                continue

            extension = file_path.suffix.lower()
            
            if extension not in self.SUPPORTED_EXTENSIONS:
                print(f"File ignored (Format not supported): {file_path.name}")
                continue
            
            audio_files.append(file_path)

        return audio_files

    def set_mask_type(self, type: AudioMaskTypes) -> None:
        self.audio_mask = type
