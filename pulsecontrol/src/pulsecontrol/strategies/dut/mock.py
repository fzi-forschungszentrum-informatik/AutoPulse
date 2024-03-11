from dataclasses import dataclass
from random import random

from pulsecontrol.strategies.dut import DutStrategy, InjectionResult


@dataclass(kw_only=True)
class Mock(DutStrategy):
    test: str = "test"

    def move(self) -> bool:
        return True

    def start(self):
        pass

    def check_success(self) -> InjectionResult:
        number = random()
        if 0.9 < number:
            return InjectionResult.RESET
        elif 0.7 < random():
            return InjectionResult.SUCCESS
        return InjectionResult.FAILURE

    def reset(self):
        pass
