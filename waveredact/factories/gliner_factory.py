from pathlib import Path
from gliner2 import GLiNER2
import sys
from huggingface_hub import snapshot_download
import logging
import os
from contextlib import redirect_stdout
import json

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(datefmt=FORMAT, level=logging.WARNING, force=True)

class GlinerFactory:
    """
    Factory class responsible for downloading and instantiating the GLiNER2 model.

    Attributes:
        model_id        - HuggingFace model ID for GLiNER
        threshold       - Confidence threshold for entity extraction
        cache_dir       - Directory path where the model is downloaded and cached
        target_labels   - List of default entity labels to extract
    """
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
            from waveredact.utils.path_utils import get_app_data_dir
            safe_cache_dir = get_app_data_dir() / "files" / "gliner_models" / "gliner2"
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
        """
        Download (if necessary), configure, and instantiate the GLiNER2 model.

        Return:
            GLiNER2 object ready for inference
        """
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
                logger.warning(f"Impossible to correct the tokenizer config: {e}")
                sys.exit(1)

        with open(os.devnull, 'w', encoding="utf-8") as devnull, redirect_stdout(devnull):
            model = GLiNER2.from_pretrained(self.cache_dir, local_files_only=True)

        return model
