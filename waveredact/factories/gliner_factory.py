from pathlib import Path
from gliner2 import GLiNER2
from huggingface_hub import snapshot_download
import logging
import os
from contextlib import redirect_stdout
import json

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(datefmt=FORMAT, level=logging.WARNING, force=True)

class GlinerFactory:
    def __init__(
        self,
        model_id: str = "fastino/gliner2-privacy-filter-PII-multi",
        cache_dir: str = "",
        target_labels: list[str] | None = None,
        threshold: float = 0.54,
    ):
        self.model_id = model_id
        self.threshold = threshold

        if not cache_dir:
            project_root = Path(__file__).resolve().parent.parent.parent
            safe_cache_dir = project_root / "files" / "gliner_models" / "gliner2"
            self.cache_dir = str(safe_cache_dir)
        else:
            self.cache_dir = cache_dir

        self.target_labels = (
            target_labels
            if target_labels
            else [
                "person",
                "first_name",
                "last_name",
                "password",
                "street_address",
                "city",
                "state_or_region",
                "bank_account",
                "account_number",
                "email",
            ]
        )

    def build(self) -> GLiNER2:
        if not (os.path.exists(self.cache_dir) and os.listdir(self.cache_dir)):
            print(f"\n🌐 Model not found locally. Downloading '{self.model_id}'... (Could take some minutes)")
            os.makedirs(self.cache_dir, exist_ok=True)
            
            snapshot_download(repo_id=self.model_id, local_dir=self.cache_dir)
            print(f"\n✅ Model downloaded successfully and saved in '{self.cache_dir}'!")
        else:
            logger.info(f"\n📦 Found model '{self.cache_dir}'. Offline loading...")

        tok_config_path = Path(self.cache_dir) / "tokenizer_config.json"
        if tok_config_path.exists():
            try:
                with open(tok_config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                if "extra_special_tokens" in config and isinstance(config["extra_special_tokens"], list):
                    del config["extra_special_tokens"]

                    with open(tok_config_path, "w", encoding="utf-8") as fw:
                        json.dump(config, fw, indent=2)
            except Exception as e:
                logger.warning(f"Impossibile correggere il tokenizer config: {e}")

        with open(os.devnull, 'w', encoding="utf-8") as devnull, redirect_stdout(devnull):
            model = GLiNER2.from_pretrained(self.cache_dir, local_files_only=True)

        return model
