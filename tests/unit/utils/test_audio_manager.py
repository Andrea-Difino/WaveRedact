import pytest
from waveredact.utils.audio_manager import IOAudioManager
from pydub.generators import Sine

class TestAudioManager:

    @pytest.fixture
    def test_audio_dir(self, tmp_path):
        """
        Create the tmp path for the test
        """
        target_dir = tmp_path / "audio_test_output"
        target_dir.mkdir(exist_ok=True)
        return target_dir

    @pytest.fixture
    def audio_manager(self, test_audio_dir):
        """
        Initializa manager with the tmp path
        """
        return IOAudioManager(input_path=str(test_audio_dir))

    def test_creates_audio_folder_if_missing(self, tmp_path):
        missing_dir = tmp_path / "missing_audio"

        assert not missing_dir.exists()

        manager = IOAudioManager(input_path=str(missing_dir))

        assert missing_dir.exists()
        assert manager.path == str(missing_dir)
    
    @pytest.fixture
    def dummy_audio_files(self, test_audio_dir):
        file_paths = []
        
        for i in range(1, 4):
            file_path = test_audio_dir / f"dummy_input{i}.wav"
            
            audio = Sine(440).to_audio_segment(duration=100)
            audio.export(str(file_path), format="wav") 
            
            file_paths.append(file_path) 
            
        return file_paths
    
    def test_get_audio(self, audio_manager, dummy_audio_files):
        files = audio_manager.get_audio()

        assert sorted(files) == sorted(dummy_audio_files), "The manager didn't find the correct files"

    def test_supported_extensions(self, audio_manager):
        difference = audio_manager.SUPPORTED_EXTENSIONS.difference({'.mp3', '.wav', '.flac', '.m4a', '.ogg'})

        assert len(difference) == 0, "Supported extensions missmatch"

        