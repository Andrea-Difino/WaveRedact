import json
from models.model import Model
from huggingface_hub import hf_hub_download
import os
import subprocess
import time
import urllib.request
import zipfile
import requests
import atexit
from openai import OpenAI

class Llama8B(Model):
    def __init__(self, sys_prompt: str):
        self.file_gguf = "Meta-Llama-3.1-8B-Instruct-Q5_K_S.gguf"
        self.model_dir = "./files/gguf_models"
        self.path = f"{self.model_dir}/{self.file_gguf}"

        self.server_dir = "./files/server"
        self.server_exe = os.path.join(self.server_dir, "llama-server.exe")

        self.sys_prompt = sys_prompt
        self.process = None
        self.check_existance()

    def check_existance(self) -> None:
        if not os.path.exists(self.path):
            print("Model not finded. Download... (it could take some minutes)...")

            download = hf_hub_download(
                repo_id="bartowski/Meta-Llama-3-8B-Instruct-GGUF", 
                filename=self.file_gguf,                          
                local_dir="./files/gguf_models/",                    
            )
            print("✅ Download completato con successo!")
        else:
            print("✅ Modello già presente sul PC.")

    def run_model(self, chunk: dict[int,str]) -> dict:
        system_prompt = self.sys_prompt
        
        prompt = ""
        for pair in chunk.items():
            prompt += f"[{pair[0]}] {pair[1]}\n"
        
        try:
            response = self.client.chat.completions.create(
                model="local-model", # Il nome non importa con llama.cpp
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Testo da analizzare: '{prompt}'"}
                ],
                temperature=0.0, 
                response_format={"type": "json_object"} 
            )
            
            risposta_testo = response.choices[0].message.content

            lista_censure = json.loads(risposta_testo)
            return lista_censure

        except Exception as e:
            print(f"Errore durante l'interrogazione dell'LLM: {e}")
            return []