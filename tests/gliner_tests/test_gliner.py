import json
import logging
import re
from gliner import GLiNER

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO, force=True)


def convert_char_to_idx(text: str, char_start: int, char_end: int) -> list[int]:
    """Convert chars positions into idxs in the words array"""
    parole = text.split(" ")
    words_idx = []
    curr_char = 0

    for word_idx, word in enumerate(parole):
        word_start = curr_char
        word_end = curr_char + len(word)

        if char_start < word_end and char_end > word_start:
            words_idx.append(word_idx)

        curr_char += len(word) + 1

    return words_idx


def remove_data_with_regex(text) -> set[int]:
    finded_idx = set()

    pattern_email = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    pattern_iban = r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"
    pattern_carte = r"\b(?:\d[ -]*?){13,16}\b"
    pattern_tel = (
        r"(?<!\w)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){1,3}\d{4,6}(?!\w)"
    )
    pattern_cap = r"\b\d{5}\b"

    regex_totale = f"({pattern_email})|({pattern_iban})|({pattern_carte})|({pattern_tel})|({pattern_cap})"

    for match in re.finditer(regex_totale, text):
        indici = convert_char_to_idx(text, match.start(), match.end())
        finded_idx.update(indici)

    return finded_idx


def main():

    with open("./tests/golden_dataset.json", mode="r") as f:
        dataset = json.load(f)

    logger.info("Avvio Motore Ibrido... Caricamento GLiNER...")
    model = GLiNER.from_pretrained(
        "urchade/gliner_medium-v2.1", cache_dir="./files/gliner_models"
    )

    labels = [
        "person",
        "first name",
        "last name",
        "password",
        "street address",
        "city",
        "state",
        "hospital",
        "bank account number",
    ]
    punteggio = 0
    json_len = len(dataset)

    totale_TP = 0
    totale_FP = 0
    totale_FN = 0

    for i, phrase in enumerate(dataset):
        logger.info(f"--- Frase {i + 1}/{json_len} ---")
        text: str = phrase["text"]
        indici_corretti_reali = phrase["target_indices"]

        total_idx = set()

        regex_idx = remove_data_with_regex(text)
        total_idx.update(regex_idx)

        entities = model.predict_entities(text, labels, threshold=0.47)
        for entity in entities:
            gliner_idx = convert_char_to_idx(
                text, entity["start"], entity["end"]
            )
            total_idx.update(gliner_idx)

        lista_finale = sorted(list(total_idx))

        set_reale = set(indici_corretti_reali)
        set_predetto = set(lista_finale)

        tp = len(set_reale.intersection(set_predetto))

        fp = len(set_predetto - set_reale)

        fn = len(set_reale - set_predetto)

        totale_TP += tp
        totale_FP += fp
        totale_FN += fn

        print(f"--- Frase {i + 1}/{json_len} ---")
        print(f"  RISULTATO PIPELINE : {lista_finale}")
        print(f"  GOLDEN DATASET     : {indici_corretti_reali}")

        if lista_finale == indici_corretti_reali:
            print("  ✅ EXACT MATCH!")
            punteggio += 1
        else:
            print(f"  ⚠️ DIFFERENZE -> Extra (FP): {fp} | Mancanti (FN): {fn}")

        print("=" * 40)

    precision = (
        totale_TP / (totale_TP + totale_FP) if (totale_TP + totale_FP) > 0 else 0
    )
    recall = totale_TP / (totale_TP + totale_FN) if (totale_TP + totale_FN) > 0 else 0
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    print("\n")
    print("📊 REPORT FINALE DEL MOTORE IBRIDO (WORD-LEVEL)\n\n")

    print(
        f"  • Frasi perfette al 100%:  {punteggio} / {json_len} ({(punteggio / json_len) * 100:.1f}%)"
    )
    print(f"  • Veri Positivi (TP):      {totale_TP} parole")
    print(f"  • Falsi Positivi (FP):     {totale_FP} parole censurate di troppo")
    print(f"  • Falsi Negativi (FN):     {totale_FN} dati sensibili persi")
    print("-" * 50)
    print(f"  🎯 PRECISION: {precision * 100:.2f}%")
    print(f"  🛡️ RECALL:    {recall * 100:.2f}%")
    print(f"  🏆 F1-SCORE:  {f1_score * 100:.2f}%")


if __name__ == "__main__":
    main()
