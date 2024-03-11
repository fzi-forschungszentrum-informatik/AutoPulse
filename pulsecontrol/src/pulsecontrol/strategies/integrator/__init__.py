from abc import abstractmethod
from dataclasses import dataclass

from pulsecontrol.helpers import HasLogger
from pulsecontrol.strategies import Strategy


@dataclass(kw_only=True)
class Integrator(Strategy, HasLogger):
    strategy: str = "integrator"

    _stop_request: bool = False

    @abstractmethod
    def start(self):
        raise NotImplementedError()

    def reset(self):
        self.log.info("Called reset on the integrator")
        self._stop_request = True
        super().reset()

    @abstractmethod
    def continue_experiment(self):
        raise NotImplementedError()
