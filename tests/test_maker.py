import json
from models.llama8B import Llama8B

with open("golden_dataset.json", mode="r") as f:
    dataset = json.load(f)

print(dataset)