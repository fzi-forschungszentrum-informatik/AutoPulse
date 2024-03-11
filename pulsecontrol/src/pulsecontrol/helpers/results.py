from dataclasses import dataclass
from typing import Any



@dataclass
class AttackResults:
    image_coords: tuple[float, float]
    world_coords: tuple[float, float]

    # The attempt number for this position
    iteration: int

    # The results depend on multiple parameters that in turn depend on the device used to inject the fault
    results: list[Any]
