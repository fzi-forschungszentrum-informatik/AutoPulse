from dataclasses import dataclass, field
from time import sleep

import serial
from serial import Serial, LF

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import logging
    from unittest.mock import MagicMock

    logging.error("RPi Module not installed, this is OK if not executed on a pi.")
    # This is a stub which allows us to run the code in environments without the picamera module
    GPIO = MagicMock()

from pulsecontrol.strategies.dut import DutStrategy, InjectionResult


@dataclass(kw_only=True)
class BasicUart(DutStrategy):
    injections_at_same_location: int = 15

    # Pin to use as a reset trigger for the DUT
    gpio_restart_trigger: int
    # Seconds to wait for the DUT to start
    boot_wait: int

    serial_port: str = "/dev/ttyS0"

    serial: Serial = field(init=False)

    _counter: int = field(repr=False, default=0)
    _timeout: int = field(repr=False, default=1)

    def __post_init__(self):
        GPIO.setup(self.gpio_restart_trigger, GPIO.OUT)
        GPIO.output(self.gpio_restart_trigger, 0)

        self.serial = serial.Serial(
            port=self.serial_port,  # Replace ttyS0 with ttyAM0 for Pi1,Pi2,Pi0
            timeout=self._timeout,
        )

    def move(self) -> bool:
        if self._counter == self.injections_at_same_location:
            self._counter = 0
            return True
        self._counter += 1
        return False

    def start(self):
        pass

    def check_success(self) -> InjectionResult:
        res = self.serial.readall()
        if b"broken" in res:
            return InjectionResult.SUCCESS
        elif not res:  # Nothing was returned
            return InjectionResult.RESET
        elif b"\n" not in res:  # Timeout occurred but there was something in the buffer
            # TODO: might be the reset condition as well?
            # no idea on how to check right now
            return InjectionResult.FAILURE
        else:
            return InjectionResult.FAILURE  # received something

    def restart_dut(self):
        self.reset()
        if (difference := self.boot_wait - self._timeout) > 0:
            sleep(difference * 2)
        self.serial.read_until(b"READY" + LF)

    def reset(self):
        GPIO.output(self.gpio_restart_trigger, 1)
        sleep(0.2)
        GPIO.output(self.gpio_restart_trigger, 0)
