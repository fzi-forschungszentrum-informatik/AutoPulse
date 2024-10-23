import time
from abc import ABC
from dataclasses import dataclass, asdict, field
from typing import TypeVar, Generic

from pulsecontrol.helpers import HasLogger
from pulsecontrol.strategies.dut import DutStrategy
from pulsecontrol.strategies.tools.chip_whisperer import Whisperer

Effect = TypeVar("Effect")


@dataclass
class Attack(Generic[Effect]):
    effect: Effect
    offset: int
    voltage: int
    repeat: int


@dataclass(kw_only=True)
class EmfiAttack(DutStrategy[Attack, Effect], HasLogger, ABC):
    whisperer: Whisperer

    # List of attack results
    attacks: list[Attack[Effect]] = field(default_factory=list, repr=False)

    # Count the number of experiments
    _counter: int = field(default=0, repr=False)

    # Flag to indicate if the user stopped the attack
    _reset: bool = field(default=False, repr=False)

    def check_results(self) -> list[Attack[Effect]]:
        return self.attacks

    def update(self):
        self.whisperer.update()
        self._counter = 0

    def reset(self):
        self.log.info("Resetting Whisperer")
        super().reset()
        self._reset = True
        self._counter = 0
        self.whisperer.reset()

    def start(self):
        self.whisperer.wait_for_probe_attachment()
        self._reset = False
        self._counter += 1

        self.attacks = []
        # If board has been hold in reset, turn it on now
        time.sleep(2)
        # to get notable offset it must be around 24000000 or so
        for offset, voltage, repeat in self.whisperer.pre_arm():
            start_time = time.time()
            if self._reset:
                break
            # The attack is performed here.
            # It's important to arm the scope somewhere in this function
            effect = self.attack()
            result = Attack(
                effect=effect,
                offset=offset,
                voltage=voltage,
                repeat=repeat
            )
            self.attacks.append(result)
            self.log.info("Success: %s", asdict(result))
            end_time = time.time()
            self.log.info(f"Experiment Duration: {end_time - start_time}")
