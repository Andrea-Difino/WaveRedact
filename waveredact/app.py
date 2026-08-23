import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel
from gliner2 import GLiNER2

from waveredact.audio.audio_censor import AudioCensor, AudioMaskTypes
from waveredact.audio.audio_manager import IOAudioManager
from waveredact.config.level import LevelSetter
from waveredact.core.gpu_setup import GPUEnvironmentManager
from waveredact.core.memory_manager import MemoryManager
from waveredact.factories.gliner_factory import GlinerFactory
from waveredact.factories.whisper_factory import WhisperFactory
from waveredact.models.gguf_model import GGUFModel
from waveredact.pipeline.chunk import Chunker
from waveredact.pipeline.extractors.gliner_extractor import GlinerExtractor
from waveredact.pipeline.extractors.regex_extractor import RegexExtractor
from waveredact.pipeline.mapper import ChunkMapper
from waveredact.pipeline.orchestrator import Orchestrator
from waveredact.pipeline.privacy_pipeline import DataPrivacyPipeline
from waveredact.services.llama_server import LlamaServerService
from waveredact.services.transcribe import TranscribeService
from waveredact.utils.console import console

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    level: str
    auto: bool
    use_llm: bool
    mode: str
    file: str | None
    folder: str | None
    custom_labels: str | None

@dataclass
class RedactResult:
    filename: str
    censored_path: str
    sensitive_words: list[str]

class WaveRedactApplication:
    def __init__(
        self, 
        config: AppConfig, 
        approval_callback: Callable[[list[str]], bool] | None = None,
        progress_callback: Callable[[str, int], None] | None = None,
        whisper_model: WhisperModel | None = None,
        gliner_model: GLiNER2 | None = None,
        gpu_setup = None
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

    def run(self) -> list[RedactResult]:
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

        if self.config.file:
            audio_manager = IOAudioManager(input_path=self.config.file, is_file=True)
        else:
            audio_manager = IOAudioManager(input_path=self.config.folder, is_file=False) # type: ignore
            
        audios = audio_manager.get_audio()
        if not audios:
            console.print("[warning]⚠️ There's no audio to process. Terminating process...[/warning]")
            return []
        
        model = None
        server = None

        try:
            index_intervals: list[tuple[Path, dict[int, str], dict[int, str]]] = []
            memory_manager = MemoryManager()

            for audio_path in audios:
                if self.progress_callback:
                    self.progress_callback(f"Processing audio {audio_path.name}", 10)
                else:
                    console.print(f"[success]✅ Processing audio {audio_path}[/success]")
                    
                iw_pair, ival_pair = transcribe_serv.transcribe_audio(str(audio_path))
                console.print(f"Complete sentence: [info]{transcribe_serv.full_text.strip()}[/info]\n")
                index_intervals.append((audio_path, iw_pair, ival_pair))

            del whisper_model
            del transcribe_serv
            memory_manager.clean_memory()
            
            if self.config.use_llm:
                model = GGUFModel(self.MODEL_NAME, self.REPO_ID, server_port=self.SERVER_PORT)
                        
                try:
                    server = LlamaServerService(self.MODEL_NAME, server_port=self.SERVER_PORT, device=gpu_setup.device)
                    server.start_server()
                except Exception as exc:
                    logger.warning("LLM server unavailable, continuing without LLM: %s", exc)
                    model = None
                    server = None

            levels_setter = LevelSetter(not self.config.auto, level_name=self.config.level, custom_label_file=self.config.custom_labels)
                        
            if self.gliner_model is None:
                gliner_factory = GlinerFactory(target_labels=levels_setter.target_labels)
                gliner_model = gliner_factory.build()
                gliner_threshold = gliner_factory.threshold
            else:
                gliner_model = self.gliner_model
                gliner_threshold = 0.50

            if model:
                model.labels = levels_setter.target_labels

            gliner_extractor = GlinerExtractor(
                gliner_model,
                levels_setter.target_labels,
                gliner_threshold,
            )
                        
            regex_extractor = RegexExtractor(levels_setter.target_labels)
                        
            privacy_pipeline = DataPrivacyPipeline(
                simple_extractors=[regex_extractor, gliner_extractor],
                llm_extractor=model
            )
            
            results = []

            for audio_path, index_word, index_interval in index_intervals:
                chunk_man = Chunker()
                chunks = chunk_man.chunk_text(index_word)

                mappers = [ChunkMapper(chunk) for chunk in chunks]
                
                orchestrator = Orchestrator(
                    index_word_pair=index_word,
                    mappers=mappers,
                    data_pipeline=privacy_pipeline,
                    use_llm=self.config.use_llm and model is not None,
                    interactive_mode=not self.config.auto,
                    progress_callback=self.progress_callback,
                    approval_callback=self.approval_callback
                )

                full_idx = orchestrator.run_audio_chunks()
                sensitive_words = [index_word[idx] for idx in sorted(full_idx)]

                censor_manager = AudioCensor(audio_manager, index_interval, full_idx)
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
        except (FileNotFoundError, ValueError) as e:
            console.print(f"[bold red]❌ Configuration Error:[/bold red] {e}")
            return []
        except Exception as e:
            console.print(f"[bold red]❌ An unexpected error occurred:[/bold red] {e}")
            return []
        finally:
            if server:
                server.stop_server()
