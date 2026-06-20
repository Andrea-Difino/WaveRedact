from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> List[Tuple[int, int]]:
        """Every extractor must return a list of coordinates: [(start, end)]"""
        pass