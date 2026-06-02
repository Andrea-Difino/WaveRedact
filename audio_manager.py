from os import listdir
from os.path import isfile, join
from enum import Enum
from faster_whisper import WhisperModel

class AudioMaskTypes(Enum):
    BEEP = "beep"


class AudioManager:

    def __init__(self):
        self.path = "./audio/"
        self.audio_mask: AudioMaskTypes = AudioMaskTypes.BEEP

    def get_audio(self) -> list[str]:
        audio_files = [self.path+f for f in listdir(self.path) if isfile(join(self.path, f))]
        return audio_files
    
    def set_mask_type(self, type: AudioMaskTypes) -> None:
        self.audio_mask = type
