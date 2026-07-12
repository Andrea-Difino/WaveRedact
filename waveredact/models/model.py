from abc import abstractmethod, ABC

class Model(ABC):
    """
    Abstract base class for all language models used for extraction.
    """
    

    @abstractmethod
    def run_model(self, chunk: dict[int,str], ambiguous_idx: list[int] | None) -> list[int]:
        """
        Execute the model on a given text chunk to identify sensitive indices.

        Params:
            chunk           - Dictionary mapping indices to words
            ambiguous_idx   - List of indices that the primary extractor was unsure about

        Return:
            List of integers corresponding to the sensitive indices
        """
        ...