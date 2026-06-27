from .base_extractor import BaseExtractor
from typing import List, Tuple
from gliner2 import GLiNER2


class GlinerExtractor(BaseExtractor):
    def __init__(self, model: GLiNER2, target_labels: List[str], threshold: float):
        self.target_labels = target_labels
        self.threshold = threshold

        self.model = model

    def extract(self, text: str, old_idx: list[int] | None = None) -> List[Tuple[int, int]]:
        output = self.model.extract_entities(text, self.target_labels, threshold=self.threshold, include_spans=True)

        entities_dict = output.get("entities", {})

        extracted_tuples = set()
        
        print("PII finded - (The label associated to the word doesn't matter. The only important thing is that all the sensitive words were finded)\n")

        for label, entities_list in entities_dict.items():
            for entity in entities_list:
                print(f"{entity['text']} => {label}")
                extracted_tuples.add((entity["start"], entity["end"]))

        return sorted(list(extracted_tuples), key=lambda x: x[0])