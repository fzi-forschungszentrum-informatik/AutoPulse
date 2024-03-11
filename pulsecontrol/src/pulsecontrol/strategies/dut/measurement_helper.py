from dataclasses import dataclass
from time import sleep

from gpiozero import LED

from pulsecontrol.helpers import HasLogger
from pulsecontrol.strategies.dut import DutStrategy, InjectionResult


@dataclass(kw_only=True)
class MeasurementHelper(DutStrategy, HasLogger):
    selector: str = "picture_trigger"
    trigger_pin: int = 18
    _counter: int = 0

    def move(self) -> bool:
        return True

    def start(self):
        led = LED(self.trigger_pin)

        # wait for measurement to stabilize
        sleep(4)
        self.log.info(f"Took Picture ({self._counter})")
        self._counter += 1
        led.on()
        # Wait for picture to be taken. This might need to be shortened
        sleep(0.19)
        led.off()

    def check_success(self) -> InjectionResult:
        return InjectionResult.FAILURE

    def reset(self):
        super().reset()
        self._counter = 0
