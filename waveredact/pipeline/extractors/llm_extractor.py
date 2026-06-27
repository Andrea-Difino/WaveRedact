from typing import List, Tuple
from waveredact.models.model import Model
from waveredact.pipeline.extractors.base_extractor import BaseExtractor

class LlmExtractor(BaseExtractor):

    def __init__(self, model: Model):
        self.model = model

    def extract(self, text: str, old_idx: list[int] | None = None) -> List[Tuple[int, int]]:
        ...
        