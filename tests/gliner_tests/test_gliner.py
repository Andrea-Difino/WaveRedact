import json
import logging
import re
from gliner import GLiNER
import numpy as np

# --- SETUP LOGGING ---
logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO, force=True)

# --- FUNZIONE DI CONVERSIONE (Cuore del sistema) ---
def converti_caratteri_in_indici(testo: str, char_start: int, char_end: int) -> list[int]:
    """Converte le posizioni (caratteri) negli indici dell'array di parole."""
    parole = testo.split(" ")
    indici_parole = []
    carattere_corrente = 0

    for indice_parola, parola in enumerate(parole):
        inizio_parola = carattere_corrente
        fine_parola = carattere_corrente + len(parola)
        
        # Se l'entità copre in parte o del tutto questa parola, salviamo l'indice
        if char_start < fine_parola and char_end > inizio_parola:
            indici_parole.append(indice_parola)
            
        carattere_corrente += len(parola) + 1 
        
    return indici_parole

# --- MOTORE 1: REGEX (Per i dati standardizzati) ---
def estrai_con_regex(testo: str) -> set:
    indici_trovati = set()
    
    # Definiamo i pattern blindati
    pattern_email = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    pattern_iban = r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b'
    pattern_carte = r'\b(?:\d[ -]*?){13,16}\b'
    pattern_tel = r'(?<!\w)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){1,3}\d{4,6}(?!\w)'
    pattern_cap = r'\b\d{5}\b'
    
    # Uniamo tutte le regex
    regex_totale = f"({pattern_email})|({pattern_iban})|({pattern_carte})|({pattern_tel})|({pattern_cap})"
    
    for match in re.finditer(regex_totale, testo):
        # Troviamo le coordinate e le convertiamo
        indici = converti_caratteri_in_indici(testo, match.start(), match.end())
        indici_trovati.update(indici)
        
    return indici_trovati

# --- ESECUZIONE PRINCIPALE ---
def main():
    # 1. Carica il Golden Dataset
    with open("./tests/golden_dataset.json", mode="r") as f:
        dataset = json.load(f)

    # 2. Inizializza Motore 2: GLiNER (Per i contesti complessi)
    logger.info("Avvio Motore Ibrido... Caricamento GLiNER...")
    model = GLiNER.from_pretrained(
        "urchade/gliner_medium-v2.1", 
        cache_dir="./files/gliner_models"
    )

    labels = [
        "person", "first name", "last name", 
        "password", 
        "street address", "city", "state", "hospital",
        "bank account number"
    ]
    punteggio = 0
    json_len = len(dataset)

    totale_TP = 0  
    totale_FP = 0  
    totale_FN = 0 

    # 3. Analisi Frase per Frase
    for i, phrase in enumerate(dataset):
        logger.info(f"--- Frase {i+1}/{json_len} ---")
        text: str = phrase["text"]
        indici_corretti_reali = phrase["target_indices"]
        
        indici_totali = set()

        indici_regex = estrai_con_regex(text)
        indici_totali.update(indici_regex)

        entities = model.predict_entities(text, labels, threshold=0.47)
        for entity in entities:
            indici_gliner = converti_caratteri_in_indici(text, entity["start"], entity["end"])
            indici_totali.update(indici_gliner)

        lista_finale = sorted(list(indici_totali))

        set_reale = set(indici_corretti_reali)
        set_predetto = set(lista_finale)

        tp = len(set_reale.intersection(set_predetto))

        fp = len(set_predetto - set_reale)

        fn = len(set_reale - set_predetto)

        totale_TP += tp
        totale_FP += fp
        totale_FN += fn
        
        print(f"--- Frase {i+1}/{json_len} ---")
        print(f"  RISULTATO PIPELINE : {lista_finale}")
        print(f"  GOLDEN DATASET     : {indici_corretti_reali}")

        if lista_finale == indici_corretti_reali:
            print("  ✅ EXACT MATCH!")
            punteggio += 1
        else:
            print(f"  ⚠️ DIFFERENZE -> Extra (FP): {fp} | Mancanti (FN): {fn}")
            
        print("=" * 40)

    # --- CALCOLO METRICHE FINALI ---
    precision = totale_TP / (totale_TP + totale_FP) if (totale_TP + totale_FP) > 0 else 0
    recall = totale_TP / (totale_TP + totale_FN) if (totale_TP + totale_FN) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print("\n")
    print("📊 REPORT FINALE DEL MOTORE IBRIDO (WORD-LEVEL)\n\n")

    print(f"  • Frasi perfette al 100%:  {punteggio} / {json_len} ({(punteggio/json_len)*100:.1f}%)")
    print(f"  • Veri Positivi (TP):      {totale_TP} parole")
    print(f"  • Falsi Positivi (FP):     {totale_FP} parole censurate di troppo")
    print(f"  • Falsi Negativi (FN):     {totale_FN} dati sensibili persi")
    print("-" * 50)
    print(f"  🎯 PRECISION: {precision * 100:.2f}%")
    print(f"  🛡️ RECALL:    {recall * 100:.2f}%")
    print(f"  🏆 F1-SCORE:  {f1_score * 100:.2f}%")

if __name__ == "__main__":
    main()