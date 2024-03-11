from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(kw_only=True)
class Strategy(ABC):
    strategy: str

    @abstractmethod
    def reset(self):
        pass
