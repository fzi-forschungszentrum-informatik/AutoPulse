from dataclasses import dataclass
from os import getenv

import requests

from pulsecontrol.helpers import HasLogger, Point3D
from pulsecontrol.strategies.control import ControlStrategy
from pulsecontrol.strategies.movement import MovementError
from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning


@dataclass(kw_only=True)
class Basic:
    user: str
    password: str


@dataclass(kw_only=True)
class Moonraker(ControlStrategy, HasLogger):
    """
    Connects to the moonraker api and directly dispatches the gcode.
    Doesn't need a HttpWrapper, because there's already an http api.
    """

    endpoint: str
    basic_auth: HTTPBasicAuth = None

    def __post_init__(self):
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        self.basic_auth = HTTPBasicAuth(
            username=getenv('MOONRAKER_USER', None),
            password=getenv('MOONRAKER_PASSWORD', None)
        )

    def reset(self):
        pass

    def query_position(self) -> Point3D:
        x, y, z, _ = self.query_printer("toolhead=position")["result"]["status"]["toolhead"][
            "position"
        ]
        return x, y, z

    def add_offset(self, x_offset: float = None, y_offset: float = None, z_offset: float = None):
        x, y, z = self.query_position()
        base = "G92"
        if x_offset is not None:
            base += f" X{x + x_offset}"
        if y_offset is not None:
            base += f" Y{y + y_offset}"
        if z_offset is not None:
            base += f" Z{z + z_offset}"

        self.send_gcode(base)

    def wait_for_move_to_finish(self):
        self.send_gcode("M400")

    def send_gcode(self, gcode: str):
        response = requests.post(self.endpoint + "/printer/gcode/script?script=%s" % gcode, auth=self.basic_auth,
                                 verify=False).json()
        match response:
            case {"result": "ok"}:
                return True
            case {"error": {"code": code, "message": message}} if code != 200:
                raise MovementError("Movement Error: %s" % message)
            case d:
                self.log.error("UNKNOWN format: %s", d)
                raise Exception()

    def probe(self) -> float:
        current_position = self.query_position()
        self.send_gcode("PROBE")
        z = self.query_position()[-1]
        self.move_to(*current_position)
        return z

    def query_printer(self, query_string: str) -> dict:
        return requests.post(self.endpoint + "/printer/objects/query?%s" % query_string, auth=self.basic_auth, verify=False).json()

    def move_to(
            self,
            x: float = None,
            y: float = None,
            z: float = None,
            *,
            speed: int | None = None,
    ):
        base = "G90\nG1"
        if x is not None:
            base += f" X{x:.4f}"
        if y is not None:
            base += f" Y{y:.4f}"
        if z is not None:
            base += f" Z{z:.4f}"
        if speed is not None:
            base += f" F{speed}"

        self.log.info("Moving to <%s>", base[6:])

        self.send_gcode(base)
        self.wait_for_move_to_finish()

    def move_rel(
            self,
            x: float = None,
            y: float = None,
            z: float = None,
            *,
            speed: int | None = None,
    ):
        base = "G91\nG1"
        if x is not None:
            base += f" X{x:.4f}"
        if y is not None:
            base += f" Y{y:.4f}"
        if z is not None:
            base += f" Z{z:.4f}"
        if speed is not None:
            base += f" F{speed}"

        self.log.info("Moving by <%s>", base[6:])

        self.send_gcode(base)
        self.wait_for_move_to_finish()

    def home(self):
        self.send_gcode("G28")

    def home_x(self):
        self.send_gcode("G28 X")

    def home_y(self):
        self.send_gcode("G28 Y")

    def home_xy(self):
        self.send_gcode("G28 X Y")

    def home_z(self, x: float, y: float, speed: int | None = None):
        self.move_to(x, y, speed=speed)
        self.send_gcode("G28 Z")

    def get_homed(self) -> tuple[bool, bool, bool]:
        axes = self.query_printer(query_string="toolhead=homed_axes")["result"]["status"]["toolhead"]["homed_axes"]
        x = 'x' in axes
        y = 'y' in axes
        z = 'z' in axes
        return x, y, z

    def get_limits(self) -> Point3D:
        return self.query_printer(query_string="toolhead=axis_maximum")["result"]["status"]["toolhead"]["axis_maximum"][
               :-1]
