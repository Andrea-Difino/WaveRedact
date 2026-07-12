from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseExtractor(ABC):
    """
    Abstract base class for all sensitive data extractors.
    """
    @abstractmethod
    def extract(self, text: str) -> List[Tuple[int, int, float]]:
        """
        Extract coordinates corresponding to the position of sensitive data

        Params:
        text    - str text of the current chunk
        
        Return:
        list of coordinates and confidence score: [(start, end, score)]
        """
        pass