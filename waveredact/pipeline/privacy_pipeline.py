from typing import List, Set, Tuple
from .extractors.base_extractor import BaseExtractor
from .extractors.regex_extractor import RegexExtractor
from .extractors.gliner_extractor import GlinerExtractor
from waveredact.models.model import Model
from .mapper import ChunkMapper

class DataPrivacyPipeline:
    def __init__(
            self,
            gliner_extractor: GlinerExtractor,
            llm_extractor: Model
        ):

        self.simple_extractors: List[BaseExtractor] = [
            RegexExtractor(),
            gliner_extractor
        ]

        self.llm_extractors: List[Model] = [
            llm_extractor
        ]

    def extract_sensitive_data(self, mapper: ChunkMapper, lock_threshold: float = 0.90) -> Tuple[Set[int], Set[int]]:
        total_idx: Set[int] = set()
        locked_idx: Set[int] = set()

        for extractor in self.simple_extractors:
            coords = extractor.extract(mapper.text)

            for start, end, score in coords:
                word_indices = mapper.get_original_idxs(start, end)
                total_idx.update(word_indices)

                if score >= lock_threshold:
                    locked_idx.update(word_indices)

        return total_idx, locked_idx
    
    def extract_sensitive_with_llm(self, mapper: ChunkMapper, ambiguous_idx: List[int]) -> Set[int]:
        total_idx: Set[int] = set()

        for extractor in self.llm_extractors:
            idx = extractor.run_model(mapper.chunk, ambiguous_idx)

            total_idx.update(idx)

        return total_idx