import logging
import click
from dataclasses import dataclass
from typing import Callable, Optional, List

from waveredact.factories.gliner_factory import GlinerFactory
from waveredact.factories.whisper_factory import WhisperFactory
from waveredact.models.gguf_model import GGUFModel
from waveredact.pipeline.extractors.gliner_extractor import GlinerExtractor
from waveredact.pipeline.extractors.regex_extractor import RegexExtractor
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

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    level: str
    auto: bool
    use_llm: bool
    mode: str
    file: Optional[str]
    folder: Optional[str]

@dataclass
class RedactResult:
    filename: str
    censored_path: str
    sensitive_words: List[str]

class WaveRedactApplication:
    def __init__(
        self, 
        config: AppConfig, 
        approval_callback: Callable[[list[str]], bool] | None = None,
        progress_callback: Callable[[str, int], None] | None = None,
        whisper_model=None,
        gliner_model=None,
        gpu_setup=None
    ):
        self.config = config
        self.approval_callback = approval_callback
        self.progress_callback = progress_callback
        
        self.whisper_model = whisper_model
        self.gliner_model = gliner_model
        self.gpu_setup = gpu_setup
        
        self.MODEL_NAME = "Qwen2.5-7B-Instruct-Q5_K_M.gguf"
        self.REPO_ID = "bartowski/Qwen2.5-7B-Instruct-GGUF"
        self.SERVER_PORT = 8080

    def run(self) -> List[RedactResult]:
        if self.gpu_setup is None:
            gpu_setup = GPUEnvironmentManager()
        else:
            gpu_setup = self.gpu_setup

        if self.whisper_model is None:
            whisper_factory = WhisperFactory(gpu_setup)
            whisper_model = whisper_factory.build()
        else:
            whisper_model = self.whisper_model

        transcribe_serv = TranscribeService(whisper_model)
        maker = None
        server = None

        if self.config.use_llm:
            maker = GGUFModel(self.MODEL_NAME, self.REPO_ID, server_port=self.SERVER_PORT)
            server = LlamaServerService(self.MODEL_NAME, server_port=self.SERVER_PORT, device=gpu_setup.device)
            try:
                server.start_server()
            except Exception as exc:
                logger.warning("LLM server unavailable, continuing without LLM: %s", exc)
                maker = None
                server = None

        if self.config.file:
            audio_manager = IOAudioManager(input_path=self.config.file, is_file=True)
        else:
            audio_manager = IOAudioManager(input_path=self.config.folder, is_file=False)
            
        audios = audio_manager.get_audio()
        if not audios:
            print("There's no audio to process. Terminating process...")
            if server:
                server.stop_server()
            return []

        try:
            levels_setter = LevelSetter(not self.config.auto, level_name=self.config.level)
            
            if self.gliner_model is None:
                gliner_factory = GlinerFactory(target_labels=levels_setter.target_labels)
                gliner_model = gliner_factory.build()
                gliner_threshold = gliner_factory.threshold
            else:
                gliner_model = self.gliner_model
                gliner_threshold = 0.90
                
            if maker:
                maker.labels = levels_setter.target_labels

            gliner_extractor = GlinerExtractor(
                gliner_model,
                levels_setter.target_labels,
                gliner_threshold,
            )
            
            regex_extractor = RegexExtractor()
            
            privacy_pipeline = DataPrivacyPipeline(
                simple_extractors=[regex_extractor, gliner_extractor],
                llm_extractor=maker
            )

            results = []

            for audio_path in audios:
                if self.progress_callback:
                    self.progress_callback(f"Processing audio {audio_path.name}", 10)
                else:
                    click.secho(f"Processing audio {audio_path}", fg='green')
                    
                transcribe_serv.transcribe_audio(str(audio_path))

                chunk_man = Chunker()
                chunks = chunk_man.chunk_text(transcribe_serv.iw_pair)

                mappers = [ChunkMapper(chunk) for chunk in chunks]
                
                orchestrator = Orchestrator(
                    index_word_pair=transcribe_serv.iw_pair,
                    mappers=mappers,
                    data_pipeline=privacy_pipeline,
                    use_llm=self.config.use_llm and maker is not None,
                    interactive_mode=not self.config.auto,
                    progress_callback=self.progress_callback,
                    approval_callback=self.approval_callback
                )

                print("Complete sentence:", transcribe_serv.full_text.strip(), "\n")

                full_idx = orchestrator.run_audio_chunks()
                sensitive_words = [transcribe_serv.iw_pair[idx] for idx in sorted(full_idx)]

                censor_manager = AudioCensor(audio_manager, transcribe_serv.ival_pair, full_idx)
                if self.config.mode == 'beep':
                    censor_mode = AudioMaskTypes.BEEP
                else:
                    censor_mode = AudioMaskTypes.SILENCE
                    
                if self.progress_callback:
                    self.progress_callback(f"Identified {len(sensitive_words)} sensitive words. Censoring audio...", 90)

                censored_file = censor_manager.censor_file(str(audio_path), mode=censor_mode)
                
                results.append(RedactResult(
                    filename=audio_path.name,
                    censored_path=censored_file,
                    sensitive_words=sensitive_words
                ))
                
            return results
        finally:
            if server:
                server.stop_server()
