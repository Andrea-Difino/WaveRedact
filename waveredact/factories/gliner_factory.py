from pathlib import Path
from waveredact.pipeline.extractors.gliner_extractor import GlinerExtractor

class GlinerFactory:

    def __init__(self, model_id: str = "fastino/gliner2-privacy-filter-PII-multi", cache_dir: str | None = None, target_labels: list[str] | None = None, threshold: float = 0.54):
        self.model_id = model_id
        self.threshold = threshold

        if not cache_dir:
            project_root = Path(__file__).resolve().parent.parent.parent
            safe_cache_dir = project_root / "files" / "gliner_models" / "gliner2"
            self.cache_dir = str(safe_cache_dir)
        else:
            self.cache_dir = cache_dir

        self.target_labels = target_labels if target_labels else [
            "person", "first_name", "last_name", "password",
            "street_address", "city", "state_or_region",
            "bank_account", "account_number", "email"
        ]

    def build(self) -> GlinerExtractor:
        return GlinerExtractor(
            self.model_id,
            self.cache_dir,
            self.target_labels,
            self.threshold
        )