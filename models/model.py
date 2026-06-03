from abc import abstractmethod, ABC

class Model(ABC):

    @abstractmethod
    def run_model(self, chunk: str):
        ...