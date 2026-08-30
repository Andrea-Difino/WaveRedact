import re

from .base_extractor import BaseExtractor


class RegexExtractor(BaseExtractor):
    """
    Extract sensitive information using predefined regular expressions.

    Attributes:
        total_regex    - Combined regular expression pattern for multiple data types
    """
    def __init__(self, target_labels: list[str] | None = None):
        pattern_mapping = {
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "iban": r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b',
            "card_number": r'\b(?:\d[ -]*?){13,16}\b',
            "payment_card": r'\b(?:\d[ -]*?){13,16}\b',
            "phone_number": r'(?<!\w)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){1,3}\d{4,6}(?!\w)',
        }
        
        selected_patterns = []
        if target_labels:
            for label in target_labels:
                if label in pattern_mapping and pattern_mapping[label] not in selected_patterns:
                    selected_patterns.append(pattern_mapping[label])
            
        if selected_patterns:
            self.total_regex = "|".join([f"({p})" for p in selected_patterns])
        else:
            self.total_regex = r'(?!x)x'
            
    def extract(self, text: str) -> list[tuple[int, int, float]]:
        return [(match.start(), match.end(), 1.0) for match in re.finditer(self.total_regex, text)]