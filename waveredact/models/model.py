from abc import abstractmethod, ABC

class Model(ABC):
    
    @abstractmethod
    def run_model(self, chunk: dict[int,str], ambiguous_idx: list[int] | None) -> list[int]:
        ...