import os
import math
import pytest
from pydub import AudioSegment
from pydub.generators import Sine

from safewave.utils.audio_censor import AudioCensor, AudioMaskTypes

class TestAudioCensor:

    @pytest.fixture
    def audio_censor(self, tmp_path):
        """tmp_path for the censored test audio"""
        test_dir = str(tmp_path / "censored_test_output")
        timestamps = {0:"1.0-2.0"}
        return AudioCensor(timestamps, {0}, rel_output_dir=test_dir)

    @pytest.fixture
    def dummy_audio_file(self, tmp_path):
        """
        Dummy audio file for test purpose
        """

        audio = Sine(440).to_audio_segment(duration=5000) 
        file_path = str(tmp_path / "dummy_input.wav")

        audio.export(file_path, format="wav") 
        return file_path

    @pytest.mark.parametrize("mode, expected_dbfs", [
        (AudioMaskTypes.SILENCE, float('-inf')),
        (AudioMaskTypes.BEEP, -18.01)
    ])

    def test_censor_file_applies_correct_mask(self, audio_censor, dummy_audio_file, mode, expected_dbfs):
        """
        Verify if censor is correctly applied to the audio
        """
        start_sec = 1.0
        end_sec = 2.0

        output_path = audio_censor.censor_file(
            input_path=dummy_audio_file,
            mode=mode
        )
        
        assert os.path.exists(output_path), "Censor file was not created"

        result_audio = AudioSegment.from_file(output_path)

        start_ms = int(start_sec * 1000)
        end_ms = int(end_sec * 1000)

        safe_margin = 50 
        censored_segment = result_audio[start_ms + safe_margin : end_ms - safe_margin]
        uncensored_segment = result_audio[0 : start_ms - safe_margin]

        
        if mode == AudioMaskTypes.SILENCE:
            assert censored_segment.dBFS == expected_dbfs, "The segment is not completely silence"
        elif mode == AudioMaskTypes.BEEP:
            assert math.isclose(censored_segment.dBFS, expected_dbfs, abs_tol=0.5), \
                f"The beep shoul be at {expected_dbfs} dBFS, but it is at {censored_segment.dBFS}"

        assert uncensored_segment.dBFS != censored_segment.dBFS, \
            "It seems that the outer audio have been modified"
        
    def test_enum_value(self):
        
        assert ["BEEP", "SILENCE"] == AudioMaskTypes._member_names_
        
        assert AudioMaskTypes.BEEP.value == "beep"
        assert AudioMaskTypes.SILENCE.value == "silence"