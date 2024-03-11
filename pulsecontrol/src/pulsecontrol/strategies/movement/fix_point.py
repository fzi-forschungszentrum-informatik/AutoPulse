from dataclasses import dataclass

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.movement import MovementStrategy


@dataclass(kw_only=True)
class FixPoint(MovementStrategy):
    def is_injection_location(self) -> bool:
        return True

    def reset(self):
        pass

    position: Point2D

    def __next__(self) -> Point2D:
        return self.position
