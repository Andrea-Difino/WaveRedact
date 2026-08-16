from unittest.mock import MagicMock, patch

import pytest

from waveredact.app import AppConfig, WaveRedactApplication


class TestWaveRedactApplication:
    def test_app_config_initialization(self):
        config = AppConfig(
            level="base",
            auto=True,
            use_llm=False,
            mode="beep",
            file="test.mp3",
            folder=None,
            custom_labels=None
        )
        assert config.level == "base"
        assert config.auto is True
        assert config.use_llm is False
        assert config.mode == "beep"
        assert config.file == "test.mp3"
        assert config.folder is None
        assert config.custom_labels is None

    def test_app_initialization(self):
        config = AppConfig(
            level="base",
            auto=True,
            use_llm=False,
            mode="beep",
            file="test.mp3",
            folder=None,
            custom_labels=None
        )
        callback = MagicMock()
        app = WaveRedactApplication(config=config, approval_callback=callback)
        
        assert app.config == config
        assert app.approval_callback == callback
        assert app.MODEL_NAME == "Qwen2.5-7B-Instruct-Q5_K_M.gguf"

    @patch("waveredact.app.GPUEnvironmentManager")
    @patch("waveredact.app.WhisperFactory")
    @patch("waveredact.app.TranscribeService")
    @patch("waveredact.app.IOAudioManager")
    @patch("waveredact.app.LevelSetter")
    @patch("waveredact.app.GlinerFactory")
    def test_app_run_no_audio(self, mock_gliner, mock_level, mock_io, mock_transcribe, mock_whisper, mock_gpu):
        config = AppConfig(
            level="base",
            auto=True,
            use_llm=False,
            mode="beep",
            file="test.mp3",
            folder=None,
            custom_labels=None
        )

        mock_io_instance = mock_io.return_value
        mock_io_instance.get_audio.return_value = []
        
        app = WaveRedactApplication(config=config)
        app.run()
        
        mock_io_instance.get_audio.assert_called_once()

    @patch("waveredact.app.GPUEnvironmentManager")
    @patch("waveredact.app.WhisperFactory")
    @patch("waveredact.app.TranscribeService")
    @patch("waveredact.app.IOAudioManager")
    @patch("waveredact.app.LevelSetter")
    @patch("waveredact.app.GlinerFactory")
    @patch("waveredact.app.GlinerExtractor")
    @patch("waveredact.app.RegexExtractor")
    @patch("waveredact.app.DataPrivacyPipeline")
    @patch("waveredact.app.Chunker")
    @patch("waveredact.app.Orchestrator")
    @patch("waveredact.app.AudioCensor")
    @patch("waveredact.app.MemoryManager")
    def test_app_run_with_audio(
        self, mock_mem, mock_censor, mock_orch, mock_chunker, mock_pipeline, 
        mock_regex, mock_gliner_ext, mock_gliner_fac, mock_level, mock_io, 
        mock_transcribe, mock_whisper, mock_gpu
    ):
        config = AppConfig(
            level="base",
            auto=True,
            use_llm=False,
            mode="beep",
            file="test.mp3",
            folder=None,
            custom_labels=None
        )

        mock_io_instance = mock_io.return_value
        from pathlib import Path
        mock_io_instance.get_audio.return_value = [Path("test.mp3")]
        
        mock_transcribe_instance = mock_transcribe.return_value
        mock_transcribe_instance.transcribe_audio.return_value = ({0: "test"}, {0: (0, 1)})
        mock_transcribe_instance.full_text = "test"
        
        mock_orch_instance = mock_orch.return_value
        mock_orch_instance.run_audio_chunks.return_value = [0]
        
        mock_censor_instance = mock_censor.return_value
        mock_censor_instance.censor_file.return_value = "test_censored.mp3"
        
        app = WaveRedactApplication(config=config)
        results = app.run()
        
        assert len(results) == 1
        assert results[0].filename == "test.mp3"
        assert results[0].censored_path == "test_censored.mp3"
        assert results[0].sensitive_words == ["test"]

    @patch("waveredact.app.GPUEnvironmentManager")
    @patch("waveredact.app.WhisperFactory")
    @patch("waveredact.app.MemoryManager")
    @patch("waveredact.app.GGUFModel")
    @patch("waveredact.app.LlamaServerService")
    @patch("waveredact.app.IOAudioManager")
    @patch("waveredact.app.TranscribeService")
    @patch("waveredact.app.LevelSetter")
    @patch("waveredact.app.GlinerFactory")
    @patch("waveredact.app.GlinerExtractor")
    @patch("waveredact.app.RegexExtractor")
    @patch("waveredact.app.DataPrivacyPipeline")
    @patch("waveredact.app.Chunker")
    @patch("waveredact.app.Orchestrator")
    @patch("waveredact.app.AudioCensor")
    def test_app_run_with_llm(
        self, mock_censor, mock_orch, mock_chunker, mock_pipeline, 
        mock_regex, mock_gliner_ext, mock_gliner_fac, mock_level, 
        mock_transcribe, mock_io, mock_llama, mock_gguf, mock_mem,
        mock_whisper, mock_gpu
    ):
        config = AppConfig(
            level="base",
            auto=True,
            use_llm=True,
            mode="silence",
            file="test.mp3",
            folder=None,
            custom_labels=None
        )

        mock_io_instance = mock_io.return_value
        from pathlib import Path
        mock_io_instance.get_audio.return_value = [Path("test.mp3")]
        
        mock_transcribe_instance = mock_transcribe.return_value
        mock_transcribe_instance.transcribe_audio.return_value = ({0: "test"}, {0: (0, 1)})
        mock_transcribe_instance.full_text = "test"
        
        app = WaveRedactApplication(config=config)
        app.run()
        
        mock_gguf.assert_called_once()
        mock_llama.assert_called_once()
        mock_llama_instance = mock_llama.return_value
        mock_llama_instance.start_server.assert_called_once()
        mock_llama_instance.stop_server.assert_called_once()