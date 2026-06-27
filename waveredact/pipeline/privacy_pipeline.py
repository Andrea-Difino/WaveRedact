from typing import List, Set
from .extractors.base_extractor import BaseExtractor
from .extractors.regex_extractor import RegexExtractor
from .extractors.gliner_extractor import GlinerExtractor
from .extractors.llm_extractor import LlmExtractor
from .mapper import ChunkMapper

class DataPrivacyPipeline:
    def __init__(
            self,
            gliner_extractor: GlinerExtractor,
            llm_extractor: LlmExtractor
        ):

        self.simple_extractors: List[BaseExtractor] = [
            RegexExtractor(),
            gliner_extractor
        ]

        self.llm_extractors: List[BaseExtractor] = [
            llm_extractor
        ]

    def extract_sensitive_data(self, mapper: ChunkMapper) -> Set[int]:
        total_idx: Set[int] = set()

        for extractor in self.simple_extractors:
            coords = extractor.extract(mapper.text)

            for start, end in coords:
                total_idx.update(mapper.get_original_idxs(start, end))

        return total_idx
    
    def extract_sensitive_with_llm(self, mapper: ChunkMapper, old_idx: List[int]) -> Set[int]:
        total_idx: Set[int] = set()

        for extractor in self.llm_extractors:
            coords = extractor.extract(mapper.text, old_idx)

            for start, end in coords:
                total_idx.update(mapper.get_original_idxs(start, end))

        return total_idx