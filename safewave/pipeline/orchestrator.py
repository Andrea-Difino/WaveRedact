from typing import Dict, List, Set
from .extractors.base_extractor import BaseExtractor
from .extractors.gliner_extractor import GlinerExtractor
from .extractors.regex_extractor import RegexExtractor
from .mapper import ChunkMapper
from pathlib import Path

class DataPrivacyPipeline:
    def __init__(
            self,
            model_id: str = "urchade/gliner_medium-v2.1", 
            cache_dir: str | None = None,
            target_labels: List[str] | None = None,
            threshold: float = 0.47
        ):
        target_labels = target_labels if target_labels else [
            "person", "first name", "last name", "password",
            "street address", "city", "state", "hospital",
            "bank account number", "email"
        ]
        
        if not cache_dir:
            project_root = Path(__file__).resolve().parent.parent.parent

            safe_cache_dir = project_root / "files" / "gliner_models"

            self.cache_dir = str(safe_cache_dir)
        else:
            self.cache_dir = cache_dir

        self.extractors: List[BaseExtractor] = [
            RegexExtractor(),
            GlinerExtractor(model_id, self.cache_dir, target_labels, threshold)
        ]

    def extract_sensitive_data(self, chunk: Dict[int, str]) -> Set[int]:
    
        mapper = ChunkMapper(chunk)
        total_idx: Set[int] = set()

        for extractor in self.extractors:
            coords = extractor.extract(mapper.text)

            for start, end in coords:
                total_idx.update(mapper.get_original_idxs(start, end))

        return total_idx