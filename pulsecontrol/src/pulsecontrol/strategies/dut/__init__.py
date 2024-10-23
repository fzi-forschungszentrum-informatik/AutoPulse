from abc import abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from pulsecontrol.strategies import Strategy

# The results from glitches can be very varied, so we let the user decide how to represent them.
Result = TypeVar("Result")
Attack = TypeVar("Attack")


@dataclass(kw_only=True)
class DutStrategy(Strategy, Generic[Attack, Result]):
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
    def check_results(self) -> list[Attack[Result]]:
        """
        Checks communication with the DUT or another device connected to the DUT, and classifies the response as
        """
        raise NotImplementedError()

    @abstractmethod
    def update(self):
        """
        Called after each complete attack. Is used to generate new parameters for another attack.
        """
        raise NotImplementedError()

    @abstractmethod
    def start(self):
        """
        Called before the injection. Can be used to initialize the chip for example.
        """
        raise NotImplementedError()

    @abstractmethod
    def attack(self) -> Result:
        """
        Performs the attack after everything else has been set up.
        This should only be called once all other preparations are done.
        """
        raise NotImplementedError()
