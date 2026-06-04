import os
import sys
if sys.platform.startswith('win'):
    try:
        import torch
        torch_lib_path = os.path.join(os.path.dirname(torch.__file__), "lib")
        
        # Aggiungiamo la cartella se esiste
        if os.path.exists(torch_lib_path):
            os.add_dll_directory(torch_lib_path)
            print(f"✅ DLL NVIDIA caricate con successo da: {torch_lib_path}")
        else:
            print("⚠️ Cartella torch/lib non trovata.")
    except ImportError:
        print("⚠️ Impossibile importare PyTorch per trovare le DLL.")

from faster_whisper import WhisperModel
from audio_manager import AudioManager
from services.transcribe import TranscribeService
from utils.chunk import Chunker
from models.llama8B import Llama8B
import yaml

def main() -> None:
    model_name = "large-v3-turbo"
    model = WhisperModel(model_name, device="cuda", compute_type="int8_float16")

    audio_manager = AudioManager()
    audios = audio_manager.get_audio()
    if len(audios) == 0:
        print("There's no audio to process. Terminating process...")
        return
    
    with open("prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)

    transcribe_serv = TranscribeService(model)
    maker = Llama8B(prompts["maker"]["default"]["system_prompt"])
    checker = Llama8B(prompts["checker"]["default"]["system_prompt"])

    for audio_path in audios:
        transcribe_serv.transcribe_audio(audio_path)
        print(transcribe_serv.iw_pair)
        chunk_man = Chunker()
        chunks = chunk_man.chunk_text(transcribe_serv.iw_pair)
        for chunk in chunks:
            res = maker.run_model(chunk)
            if len(res["redact_ids"]) != 0:
                #passare dati al modello checker
                ...
            #TODO passare chunks a due LLM . Il primo é un modello piú piccolo e cerca di censurare le parole. Il secondo é più potente, fa quello che ha fatto il primo e sistema/aggiusta le censure. I due risultati che contengono gli id delle parole da censurare vengono messi in un set in modo da togliere i duplicati

if __name__ == "__main__":
    main()