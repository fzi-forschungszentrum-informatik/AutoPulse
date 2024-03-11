from dataclasses import dataclass

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.movement import MovementStrategy


@dataclass(kw_only=True)
class HomingMode(MovementStrategy):
    target_position: Point2D
    _home: bool = False

    def reset(self):
        self._home = False

    def is_injection_location(self) -> bool:
        # at location if the next operation is a home
        return self._home

    def __next__(self) -> Point2D:
        if self._home:
            self._home = False
            return Point2D(0, self.target_position.y)
        self._home = True
        return self.target_position
