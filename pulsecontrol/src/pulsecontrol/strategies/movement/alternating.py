from dataclasses import dataclass

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.movement import MovementStrategy


@dataclass(kw_only=True)
class Alternating(MovementStrategy):
    reset_position: Point2D
    target_position: Point2D

    at_target: bool = True

    def reset(self):
        """
        Does not need resets
        """
        pass

    def is_injection_location(self) -> bool:
        return self.at_target

    def __next__(self) -> Point2D:
        if self.at_target:
            self.at_target = False
            return self.reset_position
        self.at_target = True
        return self.target_position
