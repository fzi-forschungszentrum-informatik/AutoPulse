from dataclasses import dataclass, InitVar, field
from random import randint
from time import sleep
from typing import Optional

from chipshouter import ChipSHOUTER
from chipshouter.com_tools import Firmware_State_Exception, Reset_Exception

from pulsecontrol.helpers import HasLogger
from pulsecontrol.strategies.injector import InjectorStrategy


class OverheatException(Exception):
    pass


@dataclass(kw_only=True)
class Pulse:
    width: int  # nS pulse width
    repeat: int = 1
    dead_time: Optional[int] = None  # pause between pulses when using repeats

    def set(self, chip_shouter: ChipSHOUTER):
        chip_shouter.pulse.width = self.width
        chip_shouter.pulse.repeat = self.repeat
        if self.dead_time is not None:
            chip_shouter.pulse.deadtime = self.dead_time


@dataclass(kw_only=True)
class Modes:
    emode: bool = False
    hwtrig_mode: bool = True
    hwtrig_term: bool = True

    def set(self, chip_shouter: ChipSHOUTER):
        chip_shouter.emode = self.emode
        chip_shouter.hwtrig_mode = self.hwtrig_mode
        chip_shouter.hwtrig_term = self.hwtrig_term


@dataclass(kw_only=True)
class Voltage(HasLogger):
    lower: int
    upper: int
    current: int = field(init=False)

    def __post_init__(self):
        self.current = randint(self.lower, self.upper)

    def update(self, chip_shouter: ChipSHOUTER):
        self.current = randint(self.lower, self.upper)
        chip_shouter.voltage = self.current
        self.log.info("Chipshouter set Voltage to: %s" % chip_shouter.voltage)


@dataclass(kw_only=True)
class ChipShouter(InjectorStrategy, HasLogger):
    chipshouter: ChipSHOUTER = field(default=None)
    mode: Modes = field(default_factory=Modes)

    pulse: Pulse | None
    voltage: Voltage  # between 150 and 500V

    com_port: InitVar[str]

    mute: bool = False

    _initialized: bool = field(default=False, repr=False)

    def __post_init__(self, com_port: str):
        self.chipshouter = ChipSHOUTER(com_port)

    def clear_errors(self):
        if fault := self.chipshouter.faults_current:
            self.log.error(f"Faults detected: {fault}")
        if fault := self.chipshouter.faults_latched:
            self.log.error(f"Latched faults detected: {fault}")

        self.chipshouter.faults_current = 0
        sleep(5)

    def probe_attached(self) -> bool:
        return not self.chipshouter.faults_current

    def update(self):
        if isinstance(self.voltage, Voltage):
            self.voltage.update(self.chipshouter)

    def init_shouter(self):
        self.log.info("Chipshouter init")
        # self.chipshouter.voltage = self.voltage
        self.update()
        self.chipshouter.mute = self.mute

        if self.pulse:
            self.pulse.set(self.chipshouter)
        elif self.mode.hwtrig_mode or self.mode.hwtrig_term or not self.mode.emode:
            self.log.info(
                "Pulse settings missing. They are required when not using a hardware trigger such as the chipshouter")
        self.mode.set(self.chipshouter)
        self._initialized = True

    def reset(self):
        try:
            self.disarm()
        finally:
            self.chipshouter.reset = True
            self._initialized = False

    def inject(self, count: int = 1):
        if not self.chipshouter.armed:
            raise ValueError(
                "Chipshouter is not armed, maybe an error hasn't been handled?"
            )
        self.chipshouter.pulse = count

    def arm(self, _retry: int = 3):
        if not self._initialized:
            self.init_shouter()
            sleep(5)
        try:
            self.chipshouter.armed = True
        except Firmware_State_Exception as e:
            if 'State:armed' in str(e):
                self.log.debug("Chipshouter already armed")
                return
            if 'fault_overtemp' in str(e) or 'fault_high_voltage' in str(e):
                self.reset()
                raise OverheatException()
            if not _retry:
                raise e
            self.log.error(f"Error arming chipshouter, retrying...\n{e}")
            self.clear_errors()
            self.arm(_retry - 1)
        except Reset_Exception:
            sleep(5)

    def disarm(self):
        self.chipshouter.armed = False
