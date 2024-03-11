from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path
from time import sleep

from tqdm import tqdm

from pulsecontrol.helpers import HasLogger
from pulsecontrol.strategies.control.moonraker import Moonraker
from pulsecontrol.strategies.integrator import Integrator
from pulsecontrol.strategies.movement.alternating import Alternating
from pulsecontrol.strategies.movement.homing_mode import HomingMode
from pulsecontrol.strategies.movement.tiny_stepps import TinySteps
from pulsecontrol.strategies.dut.glass_watch import GlassWatch


@dataclass(kw_only=True)
class PhysicalMeasurements(Integrator, HasLogger):
    def reset(self):
        super().reset()
        for thing in self.__dict__.values():
            try:
                thing.reset()
            except AttributeError:
                pass
            else:
                self.log.info("Stopped (%s)", thing.__class__)

    # Short description of the nature of the test
    description: str = ""

    # The z height at which the test is supposed to take place
    height: float

    # Printer Control
    printer: Moonraker

    # Movement
    movement_strategy: Alternating | TinySteps | HomingMode

    # Basic Uart interface
    interface: GlassWatch

    def start(self):
        self.init_printer()
        try:
            relative_mode = self.movement_strategy.relative_mode
        except AttributeError:
            relative_mode = False

        # Test Loop
        self.log.info(
            "About %s movements will be performed",
            self.movement_strategy.total_movements,
        )
        positions = []
        for point in tqdm(self.movement_strategy, total=self.movement_strategy.total_movements):
            if self._stop_request:
                break
            if relative_mode:
                self.printer.move_rel(*point, speed=400)
            else:
                # Home if the requested value is almost 0
                if abs(point.x) < 0.001:
                    self.printer.home_x()
                else:
                    self.printer.move_to(*point, speed=400)

            if self.movement_strategy.is_injection_location():
                positions.append(point.x)
                # this requests and logs the current position
                self.interface.start()

        if self._stop_request:
            self.log.info("Stopping due to reset, not done with the test!")
        else:
            self.log.info("Stopping...")

        rel = "rel" if relative_mode else "abs"
        step_back = "step_back" if self.movement_strategy.move_back_mode else "direct"
        file_name = f'data/{rel}_{step_back}_{self.movement_strategy.step_size}.csv'
        Path(file_name).parent.mkdir(parents=True, exist_ok=True)
        with open(file_name, 'w') as out_dump:
            out_dump.write('"movement","measured"\n')
            for point, measured in zip_longest(positions, self.interface.data, fillvalue='#'):
                out_dump.write(f'\"{point}","{measured}"\n')

    def init_printer(self):
        self._stop_request = False
        self.log.info("Starting survey function")
        # home axes
        if self.printer.get_homed() != (True, True, True):
            raise ValueError('You need to manually home the printer, due to the fixed attachment of the glass rod.')
        self.printer.move_to(*self.movement_strategy.start_position, speed=300)
        self.printer.move_to(z=self.height)
        sleep(15)
