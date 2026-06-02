from faster_whisper import WhisperModel
from audio_manager import AudioManager
from services.transcribe import TranscribeService
from utils.chunk import Chunker

def main() -> None:
    model_name = "large-v3-turbo"
    model = WhisperModel(model_name, device="cuda", compute_type="int8_float16")

    audio_manager = AudioManager()
    audios = audio_manager.get_audio()
    if len(audios) == 0:
        print("There's no audio to process. Terminating process...")
        return

    transcribe_serv = TranscribeService(model)

    for audio_path in audios:
        transcribe_serv.transcribe_audio(audio_path)
        chunk_man = Chunker()
        chunks = chunk_man.chunk_text(transcribe_serv.full_text)
        #TODO passare chunks a due LLM . Il primo é un modello piú piccolo e cerca di censurare le parole. Il secondo é più potente, fa quello che ha fatto il primo e sistema/aggiusta le censure. I due risultati che contengono gli id delle parole da censurare vengono messi in un set in modo da togliere i duplicati

if __name__ == "__main__":
    main()