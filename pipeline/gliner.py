from typing import Dict, List, Set
from .extractors.base_extractor import BaseExtractor
from .extractors.gliner_extractor import GlinerExtractor
from .extractors.regex_extractor import RegexExtractor
from .mapper import ChunkMapper

class GlinerModel:
    def __init__(
            self,
            model_id: str = "urchade/gliner_medium-v2.1", 
            cache_dir: str = "./files/gliner_models",
            target_labels: List[str] | None = None,
            threshold: float = 0.47
        ):
        target_labels = target_labels if target_labels else [
            "person", "first name", "last name", "password",
            "street address", "city", "state", "hospital",
            "bank account number",
        ]
        
        self.extractors: List[BaseExtractor] = [
            RegexExtractor(),
            GlinerExtractor(model_id, cache_dir, target_labels, threshold)
        ]

    def extract_sensitive_data(self, chunk: Dict[int, str]) -> Set[int]:
    
        mapper = ChunkMapper(chunk)
        total_idx: Set[int] = set()

        for extractor in self.extractors:
            coords = extractor.extract(mapper.text)

            for start, end in coords:
                total_idx.update(mapper.get_original_idxs(start, end))

        return total_idx