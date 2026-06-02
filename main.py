from faster_whisper import WhisperModel
from audio_manager import AudioManager
from services.transcribe import TranscribeService

def main():
    model_name = "large-v3-turbo"
    model = WhisperModel(model_name, device="cuda", compute_type="int8_float16")

    audio_manager = AudioManager()
    audios = audio_manager.get_audio()

    transcribe_serv = TranscribeService(model)

    for audio_path in audios:
        transcribe_serv.transcribe_audio(audio_path)
        print(transcribe_serv.full_text)
        print(transcribe_serv.ival_pair)
        print(transcribe_serv.iw_pair)

if __name__ == "__main__":
    main()