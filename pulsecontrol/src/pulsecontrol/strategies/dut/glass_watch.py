from dataclasses import dataclass, field
from enum import Enum

from serial import Serial

from pulsecontrol.helpers import HasLogger

from pulsecontrol.strategies.dut import DutStrategy


class Result(Enum):
    SUCCESS = 'success'


@dataclass
class Measurement:
    value: str
    result: Result


@dataclass(kw_only=True)
class GlassWatch(DutStrategy[Measurement, Result], HasLogger):
    """
    Interfaces with a glass rod based measurement device to measure the travel distance.
    """

    serial_port: str
    serial: Serial = field(init=False)

    _timeout: int = field(repr=False, default=1)

    data: list[Measurement] = field(default_factory=list)

    def check_results(self) -> list[Measurement]:
        return self.data

    def update(self):
        pass

    def attack(self) -> Result:
        return Result.SUCCESS

    def __post_init__(self):
        self.serial = Serial(
            port=self.serial_port,  # Replace ttyS0 with ttyAM0 for Pi1,Pi2,Pi0
            timeout=self._timeout,
        )

    def move(self) -> bool:
        return True

    def start(self):
        self.serial.write(b'D')
        output: bytes = self.serial.readall().strip()
        if b'Not zeroed' in output:
            raise ValueError(f'Not zeroed in {self.serial_port}')
        output: str = output.decode()
        self.log.info('Measured at: <%s>', output)
        self.data.append(Measurement(output, self.attack()))

    def reset(self):
        pass
