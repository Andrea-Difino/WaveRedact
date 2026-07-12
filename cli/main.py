import logging

import click
from dotenv import load_dotenv
from pathlib import Path

from waveredact.factories.gliner_factory import GlinerFactory
from waveredact.factories.whisper_factory import WhisperFactory
from waveredact.models.gguf_model import GGUFModel
from waveredact.pipeline.extractors.gliner_extractor import GlinerExtractor
from waveredact.pipeline.mapper import ChunkMapper
from waveredact.pipeline.orchestrator import Orchestrator
from waveredact.pipeline.privacy_pipeline import DataPrivacyPipeline
from waveredact.services.llama_server import LlamaServerService
from waveredact.services.transcribe import TranscribeService
from waveredact.utils.audio_censor import AudioCensor, AudioMaskTypes
from waveredact.utils.audio_manager import IOAudioManager
from waveredact.utils.chunk import Chunker
from waveredact.utils.gpu_setup import GPUEnvironmentManager
from waveredact.utils.level import LevelSetter

project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(datefmt=FORMAT, level=logging.WARNING, force=True)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("gliner").setLevel(logging.WARNING)
logging.getLogger("gliner.model").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

@click.command()
@click.option(
    '--level', 
    type=click.Choice(['base', 'medium', 'total'], case_sensitive=False), 
    default='total', 
    help='''Level of PII censor. Used only if --auto is applied. Levels:

    \b
    1) Base level: Immediately redact sensitive information that could compromise the security of your accounts or savings. Remove passwords, digital access keys, tokens, and banking
    or credit card details.
    \b
    2) Medium level: It extends Base level to ensure maximum compliance with privacy regulations. It removes any data that could directly identify you or other individuals, such as 
    names, email addresses, phone numbers, and identification documents.
    \b
    3) Total level: Beyond protecting accounts and identities, it eliminates every trace of geographic and temporal context—removing addresses, cities, states, and any dates 
    mentioned in the audio—thereby rendering the conversation completely decontextualized.'''
)
@click.option('--auto', is_flag=True, help='Disable interactive mode (no confirm required).')
@click.option('--use-llm', is_flag=True, help="Execute LLM to maximize precision.")
@click.option('--mode', type=click.Choice(['beep', 'muted'], case_sensitive=False), default='muted', help='Censor mode')
def main(level: str, auto: bool, use_llm: bool, mode: str) -> None:

    # VARIABLES
    MAKER_MODEL_NAME = "Qwen2.5-7B-Instruct-Q5_K_M.gguf"
    REPO_ID = "bartowski/Qwen2.5-7B-Instruct-GGUF"
    SERVER_PORT = 8080

    click.secho(f"Starting WaveRedact - Auto: {auto} | LLM: {use_llm} | Censor: {mode}", fg="cyan")

    # MODELS INITIALIZATION
    gpu_setup = GPUEnvironmentManager()
    whisper_factory = WhisperFactory(gpu_setup)
    whisper_model = whisper_factory.build()

    transcribe_serv = TranscribeService(whisper_model)
    maker = None

    if use_llm:
        maker = GGUFModel(MAKER_MODEL_NAME, REPO_ID, server_port=SERVER_PORT)

        # SERVER INITIALIZATION
        server = LlamaServerService(MAKER_MODEL_NAME, server_port=SERVER_PORT, device=gpu_setup.device)

        try:
            server.start_server()
        except Exception as exc:
            logger.warning("LLM server unavailable, continuing without LLM: %s", exc)
            maker = None

    audio_manager = IOAudioManager()
    audios = audio_manager.get_audio()
    if not audios:
        click.secho("There's no audio to process. Terminating process...", fg="yellow")
        return

    levels_setter = LevelSetter(not auto, level_name=level)

    gliner_factory = GlinerFactory(target_labels=levels_setter.target_labels)
    if maker:
        maker.labels = levels_setter.target_labels

    privacy_pipeline = DataPrivacyPipeline(
        GlinerExtractor(
            gliner_factory.build(),
            gliner_factory.target_labels,
            gliner_factory.threshold,
        ),
        maker
    )

    for audio_path in audios:
        click.secho(f"Processing audio {audio_path}", fg='green')
        transcribe_serv.transcribe_audio(str(audio_path))

        chunk_man = Chunker()
        chunks = chunk_man.chunk_text(transcribe_serv.iw_pair)

        mappers = [ChunkMapper(chunk) for chunk in chunks]
        
        orchestrator = Orchestrator(
            index_word_pair=transcribe_serv.iw_pair,
            mappers=mappers,
            data_pipeline=privacy_pipeline,
            use_llm=use_llm and maker is not None,
            interactive_mode=not auto
        )

        print("Complete sentence:", transcribe_serv.full_text.strip(), "\n")

        full_idx = orchestrator.run_audio_chunks()

        censor_manager = AudioCensor(audio_manager, transcribe_serv.ival_pair, full_idx)
        if mode == 'beep':
            censor_mode = AudioMaskTypes.BEEP
        else:
            censor_mode = AudioMaskTypes.SILENCE
        censor_manager.censor_file(str(audio_path), mode = censor_mode)

    click.secho("Thanks for using waveredact! 🌊", fg="cyan")


if __name__ == "__main__":
    main()
