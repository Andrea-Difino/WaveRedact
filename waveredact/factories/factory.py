from abc import ABC
from typing import Any


class Factory(ABC):
    """
        Factory interface for the creation of the models
    """

    def build(self) -> Any:
        ...