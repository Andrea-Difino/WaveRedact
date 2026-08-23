from waveredact.models.model import Model

from .extractors.base_extractor import BaseExtractor
from .mapper import ChunkMapper


class DataPrivacyPipeline:
    """
    Class that handle the sensitive data extractors and call them

    Attributes:
        simple_extractors    - list of BaseExtractor. BaseExtractor classes don't use llm to work
        llm_extractors       - list of Model. Model classes are LLM
    """

    def __init__(
        self,
        simple_extractors: list[BaseExtractor],
        llm_extractor: Model | None = None,
    ):
        self.simple_extractors: list[BaseExtractor] = simple_extractors

        self.llm_extractors: list[Model] = [llm_extractor] if llm_extractor else []

    def extract_sensitive_data(
        self, mapper: ChunkMapper, lock_threshold: float = 0.75
    ) -> tuple[set[int], set[int]]:
        """
        Call sequentially extractors inside simple_extractor and lock the idx of the sensitive data with a confidence higher than 0.95

        Params:
            mapper          - ChunkMapper that preserves all the information and word-idx correspondence of a chunk
            lock_threshold  - Threshold used to lock idx that must be redacted

        Returns:
            tuple with two sets. The first set has all the possible sensitive idx and the second only the locked ones
        """
        total_idx: set[int] = set()
        locked_idx: set[int] = set()

        for extractor in self.simple_extractors:
            coords = extractor.extract(mapper.text)

            for start, end, score in coords:
                word_indices = mapper.get_original_idxs(start, end)
                total_idx.update(word_indices)

                if score >= lock_threshold:
                    locked_idx.update(word_indices)

        return total_idx, locked_idx

    def extract_sensitive_with_llm(
        self, mapper: ChunkMapper, ambiguous_idx: list[int]
    ) -> set[int]:
        """
        Use LLM extractors to find sensitive data in the ambiguous indices.

        Params:
            mapper          - ChunkMapper containing chunk information
            ambiguous_idx   - list of indices that are ambiguous

        Return:
            set of integers representing the final sensitive indices
        """

        total_idx: set[int] = set()

        for extractor in self.llm_extractors:
            idx = extractor.run_model(mapper.chunk, ambiguous_idx)

            total_idx.update(idx)

        return total_idx
