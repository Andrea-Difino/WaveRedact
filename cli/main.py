from safewave.utils.gpu_setup import GPUEnvironmentManager

gpu_manager = GPUEnvironmentManager()
gpu_manager.ensure_gpu_ready()

from faster_whisper import WhisperModel
from safewave.services.transcribe import TranscribeService
from safewave.utils.audio_manager import IOAudioManager
from safewave.utils.audio_censor import AudioCensor
from safewave.utils.chunk import Chunker
#from models.gguf_model import GGUFModel
from safewave.pipeline.orchestrator import DataPrivacyPipeline
#from services.llama_server import LlamaServerService
#import yaml
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(datefmt=FORMAT,level=logging.INFO, force=True)

logging.getLogger("httpx").setLevel(logging.WARNING)


logging.getLogger("gliner").setLevel(logging.WARNING)
logging.getLogger("gliner.model").setLevel(logging.WARNING)

logging.getLogger("huggingface_hub").setLevel(logging.WARNING)


def main() -> None:
    # VARIABLES
    #MAKER_MODEL_NAME = "Meta-Llama-3-8B-Instruct-Q5_K_S.gguf"
    #REPO_ID = "bartowski/Meta-Llama-3-8B-Instruct-GGUF"
    #SERVER_PORT = 8080

    #MODELS INITIALIZATION
    model_name = "large-v3-turbo"
    model = WhisperModel(model_name, device="cuda", compute_type="int8_float16")

    orchestrator = DataPrivacyPipeline()

    #with open("prompts.yaml", "r") as f:
    #    prompts = yaml.safe_load(f)

    transcribe_serv = TranscribeService(model)
    #maker = GGUFModel(prompts["maker"]["default"]["system_prompt"], MAKER_MODEL_NAME, REPO_ID, server_port=SERVER_PORT)
    #checker = GGUFModel(prompts["checker"]["default"]["system_prompt"], MAKER_MODEL_NAME, server)

    # SERVER INITIALIZATION
    #server = LlamaServerService(MAKER_MODEL_NAME, server_port=SERVER_PORT)
    #server.start_server()

    audio_manager = IOAudioManager()
    audios = audio_manager.get_audio()
    if len(audios) == 0:
        print("There's no audio to process. Terminating process...")
        return

    for audio_path in audios:
        transcribe_serv.transcribe_audio(str(audio_path))

        chunk_man = Chunker()
        chunks = chunk_man.chunk_text(transcribe_serv.iw_pair)
        len_chunks = len(chunks)

        print("Complete sentence:" , transcribe_serv.full_text.strip() , "\n")

        full_idx: set[int] = set()

        for i, chunk in enumerate(chunks):
            logger.info(f"Running chunk: {i+1}")
            res = orchestrator.extract_sensitive_data(chunk)

            words_finded = [transcribe_serv.iw_pair[idx] for idx in sorted(res)]
            full_idx.update(res)
            
            while True:
                user_question = input(f"\nThese are the words found by the first model:\n{words_finded}\n\nAre they right (Y/N)? ")
                
                if user_question.upper() == "Y":
                    if i + 1 == len_chunks:
                        print("Thanks for using SafeWave!")
                    else:
                        print("Continue with the next chunk...")
                    break
                elif user_question.upper() == "N":
                    print("Second check activated! Passaggio all'LLM...")
                    #TODO passare chunks a due LLM . Il primo é un modello piú piccolo e cerca di censurare le parole. Il secondo é più potente, fa quello che ha fatto il primo e sistema/aggiusta le censure. I due risultati che contengono gli id delle parole da censurare vengono messi in un set in modo da togliere i duplicati

                    break 
                else:
                    print("⚠️ Invalid input. Please enter Y or N.")
        
            
        intervals_to_censor = []
        for idx in full_idx:
            start_str, end_str = transcribe_serv.ival_pair[idx].split("-")
            intervals_to_censor.append((float(start_str), float(end_str)))

        censor_manager = AudioCensor()
        censor_manager.censor_file(str(audio_path), intervals_to_censor)


if __name__ == "__main__":
    main()