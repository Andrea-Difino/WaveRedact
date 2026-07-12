import json
import re
from typing import Dict
from waveredact.models.model import Model
from huggingface_hub import hf_hub_download
import os
from openai import OpenAI
from dotenv import load_dotenv
import logging
import yaml
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(datefmt=FORMAT, level=logging.WARNING, force=True)

class GGUFModel(Model):
    """
    Implementation of the Model interface for GGUF-based local LLMs.

    Attributes:
        model_dir       - Path to the directory where the model is stored
        file_gguf       - Filename of the GGUF model
        path            - Complete path to the model file
        repo_id         - HuggingFace repository ID for the model
        target_labels   - List of sensitive labels to extract
        sys_prompt      - System prompt for the LLM
        user_prompt     - User prompt template for the LLM
        client          - OpenAI API client instance connected to the local server
    """
    def __init__(self, gguf_file_name: str, repo_id: str, model_dir: str | None = None, server_port: int = 8080):
        project_root = Path(__file__).resolve().parent.parent.parent
        self.model_dir = model_dir if model_dir else str(project_root / "files" / "gguf_models")
        
        self.file_gguf = gguf_file_name
        self.path = f"{self.model_dir}/{self.file_gguf}"
        self.repo_id = repo_id
        self.target_labels: list[str] | None = None

        prompts_path = project_root / "prompts.yaml"
        with open(prompts_path, "r") as f:
            prompts = yaml.safe_load(f)

        self.sys_prompt = prompts["maker"]["default"]["system_prompt"]
        self.user_prompt = prompts["maker"]["default"]["user_prompt"]
        self._check_existance()

        self.client = OpenAI(
            base_url=f"http://localhost:{server_port}/v1", 
            api_key="local"
        )
    
    @property
    def labels(self) -> list[str]:
        return self.target_labels if self.target_labels else []

    @labels.setter
    def labels(self, labels: list[str]):
        self.target_labels = labels

    def _check_existance(self) -> None:
        if not os.path.exists(self.path):
            print("Model not found. Download... (it could take some minutes)...")

            _ = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.file_gguf,  
                local_dir=self.model_dir,  
                token=os.environ.get("HF_TOKEN")             
            )
            print("Download completed!")
        else:
            print("Model already downloaded")

    def _parse_llm_response(self, text_response: str) -> Dict | None:
        """
        Transform the model response in a correct JSON object

        Params:
            text_response   - response of the LLM
        """
        if not text_response:
            return None

        json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse cleaned JSON: {e}")
                return None
        return None

    def _extract_ids_with_healing(self, parsed_data: Dict, chunk: Dict[int, str]) -> list[int]:
        """
        Extract sensitive IDs and check possible hallucinations of the model
        
        Params:
            parsed_data     - JSON object with the model output
            chunk           - dict with the right correspondece of id-word
        """
        list_sensitive_ids = []

        if "word_analysis" not in parsed_data:
            logger.error("The output JSON doesn't have 'word_analysis' array. Returning empty list")
            return []

        for analysis in parsed_data["word_analysis"]:
            if analysis.get("action") == "SENSITIVE":
                reported_id = analysis.get("id")
                reported_word = analysis.get("word")
                
                if reported_id is not None and reported_word is not None:
                    if reported_id in chunk and reported_word in chunk[reported_id]:
                        list_sensitive_ids.append(reported_id)
                        
                    else:
                        logger.warning(f"LLM hallucinated ID {reported_id} for word '{reported_word}'. Attempting recovery...")
                        for real_id, real_word in chunk.items():
                            if reported_word in real_word:
                                list_sensitive_ids.append(real_id)
                                print("ID recovered")
                                break
        
        return list_sensitive_ids

    def run_model(self, chunk: Dict[int, str], ambiguous_idx: list[int] | None) -> list[int]:
        print("[STEP 3] Using LLM")
        
        couple_str = "".join([f"[{k}] {v}\n" for k, v in chunk.items()])
        user_prompt = self.user_prompt.format(labels=self.labels, ambiguous=ambiguous_idx, idx_couples=couple_str)
        
        try:
            response = self.client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "system", "content": self.sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0, 
                response_format={"type": "json_object"} 
            )
            
            text_response = response.choices[0].message.content
            
            if text_response:
                parsed_data = self._parse_llm_response(text_response)
                if parsed_data:
                    return self._extract_ids_with_healing(parsed_data, chunk)
                else:
                    logger.warning("No valid JSON structure found in the LLM response.")
                    return []
            else:
                return []

        except Exception as e:
            logger.warning(f"Error during LLM inference: {e}")
            return []