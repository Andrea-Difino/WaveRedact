import json
from safewave.models.gguf_model import GGUFModel
import yaml
from safewave.services.llama_server import LlamaServerService
import pandas as pd
import logging
from safewave.utils.chunk import Chunker

logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(datefmt=FORMAT,level=logging.INFO, force=True)


with open("./tests/golden_dataset.json", mode="r") as f:
    dataset = json.load(f)

MAKER_MODEL_NAME = "Qwen2.5-14B-Instruct-Q5_K_S.gguf"
REPO_ID = "bartowski/Qwen2.5-14B-Instruct-GGUF"
SERVER_PORT = 8080

with open("prompts.yaml", "r") as f:
    prompts = yaml.safe_load(f)

maker = GGUFModel(prompts["maker"]["default"]["system_prompt3"], MAKER_MODEL_NAME, REPO_ID, server_port=SERVER_PORT)

server = LlamaServerService(MAKER_MODEL_NAME, server_port=SERVER_PORT)
server.start_server()

chunker = Chunker(20,50)

list_sensitive_ids_test = []
list_sensitive_ids_real = []

json_len = len(dataset)
for i,phrase in enumerate(dataset):
    logger.info(f"Running phrase {i+1}/{json_len}")
    text: str = phrase["text"]
    list_sensitive_ids_real.append(phrase["target_indices"])
    iw_pair = {i:w for i,w in enumerate(text.split(" "))}
    one_chunk_ids = set()
    for j,chunk in enumerate(chunker.chunk_text(iw_pair)):
        print("chunk:",j+1)
        one_chunk_ids.update(maker.run_model(chunk)["redact_ids"])
    list_sensitive_ids_test.append(list(one_chunk_ids))
    one_chunk_ids.clear()

comparison = pd.DataFrame({"test_ids": list_sensitive_ids_test, "real_ids": list_sensitive_ids_real})
comparison.to_csv("test_result.csv")

# RESULTS
# Meta-Llama-3-8B-Instruct-Q5_K_S.gguf : sys1 - 26/40, sys2 - 25/40 , sys2-chunk - 26/40
# Qwen2.5-14B-Instruct-Q5_K_S.gguf : sys1 - 20/40, sys2 - 30/40, sys2-chunk - 29/40
