from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies import Strategy


@dataclass(kw_only=True)
class MovementStrategy(Iterator[Point2D], Strategy, ABC):
    strategy: str = "movement"

    # estimate of the number of movements performed with the given configuration
    total_movements: int | None = None

    @abstractmethod
    def is_injection_location(self) -> bool:
        raise NotImplementedError()


class MovementError(Exception): ...
