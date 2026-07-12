from typing import List, Set, Tuple

from .extractors.base_extractor import BaseExtractor
from .extractors.gliner_extractor import GlinerExtractor
from .extractors.regex_extractor import RegexExtractor
from .mapper import ChunkMapper
from waveredact.models.model import Model


class DataPrivacyPipeline:
    """
    Class that handle the sensitive data extractors and call them

    Attributes:
        simple_extractors    - list of BaseExtractor. BaseExtractor classes don't use llm to work
        llm_extractors       - list of Model. Model classes are LLM
    """

    def __init__(
        self,
        gliner_extractor: GlinerExtractor,
        llm_extractor: Model | None = None,
    ):
        self.simple_extractors: List[BaseExtractor] = [
            RegexExtractor(),
            gliner_extractor,
        ]

        self.llm_extractors: List[Model] = [llm_extractor] if llm_extractor else []

    def extract_sensitive_data(
        self, mapper: ChunkMapper, lock_threshold: float = 0.99
    ) -> Tuple[Set[int], Set[int]]:
        """
        Call sequentially extractors inside simple_extractor and lock the idx of the sensitive data with a confidence higher than 0.99

        Params:
            mapper          - ChunkMapper that preserves all the information and word-idx correspondence of a chunk
            lock_threshold  - Threshold used to lock idx that must be redacted

        Returns:
            Tuple with two sets. The first set has all the possible sensitive idx and the second only the locked ones
        """
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

    def extract_sensitive_with_llm(
        self, mapper: ChunkMapper, ambiguous_idx: List[int]
    ) -> Set[int]:
        """
        Use LLM extractors to find sensitive data in the ambiguous indices.

        Params:
            mapper          - ChunkMapper containing chunk information
            ambiguous_idx   - List of indices that are ambiguous

        Return:
            Set of integers representing the final sensitive indices
        """
        

        total_idx: Set[int] = set()

        for extractor in self.llm_extractors:
            idx = extractor.run_model(mapper.chunk, ambiguous_idx)

            total_idx.update(idx)

        return total_idx
