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
            "email": r'(?i)\b[a-z0-9._%+-]+(?:\s*(?:@|chiocciola|\bat\b)\s*[a-z0-9.-]+?|[-_]?(?:gmail|yahoo|hotmail|outlook|libero|virgilio|icloud|alice|pec))\s*(?:\.|punto|\bdot\b)\s*(?:com|it|net|org|eu|gov|edu|info|io|co|me)\b',
            "iban": r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b',
            "card_number": r'\b(?:\d[ -]*?){13,16}\b',
            "payment_card": r'\b(?:\d[ -]*?){13,16}\b',
            "phone_number": r'(?<!\w)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){1,3}\d{4,6}(?!\w)',
            "ip_address": r'(?i)\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:\.|\s*punto\s*|\s*dot\s*)){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
            "tax_id": r'(?i)\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b', 
            "national_id_number": r'(?i)\b\d{3}(?:-|\s*trattino\s*|\s*dash\s*|\s+)\d{2}(?:-|\s*trattino\s*|\s*dash\s*|\s+)\d{4}\b',
            "sensitive_date": r'(?i)\b(?:0?[1-9]|[12][0-9]|3[01])(?:[-/:]|\s*slash\s*|\s*barra\s*|\s*trattino\s*|\s*dash\s*|\s+)(?:0?[1-9]|1[012])(?:[-/:]|\s*slash\s*|\s*barra\s*|\s*trattino\s*|\s*dash\s*|\s+)(?:\d{4}|\d{2})\b|\b(?:\d{4})(?:[-/:]|\s*slash\s*|\s*barra\s*|\s*trattino\s*|\s*dash\s*|\s+)(?:0?[1-9]|1[012])(?:[-/:]|\s*slash\s*|\s*barra\s*|\s*trattino\s*|\s*dash\s*|\s+)(?:0?[1-9]|[12][0-9]|3[01])\b',
        }
        
        self.patterns: list[tuple[re.Pattern, str]] = []
        if target_labels:
            for label in target_labels:
                lower_label = label.lower()
                if lower_label in pattern_mapping:
                    self.patterns.append((re.compile(pattern_mapping[lower_label]), label))
            
    def extract(self, text: str) -> list[tuple[int, int, float, str]]:
        results = []
        for pattern, label in self.patterns:
            for match in pattern.finditer(text):  
                results.append((match.start(), match.end(), 1.0, label))
   
        return results