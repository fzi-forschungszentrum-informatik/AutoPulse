from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

from pulsecontrol.strategies import Strategy


class InjectionResult(Enum):
    SUCCESS = auto()  # if a glitch was detected
    FAILURE = auto()  # if the device didn't show an effect
    RESET = auto()  # if the device needed a reset or reset on its own


@dataclass(kw_only=True)
class DutStrategy(Strategy):
    strategy: str = "dut"

    """
    For listening to events from the device-under-test (DUT).
    This strategy decides when to move to the next position, and decides success or failure.
    """

    @abstractmethod
    def move(self) -> bool:
        """
        Set this to true if you want to move to the next location.
        """
        raise NotImplementedError()

    @abstractmethod
    def check_success(self) -> InjectionResult:
        """
        Checks communication with the DUT or another device connected to the DUT, and classifies the response as
        """
        raise NotImplementedError()

    @abstractmethod
    def start(self):
        """
        Called before the injection. Can be used to initialize the chip for example.
        """
        raise NotImplementedError()
