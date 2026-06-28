from typing import Dict, List

class ChunkMapper:
    def __init__(self, chunk: Dict[int, str]):
        self.chunk = chunk
        self.text = ""
        self.char_mapping = {}
        self._build_mapping()

    def _build_mapping(self) -> None:
        curr_char = 0
        for original_idx, word_text in self.chunk.items():
            start_char = curr_char
            self.text += word_text
            end_char = len(self.text)
            self.char_mapping[original_idx] = (start_char, end_char)
            curr_char = end_char

    def get_original_idxs(self, char_start: int, char_end: int) -> List[int]:
        """Convert  char position in the true Whsiper IDs"""
        found_idxs = []
        for idx, (w_start, w_end) in self.char_mapping.items():
            if char_start < w_end and char_end > w_start:
                found_idxs.append(idx)
        return found_idxs