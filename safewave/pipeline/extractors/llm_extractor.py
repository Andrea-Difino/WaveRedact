from typing import List, Tuple

from safewave.pipeline.extractors.base_extractor import BaseExtractor

class LlmExtractor(BaseExtractor):

    def __init__(self):
        ...

    def extract(self, text: str) -> List[Tuple[int, int]]:
        ...
        