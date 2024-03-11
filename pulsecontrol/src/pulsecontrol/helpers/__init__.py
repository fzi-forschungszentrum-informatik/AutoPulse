import logging
import operator
from dataclasses import dataclass, field
from enum import Enum
from logging import Logger
from typing import Union, Iterable, Callable


@dataclass(kw_only=True)
class HasLogger:
    _log: Logger | None = field(repr=False, default=None)

    @property
    def log(self):
        if self._log is None:
            name = ".".join((self.__module__, self.__class__.__name__))
            self._log = logging.getLogger(name)
        return self._log


def format_hex(*data: int | bytes) -> str:
    return ' '.join(map(lambda x: f"0x{x:02X}", data))


def format_hex2(*data: int | bytes) -> list[str]:
    out = []
    for d in data:
        tmp = '0x'
        tmp += hex(d)[2:].upper()
        out.append(tmp)
    return out

class ConfigurationError(Exception): ...


class DeploymentType(Enum):
    HTTP = 1
    USB = 2  # unsupported at the moment


class CameraType(Enum):
    PROBE = 1
    PCB = 2


class FromIter:
    def __init__(self, *args):
        super().__init__(*args)

    @classmethod
    def from_iter(cls, data: Iterable):
        return cls(*data)


Operable = Union["Point2D", float, int, tuple[float, float]]


@dataclass
class Point2D(FromIter):
    x: float
    y: float

    def to_list(self) -> list[float, float]:
        return [self.x, self.y]

    def to_tuple(self) -> tuple[float, float]:
        return self.x, self.y

    def _operation_by_type(
        self,
        other: Operable,
        operation: Callable[[float, Union[float, int]], float],
    ) -> "Point2D":
        match other:
            case tuple(x, y) | Point2D(x, y):
                return Point2D(operation(self.x, x), operation(self.y, y))
            case float() | int() | _:
                return Point2D(operation(self.x, other), operation(self.y, other))

    def __mul__(self, other: Union["Point2D", float, int, tuple[float, float]]) -> "Point2D":
        return self._operation_by_type(other, operation=operator.mul)

    def __add__(self, other: Union["Point2D", float, int, tuple[float, float]]) -> "Point2D":
        return self._operation_by_type(other, operation=operator.add)

    def __sub__(self, other: Union["Point2D", float, int, tuple[float, float]]) -> "Point2D":
        return self._operation_by_type(other, operation=operator.sub)

    def __truediv__(self, other: Union["Point2D", float, int, tuple[float, float]]) -> "Point2D":
        return self._operation_by_type(other, operation=operator.truediv)

    def __floordiv__(self, other: Union["Point2D", float, int, tuple[float, float]]) -> "Point2D":
        return self._operation_by_type(other, operation=operator.floordiv)

    def __getitem__(self, item: int):
        match item:
            case 0:
                return self.x
            case 1:
                return self.y
            case _:
                raise IndexError()

    def __format__(self, format_spec):
        return (
            f"{self.__class__.__name__}("
            f"{format(self.x, format_spec)}, {format(self.y, format_spec)})"
        )


Angle = float
Width = float
Height = float
# Numpy doesn't allow typing for array shapes
# Any workarounds with Annotated[NDArray[np.float32], Literal[2]] won't work with dacite
# There is currently no good way of typing this, so we have to use `float`.
# Point2D = tuple[float, float]
Point3D = tuple[float, float, float]
Rectangle = tuple[tuple[float, float], tuple[Width, Height], Angle]
