from faster_whisper import WhisperModel

class TranscribeService:

    def __init__(self, model: WhisperModel):
        self.model = model
        self.iw_pair: dict[int, str]
        self.ival_pair: dict[int, str]
        self.full_text: str

    def transcribe_audio(self, audio_path: str):

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
        result = {i:w for i,w in enumerate(data)}
        return result
        
    
