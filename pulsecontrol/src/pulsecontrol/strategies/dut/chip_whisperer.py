from dataclasses import dataclass, field, asdict
from functools import cached_property
from random import randint
from time import sleep
from typing import Literal

import chipwhisperer as cw
from chipwhisperer.capture.scopes import OpenADC
from chipwhisperer.capture.scopes.cwhardware.ChipWhispererExtra import GPIOSettings
from chipwhisperer.capture.scopes.cwhardware.ChipWhispererGlitch import GlitchSettings
from chipwhisperer.capture.targets import SimpleSerial
from pulsecontrol.strategies.injector.chip_shouter import ChipShouter
from tqdm import tqdm

from pulsecontrol.helpers import HasLogger, format_hex2
from pulsecontrol.strategies.dut import DutStrategy

from scripts.com.bootloader import public_password

MULTI = False


@dataclass
class Results:
    success: bool
    offset: int
    voltage: int
    repeat: int


@dataclass(kw_only=True)
class Offset:
    start: int
    end: int
    step: int

    def __iter__(self):
        return range(self.start, self.end, self.step).__iter__()


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

    # Desired pulse width in nanoseconds
    pulse_width: Range | None = None
    # Desired number of clock cycles the pulse will be active
    repeat: Range | int | None = None

    def __post_init__(self):
        if self.pulse_width is None and self.repeat is None:
            raise ValueError("Either pulse_width or repeat must be set")
        if self.pulse_width is not None and self.repeat is not None:
            raise ValueError("Only one of pulse_width or repeat must be set")

    def set(self, glitch: GlitchSettings, clkgen_freq: float):
        glitch.clk_src = self.clk_src
        glitch.output = self.output
        glitch.trigger_src = self.trigger_src
        glitch.arm_timing = self.arm_timing
        self.update(glitch, clkgen_freq)

    def update(self, glitch: GlitchSettings, clkgen_freq: float):
        # Calculate the number of repeats needed to get the desired pulse width
        if self.pulse_width:
            self.pulse_width.update()
            data = int((self.pulse_width.current * clkgen_freq) / 1e9)
            glitch.repeat = data
            self.repeat = data
            self.log.info("Updated pulse width to: %s ns => %s ClockCycles @ %f", self.pulse_width.current, data,
                          clkgen_freq)
        else:
            self.repeat.update()
            glitch.repeat = self.repeat.current
            self.log.info("Updated pulse repeat to: %s ClockCycles @ %f", self.repeat.current, clkgen_freq)


@dataclass(kw_only=True)
class IO(HasLogger):
    """ GPIOSettings """

    glitch_hp: bool = False
    glitch_lp: bool = False
    hs2: Literal["clkgen", "glitch", "disabled"] = "disabled"
    tio1: Literal["serial_rx", "serial_tx", "high_z", "gpio_low", "gpio_high", "gpio_disabled"] = 'serial_rx'
    tio2: Literal["serial_rx", "serial_tx", "high_z", "gpio_low", "gpio_high", "gpio_disabled"] = 'serial_tx'
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
class Whisperer(DutStrategy, HasLogger):
    whisperer: bool  # selection flag for dacite

    _counter: int = field(default=0, repr=False)
    fixed_end: int = -1
    move_after: int = 20

    scope: OpenADC = field(repr=False, default=None)
    glitch: Glitch = field(default_factory=Glitch)
    offset: Offset = field(default_factory=Offset)
    io: IO = field(default_factory=IO)
    chipshouter: ChipShouter

    # this value determines the number of repeats needed to get the desired pulse width
    clkgen_freq: float = 20e6
    target: SimpleSerial = field(repr=False, default=None)

    public_password: list[int] = field(default_factory=lambda: [0xFE, 0xED, 0xFA, 0xCE, 0xCA, 0xFE, 0xBE, 0xEF])

    _success: list[Results] = field(default_factory=list, repr=False)
    _reset: bool = field(default=False, repr=False)

    def __post_init__(self):
        self.scope: OpenADC = cw.scope()
        self.scope.default_setup()

        self.io.set(self.scope.io)
        # chipshouter trigger setup
        self.scope.trigger.triggers = "tio2"

        self.target = cw.target(self.scope, SimpleSerial, noflush=True)
        self.target.baud = 14400

        # Set glitch source and parameters
        self.glitch.set(self.scope.glitch, self.clkgen_freq)
        # This value is important for calculating the real glitch length in nanoseconds
        self.scope.clock.clkgen_freq = self.clkgen_freq

        self.log.info(self.scope)

        # These settings have an effect again
        # self.scope.io.glitch_hp = False
        # self.scope.io.glitch_lp = True

        # Start shouter
        self.chipshouter.init_shouter()

    def move(self) -> bool:
        return not bool(self._counter % self.move_after)

    @cached_property
    def autobaud_enabled(self) -> bool:
        self.restart_board()
        # Autobaud will return 0x59 (Y) if it is enabled, no matter the input
        val = self.check_echo(0x00)
        self.restart_board()
        return val

    def restart_board(self):
        self.scope.io.nrst = False
        # wait for reset
        sleep(0.05)
        self.scope.io.nrst = None
        # wait for boot
        sleep(0.2)

    def init_uart(self):
        self.target.ser.flush()
        if self.autobaud_enabled:
            self.target.ser.write(b"\x00")
            sleep(0.05)
            self.log.info('Flushed UART; Sent auto-baud zero-byte: %s', format_hex2(*self.target.ser.hardware_read(1)))
        else:
            self.log.info('Flushed UART; Auto-baud not enabled')

    def check_echo(self, *data: int | bytes) -> bool:
        ser = self.target.ser
        ser.flush()
        for d in data:
            ser.write(bytearray([d]))
        response = ser.hardware_read(len(data) + 5)
        self.log.info("Sent/Response: %s <-> %s", format_hex2(*data), format_hex2(*response))
        return tuple(response) == data

    def send_password(self, password: list[int]) -> bool:
        serial = self.target.ser
        serial.flush()

        # write all bytes except the last one
        response = []
        for pw in password[:-1]:
            serial.write(bytearray([pw]))
            sleep(0.01)
            res = serial.hardware_read(5)
            response.extend(res)

        if response != password[:-1]:
            self.log.error("Send/Receive missmatch")
            return False

        ###############################################
        # Glitch (arm will enable the trigger on the serial connection)
        self.scope.arm()
        serial.write(bytearray([password[-1]]))

        # check if the password was sent correctly
        response.extend(serial.hardware_read(5))
        self.log.info('Response: %s', format_hex2(*response))
        if response[:len(password)] == password:
            self.log.info("Data sent correctly")
        else:
            self.log.info("Last byte not sent correctly. Expected: %s, got: %s", format_hex2(*password),
                          format_hex2(*response))

        serial.flush()
        # sleep(0.1)

        # Send start address, will indicate if the password was accepted
        try:
            return self.check_echo(0x2F, 0x5A)
        except IOError as e:
            self.log.error("Error: %s", e)
            return False

    def download_data(self, data: list):
        """
        https://www.youtube.com/watch?v=pkhV9K9raHE
        size = 0x2000
        """
        serial = self.target.ser
        for i, w in tqdm(enumerate(data)):
            serial.write(bytearray([w]))
            response = serial.read(1)

            if len(response) != 1:
                self.log.info("Response: %x", response)
                raise IOError("wrong response length")
            elif ord(response[0]) != w:
                print("got wrong echo: %x != %x" % (ord(response[0]), w))
                raise IOError("wrong echo")
        serial.flush()

    def start(self):
        self._reset = False
        # password = [0xFF, 0xFE, 0xCA, 0xCE, 0xAB, 0xDA, 0xD4, 0xAF]
        password = public_password
        # password[-1] = 0xFF
        self._success = []

        for offset in self.offset:
            if self._reset:
                break

            self.chipshouter.arm()
            self.restart_board()
            self.init_uart()
            self.scope.glitch.ext_offset = offset
            armed_state = self.scope.arm()
            self.log.info("Arming chipwhisperer, state: %s", armed_state)

            result = Results(success=self.send_password(password), offset=offset,
                             voltage=self.chipshouter.voltage.current,
                             repeat=self.glitch.repeat.current)
            self._success.append(result)
            self.log.info("Success: %s", asdict(result))

    def wait_for_probe_attachment(self):
        while not self.chipshouter.probe_attached():
            self.log.info("Probe not recognized, waiting...")
            sleep(5)
        self.log.info("Probe attached successfully, continuing...")

    def update(self):
        self.chipshouter.update()
        self.glitch.update(self.scope.glitch, self.clkgen_freq)

    def check_success(self) -> list[Results]:
        self._counter += 1
        return self._success

    def reset(self):
        self.log.info("Resetting Whisperer")
        super().reset()
        self._reset = True
        self._counter = 0
        self.chipshouter.disarm()
        self.scope.dis()
        self.target.dis()
