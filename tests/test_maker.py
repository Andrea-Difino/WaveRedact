import json
from models.gguf_model import GGUFModel
import yaml
from services.llama_server import LlamaServerService

with open("./tests/golden_dataset.json", mode="r") as f:
    dataset = json.load(f)

MAKER_MODEL_NAME = "Meta-Llama-3-8B-Instruct-Q5_K_S.gguf"
SERVER_PORT = 8080

with open("prompts.yaml", "r") as f:
    prompts = yaml.safe_load(f)

maker = GGUFModel(prompts["maker"]["default"]["system_prompt"], MAKER_MODEL_NAME, server_port=SERVER_PORT)

server = LlamaServerService(MAKER_MODEL_NAME, server_port=SERVER_PORT)
server.start_server()

for phrase in dataset:
    text: str = phrase["text"]
    iw_pair = {i:w for i,w in enumerate(text.split(" "))}
    maker.run_model(iw_pair)