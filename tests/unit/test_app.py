from unittest.mock import MagicMock, patch

from waveredact.app import AppConfig, WaveRedactApplication


class TestWaveRedactApplication:
    def test_app_config_initialization(self):
        config = AppConfig(
            level="base",
            auto=True,
            use_llm=False,
            mode="beep",
            file="test.mp3",
            folder=None
        )
        assert config.level == "base"
        assert config.auto is True
        assert config.use_llm is False
        assert config.mode == "beep"
        assert config.file == "test.mp3"
        assert config.folder is None

    def test_app_initialization(self):
        config = AppConfig(
            level="base",
            auto=True,
            use_llm=False,
            mode="beep",
            file="test.mp3",
            folder=None
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
            folder=None
        )

        mock_io_instance = mock_io.return_value
        mock_io_instance.get_audio.return_value = []
        
        app = WaveRedactApplication(config=config)
        app.run()
        
        mock_io_instance.get_audio.assert_called_once()