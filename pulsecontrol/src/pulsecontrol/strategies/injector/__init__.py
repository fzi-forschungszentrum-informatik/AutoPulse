from abc import abstractmethod
from dataclasses import dataclass

from pulsecontrol.strategies import Strategy


@dataclass(kw_only=True)
class InjectorStrategy(Strategy):
    strategy: str = "injector"

    @abstractmethod
    def inject(self, count: int):
        """
        Inject pulses.

        Args:
            count: The amount of pulses that are supposed to be injected.
        """
        raise NotImplementedError()

    @abstractmethod
    def arm(self):
        raise NotImplementedError()

    @abstractmethod
    def disarm(self):
        raise NotImplementedError()
