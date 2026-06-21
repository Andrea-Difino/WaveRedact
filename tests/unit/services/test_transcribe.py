import pytest
from unittest.mock import MagicMock
from waveredact.services.transcribe import TranscribeService


class MockWord:
    """Emulate word object of faster_whisper"""
    def __init__(self, word: str, start: float, end: float):
        self.word = word
        self.start = start
        self.end = end

class MockSegment:
    """Emulate segment object of faster_whisper"""
    def __init__(self, words: list[MockWord] | None = None):
        self.words = words or []


class TestTranscribeService:

    def test_compute_idx_pair(self):
        """Text intern helper method for dict creation"""
        mock_model = MagicMock()
        service = TranscribeService(mock_model)
        
        data = ["Hello", "world", "test"]
        result = service._compute_idx_pair(data)
        
        assert result == {0: "Hello", 1: "world", 2: "test"}

    def test_transcribe_audio_success(self):
        """Testa the principal flow"""

        mock_model = MagicMock()

        word1 = MockWord(" Hello", 0.0, 1.5)
        word2 = MockWord(" world", 1.5, 2.5)
        segment1 = MockSegment([word1, word2])
        
        word3 = MockWord(" test", 3.0, 4.0)
        segment2 = MockSegment([word3])

        mock_model.transcribe.return_value = ([segment1, segment2], MagicMock())

        service = TranscribeService(mock_model)
        service.transcribe_audio("fake_audio.wav")

        mock_model.transcribe.assert_called_once_with(
            "fake_audio.wav",
            beam_size=5,
            word_timestamps=True,
        )

        assert service.full_text == " Hello world test"

        assert service.iw_pair == {
            0: " Hello",
            1: " world",
            2: " test"
        }
        
        assert service.ival_pair == {
            0: "0.0-1.5",
            1: "1.5-2.5",
            2: "3.0-4.0"
        }

    def test_transcribe_audio_empty_segments(self):
        """Test behavior for mute audio"""
        mock_model = MagicMock()
        
        mock_model.transcribe.return_value = ([], MagicMock())
        
        service = TranscribeService(mock_model)
        service.transcribe_audio("empty_audio.wav")
        
        assert service.full_text == ""
        assert service.iw_pair == {}
        assert service.ival_pair == {}

    def test_transcribe_audio_segment_without_words(self):
        """Testa il behavior if whisper return a result with segment but whithout word attribute"""
        mock_model = MagicMock()

        segment_no_words = MockSegment(words=[])
        mock_model.transcribe.return_value = ([segment_no_words], MagicMock())
        
        service = TranscribeService(mock_model)
        service.transcribe_audio("weird_audio.wav")
        
        assert service.full_text == ""
        assert service.iw_pair == {}
        assert service.ival_pair == {}