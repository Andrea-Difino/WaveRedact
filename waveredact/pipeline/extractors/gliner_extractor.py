from .base_extractor import BaseExtractor
from typing import List, Tuple
from gliner2 import GLiNER2


class GlinerExtractor(BaseExtractor):
    """
    Extract sensitive entities using the GLiNER2 model.

    Attributes:
        target_labels   - List of entity labels to extract (e.g., PERSON, LOCATION)
        threshold       - Confidence threshold for entity extraction
        model           - GLiNER2 model instance
    """
    def __init__(self, model: GLiNER2, target_labels: List[str], threshold: float):
        self.target_labels = target_labels
        self.threshold = threshold

        self.model = model

    def extract(self, text: str) -> List[Tuple[int, int, float]]:
        print("[STEP 2] Using GLiNER2 extractor")
        output = self.model.extract_entities(text, self.target_labels, threshold=self.threshold, include_spans=True, include_confidence=True)

        entities_dict = output.get("entities", {})

        extracted_tuples = set()

        for label, entities_list in entities_dict.items():
            for entity in entities_list:
                score = float(entity.get("confidence", 0.0))
                extracted_tuples.add((entity["start"], entity["end"], score))

        return sorted(list(extracted_tuples), key=lambda x: x[0])