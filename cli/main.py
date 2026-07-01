from waveredact.utils.gpu_setup import GPUEnvironmentManager
from waveredact.utils.level import LevelSetter
import click

gpu_manager = GPUEnvironmentManager()
gpu_manager.ensure_gpu_ready()

from faster_whisper import WhisperModel
from waveredact.services.transcribe import TranscribeService
from waveredact.utils.audio_manager import IOAudioManager
from waveredact.utils.audio_censor import AudioCensor
from waveredact.utils.chunk import Chunker
from waveredact.pipeline.orchestrator import Orchestrator
from waveredact.factories.gliner_factory import GlinerFactory
from waveredact.pipeline.extractors.gliner_extractor import GlinerExtractor

from waveredact.models.gguf_model import GGUFModel
from waveredact.pipeline.privacy_pipeline import DataPrivacyPipeline
from waveredact.pipeline.mapper import ChunkMapper

from waveredact.services.llama_server import LlamaServerService
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(datefmt=FORMAT, level=logging.INFO, force=True)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("gliner").setLevel(logging.WARNING)
logging.getLogger("gliner.model").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

@click.command()
@click.option('--level', type=click.Choice(['base', 'medium', 'total'], case_sensitive=False), default='total', help='Level of PII censor. Used only if --auto is applied')
@click.option('--auto', is_flag=True, help='Disable interactive mode (no confirm required).')
@click.option('--use-llm', is_flag=True, help="Execute LLM to maximize precision.")
def main(level: str, auto: bool, use_llm: bool) -> None:
    # VARIABLES
    MAKER_MODEL_NAME = "Qwen2.5-14B-Instruct-Q5_K_S.gguf"
    REPO_ID = "bartowski/Qwen2.5-14B-Instruct-GGUF"
    SERVER_PORT = 8080

    click.secho(f"Starting WaveRedact - Auto: {auto} | LLM: {use_llm}", fg="cyan")

    # MODELS INITIALIZATION
    model_name = "large-v3-turbo"
    model = WhisperModel(model_name, device="cuda", compute_type="int8_float16")

    transcribe_serv = TranscribeService(model)
    maker = GGUFModel(MAKER_MODEL_NAME, REPO_ID, server_port=SERVER_PORT)
    # checker = GGUFModel(prompts["checker"]["default"]["system_prompt"], MAKER_MODEL_NAME, server)

    # SERVER INITIALIZATION
    server = LlamaServerService(MAKER_MODEL_NAME, server_port=SERVER_PORT)
    server.start_server()

    audio_manager = IOAudioManager()
    audios = audio_manager.get_audio()
    if len(audios) == 0:
        click.secho("There's no audio to process. Terminating process...", fg="yellow")
        return

    for audio_path in audios:
        transcribe_serv.transcribe_audio(str(audio_path))

        chunk_man = Chunker()
        chunks = chunk_man.chunk_text(transcribe_serv.iw_pair)

        mappers = [ChunkMapper(chunk) for chunk in chunks]
        
        levels_setter = LevelSetter(not auto, level_name=level)

        gliner_factory = GlinerFactory(target_labels=levels_setter.target_labels)
        maker.labels = levels_setter.target_labels

        privacy_pipeline = DataPrivacyPipeline(
            GlinerExtractor(
                gliner_factory.build(),
                gliner_factory.target_labels,
                gliner_factory.threshold,
            ),
            maker
        )

        orchestrator = Orchestrator(
            index_word_pair=transcribe_serv.iw_pair,
            mappers=mappers,
            data_pipeline=privacy_pipeline,
            auto_llm=use_llm,             
            interactive_mode=not auto
        )

        print("Complete sentence:", transcribe_serv.full_text.strip(), "\n")

        full_idx = orchestrator.run_audio_chunks()

        censor_manager = AudioCensor(transcribe_serv.ival_pair, full_idx)
        censor_manager.censor_file(str(audio_path))

    print("\nThanks for using waveredact!")


if __name__ == "__main__":
    main()
