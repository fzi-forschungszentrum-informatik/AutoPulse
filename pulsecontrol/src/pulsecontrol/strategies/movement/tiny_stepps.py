from dataclasses import dataclass, field

from pulsecontrol.helpers import Point2D, ConfigurationError
from pulsecontrol.strategies.movement import MovementStrategy


@dataclass(kw_only=True)
class TinySteps(MovementStrategy):
    start_position: Point2D
    end_position: Point2D | None = None

    step_size: float

    relative_mode: bool = False
    move_back_mode: bool = False
    move_back_position: Point2D = None
    move_back_state: bool = False

    current_position: Point2D = field(init=False, repr=False)

    def __post_init__(self):
        self.current_position = self.start_position
        if self.move_back_mode and self.move_back_position is None:
            raise ConfigurationError(
                "Invalid config, set both move-back-mode and the position!"
            )
        if self.move_back_mode and self.relative_mode:
            raise ConfigurationError("Only one mode is allowed at a time!")
        if self.total_movements is not None and self.end_position is not None:
            raise ConfigurationError("Only one end condition is allowed at a time!")
        if self.total_movements is None and self.end_position is None:
            raise ConfigurationError("No end condition is set!")

        if self.total_movements is not None:
            self.end_position = Point2D(self.total_movements * self.step_size + self.start_position.x, self.start_position.y)
            self.total_movements = self.total_movements
        else:
            self.total_movements = int((self.end_position.x - self.start_position.x) / self.step_size)

    def reset(self):
        self.current_position = self.start_position

    def __next__(self) -> Point2D:
        if self.step_size + self.current_position.x > self.end_position.x:
            raise StopIteration()

        if not self.move_back_state:
            # prevent double increases
            self.current_position.x += self.step_size

        if self.move_back_mode:
            if self.move_back_state:
                self.move_back_state = False
                return self.current_position
            else:
                self.move_back_state = True
                return self.move_back_position
        elif self.relative_mode:
            return Point2D(self.step_size, 0.0)

        return self.current_position

    def is_injection_location(self) -> bool:
        return not self.move_back_state
