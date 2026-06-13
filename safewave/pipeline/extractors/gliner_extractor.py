from .base_extractor import BaseExtractor
from typing import List, Tuple
from gliner import GLiNER

class GlinerExtractor(BaseExtractor):
    def __init__(self, model_id: str, cache_dir: str, target_labels: List[str], threshold: float):
        self.target_labels = target_labels
        self.threshold = threshold
        self.model = GLiNER.from_pretrained(model_id=model_id, cache_dir=cache_dir)

    def extract(self, text: str) -> List[Tuple[int, int]]:
        entities = self.model.predict_entities(text, self.target_labels, threshold=self.threshold)
        return [(entity["start"], entity["end"]) for entity in entities]