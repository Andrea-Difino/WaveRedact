import json
from models.model import Model
from huggingface_hub import hf_hub_download
import os
from openai import OpenAI
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(datefmt=FORMAT,level=logging.INFO, force=True)

class GGUFModel(Model):
    def __init__(self, sys_prompt: str, gguf_file_name: str, repo_id: str ,model_dir: str = "./files/gguf_models", server_port: int = 8080):
        self.file_gguf = gguf_file_name
        self.model_dir = os.path.abspath(model_dir)
        self.path = f"{self.model_dir}/{self.file_gguf}"
        self.repo_id = repo_id

        self.sys_prompt = sys_prompt
        self.check_existance()

        self.client = OpenAI(
            base_url=f"http://localhost:{server_port}/v1", 
            api_key="locale"
        )

    def check_existance(self) -> None:
        if not os.path.exists(self.path):
            print("Model not finded. Download... (it could take some minutes)...")

            download = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.file_gguf,  
                local_dir=self.model_dir,  
                token=os.environ["HF_TOKEN"]             
            )
            print("Download completed!")
        else:
            print("Model already downloaded")

    def run_model(self, chunk: dict[int,str]) -> dict:
        system_prompt = self.sys_prompt
        
        prompt = ""
        for pair in chunk.items():
            prompt += f"[{pair[0]}] {pair[1]}\n"
        
        try:
            response = self.client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Testo da analizzare: '{prompt}'"}
                ],
                temperature=0.0, 
                response_format={"type": "json_object"} 
            )
            
            risposta_testo = response.choices[0].message.content

            list_sensitive_ids = json.loads(risposta_testo if risposta_testo else "")
            return list_sensitive_ids

        except Exception as e:
            print(f"Errore during LLM inference: {e}")
            return {}