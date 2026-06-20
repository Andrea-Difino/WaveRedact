import re
from .base_extractor import BaseExtractor
from typing import List, Tuple

class RegexExtractor(BaseExtractor):
    def __init__(self):
        pattern_email = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        pattern_iban = r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b'
        pattern_carte = r'\b(?:\d[ -]*?){13,16}\b'
        pattern_tel = r'(?<!\w)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){1,3}\d{4,6}(?!\w)'
        pattern_cap = r'\b\d{5}\b'
        self.regex_totale = f"({pattern_email})|({pattern_iban})|({pattern_carte})|({pattern_tel})|({pattern_cap})"

    def extract(self, text: str) -> List[Tuple[int, int]]:
        return [(match.start(), match.end()) for match in re.finditer(self.regex_totale, text)]