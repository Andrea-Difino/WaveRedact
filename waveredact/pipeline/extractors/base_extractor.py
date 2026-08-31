from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """
    Abstract base class for all sensitive data extractors.
    """
    @abstractmethod
    def extract(self, text: str) -> list[tuple[int, int, float, str]]:
        """
        Extract coordinates corresponding to the position of sensitive data

        Params:
        text    - str text of the current chunk
        
        Return:
        list of coordinates, confidence score, and entity type label: [(start, end, score, label)]
        """
        pass