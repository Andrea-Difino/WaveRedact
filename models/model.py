from abc import abstractmethod, ABC

class Model(ABC):

    @abstractmethod
    def run_model(self, chunk: list[str], idx_word_pairs: dict) -> list[int]:
        ...