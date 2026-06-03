from transformers import pipeline
from .model import Model

class OpenaiPrivacyFilter(Model):

    def __init__(self):
        ...

    def run_model(self, chunk: str):
        privacy_filter = pipeline(
            task="token-classification",
            model="openai/privacy-filter",
            aggregation_strategy="simple",
            device="cuda",
            trust_remote_code=True
        )

        print("Analisi testo...")
        results = privacy_filter(chunk)

        for entity in results:
            parola = entity['word']
            categoria = entity['entity_group']
            score = entity['score']
            # start e end indicano il carattere esatto nella stringa
            inizio = entity['start']
            fine = entity['end']
            
            print(f"Trovato: '{parola}' | Categoria: {categoria} | Posizione: {inizio}-{fine} | Affidabilità: {score:.2f}")