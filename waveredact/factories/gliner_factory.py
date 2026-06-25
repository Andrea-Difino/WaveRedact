from pathlib import Path
from gliner2 import GLiNER2
import os

class GlinerFactory:

    def __init__(self, model_id: str = "fastino/gliner2-privacy-filter-PII-multi", cache_dir: str = "", target_labels: list[str] | None = None, threshold: float = 0.54):
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

    def build(self) -> GLiNER2:
        if os.path.exists(self.cache_dir) and os.listdir(self.cache_dir):
            print(f"📦 [WaveRedact] Finded model '{self.cache_dir}'. Offline loading...")

            model = GLiNER2.from_pretrained(self.cache_dir, local_files_only=True)
        else:
            print(f"🌐 [WaveRedact] Model not finded locally. Downloading '{self.model_id}'... (Could take some minutes)")

            os.makedirs(self.cache_dir, exist_ok=True)

            model = GLiNER2.from_pretrained(self.model_id)
            model.save_pretrained(self.cache_dir)
            print(f"✅ [WaveRedact] Modello scaricato con successo e salvato in '{self.cache_dir}'!")

        return model