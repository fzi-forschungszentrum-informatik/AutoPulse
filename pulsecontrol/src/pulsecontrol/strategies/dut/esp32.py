from dataclasses import dataclass
from enum import Enum
from time import sleep

from pulsecontrol.helpers import HasLogger
from pulsecontrol.strategies.dut.emfi_attack import EmfiAttack


class EMPEffect(Enum):
    ERROR = "error"
    SUCCESS = "success"
    NO_EFFECT = "no_effect"
    NO_RESPONSE = "no_response"
    REBOOT = "reboot"


@dataclass(kw_only=True)
class EspAttack(EmfiAttack[EMPEffect], HasLogger):
    # Flag to hint dacite which attack to use
    esp: bool

    fixed_end: int = -1
    move_after: int = 20

    def move(self) -> bool:
        return not bool(self._counter % self.move_after)

    def send_cmd_and_get_response(self, *data: int | bytes) -> str:
        ser = self.whisperer.target.ser
        ser.flush()
        for d in data:
            ser.write(bytearray([d]))
        response = ser.read(800, 20)
        self.log.info("Response: %s", response)
        return response

    def attack(self) -> EMPEffect:
        response = self.send_cmd_and_get_response(0x61)
        if response.strip() == "10000":
            return EMPEffect.NO_EFFECT
        # Restart board to prevent unwanted behaviour in the following attacks
        self.whisperer.restart_board()
        sleep(1)
        if not response.strip():
            return EMPEffect.NO_RESPONSE
        if "I (" in response or "cpu_start" in response:
            return EMPEffect.REBOOT
        if response[:4].strip().isdigit():
            return EMPEffect.SUCCESS
        return EMPEffect.ERROR
