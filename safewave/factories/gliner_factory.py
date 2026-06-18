from pathlib import Path
from safewave.pipeline.extractors.gliner_extractor import GlinerExtractor

class GlinerFactory:

    def __init__(self, model_id: str = "urchade/gliner_medium-v2.1", cache_dir: str | None = None, target_labels: list[str] | None = None, threshold: float = 0.47):
        self.model_id = model_id
        self.threshold = threshold

        if not cache_dir:
            project_root = Path(__file__).resolve().parent.parent.parent

            safe_cache_dir = project_root / "files" / "gliner_models"

            self.cache_dir = str(safe_cache_dir)
        else:
            self.cache_dir = cache_dir

        self.target_labels = target_labels if target_labels else [
            "person", "first name", "last name", "password",
            "street address", "city", "state", "hospital",
            "bank account number", "email"
        ]

    def build(self) -> GlinerExtractor:
        return GlinerExtractor(
            self.model_id,
            self.cache_dir,
            self.target_labels,
            self.threshold
        )