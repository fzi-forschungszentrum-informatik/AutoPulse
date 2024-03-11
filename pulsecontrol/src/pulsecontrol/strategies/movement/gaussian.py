from dataclasses import dataclass, field

import numpy as np

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.movement import MovementStrategy


@dataclass(kw_only=True)
class Gaussian(MovementStrategy):
    """
    Selects the new position by sampling a gaussian distribution.
    """

    var: float
    center: Point2D
    # The number of samples to take. -1 for infinite.
    iterations: int = -1
    _original_iterations: int = field(init=False)

    def __post_init__(self):
        self._original_iterations = self.iterations

    def is_injection_location(self) -> bool:
        return True

    def reset(self):
        self.iterations = self._original_iterations

    def __next__(self) -> Point2D:
        if self.iterations == 0:
            raise StopIteration()
        self.iterations -= 1
        return Point2D.from_iter(
            np.clip(
                np.random.normal(loc=self.center.to_tuple(), scale=self.var, size=2),
                0,
                1,
            )
        )
