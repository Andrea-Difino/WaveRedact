from faster_whisper import WhisperModel

class TranscribeService:
    """
    Handle transcription of audio files using WhisperModel.

    Attributes:
        model           - WhisperModel instance
        iw_pair         - Dictionary mapping indices to words
        ival_pair       - Dictionary mapping indices to intervals
        full_text       - Full transcribed text string
    """

    def __init__(self, model: WhisperModel):
        self.model = model
        self.iw_pair: dict[int, str]
        self.ival_pair: dict[int, str]
        self.full_text: str

    def transcribe_audio(self, audio_path: str):
        """
        Transcribe the given audio file and populate full text, word pairs, and interval pairs.

        Params:
            audio_path  - Path to the audio file
        """

        segments, _ = self.model.transcribe(audio_path, beam_size=5, word_timestamps=True)
        words_list: list[str] = []
        intervals_list: list[str] = []

        for segment in segments:
            if segment.words:
                for word in segment.words:
                    words_list.append(word.word)
                    intervals_list.append(f"{word.start}-{word.end}")

        self.full_text = "".join(words_list)
        self.iw_pair = self._compute_idx_pair(words_list)
        self.ival_pair = self._compute_idx_pair(intervals_list)
    
    def _compute_idx_pair(self, data: list[str]) -> dict[int, str]:
        """
        Create a dictionary mapping an index to a string in a list.

        Params:
            data        - List of strings

        Return:
            Dictionary mapping integers to strings
        """
        result = {i:w for i,w in enumerate(data)}
        return result
        
    
