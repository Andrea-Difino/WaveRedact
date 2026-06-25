from .base_extractor import BaseExtractor
from typing import List, Tuple
from gliner2 import GLiNER2
import os

class GlinerExtractor(BaseExtractor):
    def __init__(self, model_id: str, cache_dir: str, target_labels: List[str], threshold: float):
        self.target_labels = target_labels
        self.threshold = threshold

        if os.path.exists(cache_dir) and os.listdir(cache_dir):
            print(f"📦 [WaveRedact] Finded model '{cache_dir}'. Offline loading...")

            self.model = GLiNER2.from_pretrained(cache_dir, local_files_only=True)
        else:
            print(f"🌐 [WaveRedact] Model not finded locally. Downloading '{model_id}'... (Could take some minutes)")

            os.makedirs(cache_dir, exist_ok=True)
            self.model = GLiNER2.from_pretrained(model_id)
            self.model.save_pretrained(cache_dir)

            print(f"✅ [WaveRedact] Modello scaricato con successo e salvato in '{cache_dir}'!")

    def extract(self, text: str) -> List[Tuple[int, int]]:
        output = self.model.extract_entities(text, self.target_labels, threshold=self.threshold, include_spans=True)

        entities_dict = output.get("entities", {})

        extracted_tuples = set()
        
        print("PII finded - (The label associated to the word doesn't matter. The only important thing is that all the sensitive words were finded)\n")

        for label, entities_list in entities_dict.items():
            for entity in entities_list:
                print(f"{entity['text']} => {label}")
                extracted_tuples.add((entity["start"], entity["end"]))

        return sorted(list(extracted_tuples), key=lambda x: x[0])