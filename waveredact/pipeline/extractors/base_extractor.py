from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> List[Tuple[int, int, float]]:
        """
        Extract coordinates corresponding to the position of sensitive data

        Params:
        text    - str text of the current chunk
        old_idx - list of the previous extracted indices. Used to check if the previous step made some errors
        
        Return:
        list of coordinates and confidence score: [(start, end, score)]
        """
        pass