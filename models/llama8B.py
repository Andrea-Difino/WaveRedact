from openai import OpenAI
import json
from models.model import Model

class Llama8B(Model):
    def __init__(self, sys_prompt: str):
        self.client = OpenAI(
            base_url="http://localhost:8080/v1", 
            api_key="sk-no-key-required" 
        )
        self.sys_prompt = sys_prompt

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