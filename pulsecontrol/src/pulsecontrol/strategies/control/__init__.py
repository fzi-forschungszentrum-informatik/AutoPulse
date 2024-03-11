from abc import abstractmethod
from dataclasses import dataclass

from pulsecontrol.strategies import Strategy
from pulsecontrol.helpers import Point3D


@dataclass(kw_only=True)
class ControlStrategy(Strategy):
    strategy: str = "control"

    @abstractmethod
    def move_to(self, x: float, y: float):
        """
        Move to a point on the XY plane.

        Args:
            x: x coordinate to move to.
            y: y coordinate to move to
        """
        raise NotImplementedError()

    @abstractmethod
    def move_rel(self, x: float, y: float, z: float):
        """
        Relative move in the x, y and z direction.
        """
        raise NotImplementedError()

    @abstractmethod
    def add_offset(self, x: float, y: float, z: float):
        """
        Allows to calibrate for changes in the position of the probe.
        """
        raise NotImplementedError()

    @abstractmethod
    def home(self):
        raise NotImplementedError()

    @abstractmethod
    def home_x(self):
        raise NotImplementedError()

    @abstractmethod
    def home_y(self):
        raise NotImplementedError()

    @abstractmethod
    def home_xy(self):
        raise NotImplementedError()

    @abstractmethod
    def home_z(self, x: float, y: float):
        """
        Home the z axis at a specified position.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_homed(self) -> tuple[bool, bool, bool]:
        """
        Return true for each axis if they are homed.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_limits(self) -> Point3D:
        """
        Get the maximum position for each axis.
        """
        raise NotImplementedError()
