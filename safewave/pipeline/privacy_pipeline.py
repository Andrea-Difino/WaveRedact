from typing import List, Set
from .extractors.base_extractor import BaseExtractor
from .extractors.regex_extractor import RegexExtractor
from .mapper import ChunkMapper
from safewave.factories.gliner_factory import GlinerFactory

class DataPrivacyPipeline:
    def __init__(
            self,
            gliner_factory: GlinerFactory,
        ):

        self.extractors: List[BaseExtractor] = [
            RegexExtractor(),
            gliner_factory.build()
        ]

    def extract_sensitive_data(self, mapper: ChunkMapper) -> Set[int]:

        total_idx: Set[int] = set()

        for extractor in self.extractors:
            coords = extractor.extract(mapper.text)

            for start, end in coords:
                total_idx.update(mapper.get_original_idxs(start, end))

        return total_idx