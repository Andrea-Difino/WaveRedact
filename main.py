from faster_whisper import WhisperModel
from audio_manager import AudioManager

def main():
    model_name = "large-v3-turbo"
    model = WhisperModel(model_name, device="cuda", compute_type="int8_float16")

    audio_manager = AudioManager()
    audios = audio_manager.get_audio()

    for audio_path in audios:
        words_list, intervals_list = audio_manager.transcribe_audio(audio_path, model)
        print(words_list)
        print(intervals_list)

if __name__ == "__main__":
    main()