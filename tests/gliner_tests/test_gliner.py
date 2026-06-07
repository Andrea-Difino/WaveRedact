import json
import logging
from gliner import GLiNER

logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(datefmt=FORMAT,level=logging.INFO, force=True)

with open("./tests/golden_dataset.json", mode="r") as f:
    dataset = json.load(f)


model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1", cache_dir="./files/gliner_models")

labels = [
    "full name", 
    "password", 
    "email address", 
    "physical address", 
    "phone number", 
    "IBAN", 
    "credit card number"
]

json_len = len(dataset)
for i,phrase in enumerate(dataset):
    logger.info(f"Running phrase {i+1}/{json_len}")
    text: str = phrase["text"]
    entities = model.predict_entities(text, labels, threshold=0.5)
    for entity in entities:
        print("[", entity["start"], entity["end"],"]",entity["text"], "=>", entity["label"], "| Accuracy:", entity["score"])

    