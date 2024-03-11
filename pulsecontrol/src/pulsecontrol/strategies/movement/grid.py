from dataclasses import dataclass, field
from math import isclose

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.movement import MovementStrategy


@dataclass(kw_only=True)
class Grid(MovementStrategy):
    def is_injection_location(self) -> bool:
        return True

    # The amount of steps to take in each dimension.
    step_x: float
    step_y: float

    # a uniform offset for both sides.
    # can be used to start the grid further in the middle of the chip
    offset_x: float = 0.0
    offset_y: float = 0.0

    position: Point2D = field(init=False)

    def __post_init__(self):
        # this inits pos_x and pos_y
        self.reset()

    def __next__(self) -> Point2D:
        self.position.x += 1 / (self.step_x + 1)
        if isclose(self.position.x, 1 - self.offset_x):
            self.position.x = self.offset_x + 1 / (self.step_x + 1)

            self.position.y += 1 / (self.step_y + 1)
            if isclose(self.position.y, (1 - self.offset_y)):
                raise StopIteration()

        return self.position

    def reset(self):
        self.position = Point2D(self.offset_x, self.offset_y + 1 / (self.step_y + 1))
        # self.pos_x = self.offset_x
        # self.pos_y = self.offset_y + 1 / (self.step_y + 1)  # x also starts there
