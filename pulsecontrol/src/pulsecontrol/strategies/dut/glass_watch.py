from dataclasses import dataclass, field

from serial import Serial

from pulsecontrol.helpers import HasLogger

from pulsecontrol.strategies.dut import DutStrategy, InjectionResult


@dataclass(kw_only=True)
class GlassWatch(DutStrategy, HasLogger):
    serial_port: str
    serial: Serial = field(init=False)

    _timeout: int = field(repr=False, default=1)

    data: list = field(default_factory=list)

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
        self.data.append(output)

    def check_success(self) -> InjectionResult:
        return InjectionResult.SUCCESS

    def reset(self):
        pass
