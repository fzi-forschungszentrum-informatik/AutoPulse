from dataclasses import dataclass, field
from random import randint
from time import sleep
from typing import Literal, Generator, Iterator, Callable

import chipwhisperer as cw
from chipwhisperer.capture.scopes import OpenADC
# The chipwhisperer api is a bit borked, ignore this import error
from chipwhisperer.capture.scopes._OpenADCInterface import ClockSettings  # noqa
from chipwhisperer.capture.scopes.cwhardware.ChipWhispererExtra import GPIOSettings, TriggerSettings
from chipwhisperer.capture.scopes.cwhardware.ChipWhispererGlitch import GlitchSettings
from chipwhisperer.capture.targets import SimpleSerial
from pulsecontrol.strategies.injector.chip_shouter import ChipShouter

from pulsecontrol.helpers import HasLogger


@dataclass(kw_only=True)
class Offset:
    start: int
    end: int
    step: int

    _current: Iterator[int] = None

    def __iter__(self):
        self._current = iter(range(self.start, self.end, self.step))
        return self

    def __next__(self):
        if self._current is None:
            raise StopIteration
        return next(self._current)


@dataclass(kw_only=True)
class Range:
    lower: int
    upper: int
    current: int = field(init=False)

    def __post_init__(self):
        self.current = randint(self.lower, self.upper)

    def update(self):
        self.current = randint(self.lower, self.upper)


@dataclass(kw_only=True)
class Glitch(HasLogger):
    clk_src: Literal["target", "clkgen", "pll"]
    output: Literal["clock_xor", "clock_or", "glitch_only", "clock_only", "enable_only"]
    trigger_src: Literal["continuous", "manual", "ext_single", "ext_continuous"]
    arm_timing: Literal["no_glitch", "before_scope", "after_scope"]

    # Desired number of clock cycles the pulse will be active
    repeat: Range

    def set(self, glitch: GlitchSettings, clkgen_freq: float):
        glitch.clk_src = self.clk_src
        glitch.output = self.output
        glitch.trigger_src = self.trigger_src
        glitch.arm_timing = self.arm_timing
        if ns := (self.repeat.current / clkgen_freq * 1e9) < 20:
            self.log.warning("Pulse width is close to the minimum, consider increasing the number of repeats. %s ns",
                             ns)

        self.update(glitch)

    def update(self, glitch: GlitchSettings):
        # Calculate the number of repeats needed to get the desired pulse width
        if self.repeat is Range:
            self.repeat.update()
            new_val = self.repeat.current
            glitch.repeat = new_val
            self.log.info("Updated pulse repeat to: %s", self.repeat.current)
        else:
            self.log.info("Pulse repeat is fixed to: %s", self.repeat)


@dataclass(kw_only=True)
class Clock(HasLogger):
    """ Clock Settings (Lite/Pro) """

    clkgen_src: Literal["extclk", "system", "internal"] | None
    clkgen_mul: int | None  # Valid ranges are between [2, 256]
    clkgen_div: int | None  # Valid ranges are between [1, 256]
    clkgen_freq: float | None  # Tries to find the best mul/div values for the desired frequency

    adc_src: Literal["extctl_x1", "extctl_x4", "clkgen_x1", "clkgen_x4", "extclk_dir"]
    freq_ctr_src: Literal["clkgen", "extclk"]

    def set(self, clock: ClockSettings):
        if self.clkgen_src is not None:
            clock.clkgen_src = self.clkgen_src
        if self.clkgen_mul is not None:
            clock.clkgen_mul = self.clkgen_mul
        if self.clkgen_div is not None:
            clock.clkgen_div = self.clkgen_div
        if self.clkgen_freq is not None:
            clock.clkgen_freq = self.clkgen_freq

        if self.adc_src is not None:
            clock.adc_src = self.adc_src
        if self.freq_ctr_src is not None:
            clock.freq_ctr_src = self.freq_ctr_src

        # DCM is unlocked after setting the clock, use this to lock both DCMs
        clock.reset_dcms()


@dataclass(kw_only=True)
class IO(HasLogger):
    """ GPIOSettings """

    glitch_hp: bool = False
    glitch_lp: bool = False
    hs2: Literal["clkgen", "glitch", "disabled"] = "disabled"
    tio1: Literal["serial_rx", "serial_tx", "high_z", "gpio_low", "gpio_high", "gpio_disabled"] = 'high_z'
    tio2: Literal["serial_rx", "serial_tx", "high_z", "gpio_low", "gpio_high", "gpio_disabled"] = 'high_z'
    tio3: Literal[
        "serial_rx", "serial_tx", "serial_tx_rx", "high_z", "gpio_low", "gpio_high", "gpio_disabled"] = 'high_z'
    tio4: Literal["serial_tx", "high_z", "gpio_low", "gpio_high", "gpio_disabled"] = 'high_z'

    def set(self, io: GPIOSettings):
        io.glitch_hp = self.glitch_hp
        io.glitch_lp = self.glitch_lp
        io.hs2 = self.hs2
        io.tio1 = self.tio1
        io.tio2 = self.tio2
        io.tio3 = self.tio3
        io.tio4 = self.tio4


@dataclass(kw_only=True)
class Trigger(HasLogger):
    """ Generic Trigger Settings """

    # Take a look at `TriggerSettings` for more information 
    triggers: str | None = None

    def set(self, trigger: TriggerSettings):
        if self.triggers is not None:
            trigger.triggers = self.triggers


@dataclass(kw_only=True)
class Whisperer(HasLogger):
    scope: OpenADC = field(repr=False, default=None)

    glitch: Glitch = field(default_factory=Glitch)
    clock: Clock = field(default_factory=Clock)
    offset: Offset = field(default_factory=Offset)
    io: IO = field(default_factory=IO)
    trigger: Trigger = field(default_factory=Trigger)

    # Chipshouter controlled by the whisperer
    # Required for accurate triggers
    chipshouter: ChipShouter | None = None

    # this value determines the number of repeats needed to get the desired pulse width
    clkgen_freq: float
    target: SimpleSerial = field(repr=False, default=None)
    target_baud: int = 115200
    # Some boards use a reset pin, some an enable pin.
    # This value determines what value is required to reset the board.
    board_on_pin_state: bool

    def __post_init__(self):
        self.scope: OpenADC = cw.scope()
        self.scope.default_setup()

        self.target = cw.target(self.scope, SimpleSerial, noflush=True)
        self.target.baud = self.target_baud

        self.trigger.set(self.scope.trigger)

        # Set glitch source and parameters
        self.glitch.set(self.scope.glitch, self.clock.clkgen_freq)
        # This value is important for calculating the real glitch length in nanoseconds
        self.clock.set(self.scope.clock)
        # Order might be important
        self.io.set(self.scope.io)

        self.log.info(self.scope)

        # Start shouter, if available
        if self.chipshouter is not None:
            self.chipshouter.init_shouter()

    def is_ready(self):
        if self.chipshouter.probe_attached():
            return True
        self.log.error("Probe is not attached, waiting until it is attached...")
        return False

    def restart_board(self):
        """ 
        Restarts the board by toggling the reset pin.
        Waiting for the boot to finish is the responsibility of the caller.
        """
        self.scope.io.nrst = not self.board_on_pin_state
        # wait for reset
        sleep(0.05)
        self.scope.io.nrst = self.board_on_pin_state

    def pre_arm(self) -> Generator[(int, int, int), None, None]:
        for offset in self.offset:
            self.chipshouter.arm()
            self.restart_board()
            self.scope.glitch.ext_offset = offset
            yield offset, self.chipshouter.voltage.current, self.glitch.repeat.current

    def wait_for_probe_attachment(self):
        while not self.chipshouter.probe_attached():
            self.log.info("Probe not recognized, waiting...")
            sleep(5)
        self.log.info("Probe attached successfully, continuing...")

    def update(self):
        self.chipshouter.update()
        self.glitch.update(self.scope.glitch)

    def reset(self):
        self.log.info("Resetting Whisperer")
        self.chipshouter.disarm()
        self.chipshouter.reset()
        self.scope.reset_sam3u()
        self.scope.dis()
        self.target.dis()
