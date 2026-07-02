import json
from waveredact.models.model import Model
from huggingface_hub import hf_hub_download
import os
from openai import OpenAI
from dotenv import load_dotenv
import logging
import yaml

load_dotenv()
logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(datefmt=FORMAT,level=logging.WARNING, force=True)

class GGUFModel(Model):
    def __init__(self, gguf_file_name: str, repo_id: str ,model_dir: str = "./files/gguf_models", server_port: int = 8080):
        self.file_gguf = gguf_file_name
        self.model_dir = os.path.abspath(model_dir)
        self.path = f"{self.model_dir}/{self.file_gguf}"
        self.repo_id = repo_id
        self.target_labels: list[str] | None = None

        with open("prompts.yaml", "r") as f:
            prompts = yaml.safe_load(f)

        self.sys_prompt = prompts["maker"]["default"]["system_prompt"]
        self.user_prompt = prompts["maker"]["default"]["user_prompt"]
        self.check_existance()

        self.client = OpenAI(
            base_url=f"http://localhost:{server_port}/v1", 
            api_key="locale"
        )
    
    @property
    def labels(self) -> list[str]:
        return self.target_labels if self.target_labels else []

    @labels.setter
    def labels(self, labels: list[str]):
        self.target_labels = labels

    def check_existance(self) -> None:
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

    def run_model(self, chunk: dict[int,str], ambiguous_idx: list[int] | None) -> list[int]:
        system_prompt = self.sys_prompt
        
        couple = ""
        for pair in chunk.items():
            couple += f"[{pair[0]}] {pair[1]}\n"

        user_prompt = self.user_prompt.format(labels=self.labels, ambiguous=ambiguous_idx, idx_couples=couple)
        
        try:
            response = self.client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Testo da analizzare: '{user_prompt}'"}
                ],
                temperature=0.0, 
                response_format={"type": "json_object"} 
            )
            
            risposta_testo = response.choices[0].message.content

            list_sensitive_ids: list[int] = json.loads(risposta_testo if risposta_testo else "")["final_indices"]
            return list_sensitive_ids

        except Exception as e:
            logger.warning(f"Error during LLM inference: {e}")
            return []