import json
from dataclasses import field, dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from time import sleep

import cv2
import numpy as np
from retry import retry
from pulsecontrol.helpers import Rectangle, Point2D
from pulsecontrol.strategies.camera import CameraStrategies
from pulsecontrol.strategies.camera.probe_camera import ProbeCamera
from pulsecontrol.strategies.control.moonraker import Moonraker
from pulsecontrol.strategies.dut.bam_attack import BamAttack
from pulsecontrol.strategies.dut.esp32 import EspAttack
from pulsecontrol.strategies.integrator import Integrator
from pulsecontrol.strategies.movement import MovementError
from pulsecontrol.strategies.movement.fix_point import FixPoint
from pulsecontrol.strategies.movement.gaussian import Gaussian
from pulsecontrol.strategies.movement.grid import Grid
from pulsecontrol.strategies.movement.http_wrapper import HttpWrapper as MovementWrapper
from pulsecontrol.helpers.results import AttackResults
from pulsecontrol.strategies.injector.chip_shouter import OverheatException


@dataclass
class TmpStore:
    # Offset for movements, measured from chip surface to tip of probe
    movement_offset: float | None = 20
    chip_position: Rectangle | None = None
    abs_chip_position: Point2D | None = None

    def reset(self):
        self.movement_offset = None
        self.chip_position = None
        self.abs_chip_position = None


class SetupState(Enum):
    """
    The state the setup is in
    """

    NOT_READY = -1
    FINDING_CHIP = 0
    WAITING_PROBE_STOW = 1
    FINDING_PROBE = 2
    READY = 3


@dataclass(kw_only=True)
class AdvancedAttacker(Integrator):
    # Cameras
    probe_camera: ProbeCamera
    pcb_camera: CameraStrategies

    # Printer Control
    printer: Moonraker

    # Movement
    movement_strategy: FixPoint | Gaussian | Grid | MovementWrapper

    # Attack implementation and interaction with the DUT
    attack: EspAttack | BamAttack

    chip_position: tuple[np.ndarray, np.ndarray, float] | None = None
    probe_offset_xy: Point2D | None = None

    # Position of the touch probe in relation to the chip-shouter probe
    touch_position: Point2D = field(default_factory=lambda: Point2D(-20.6, -30.7))

    # Height at which to glitch. Relative to the chip surface.
    glitch_height: float
    # Height difference between the probe and the BLTouch device
    probe_height: float
    # Absolute height of chip surface
    chip_surface_height: float | None = None

    _attack_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%dT%H%M%S"))
    _out_path: Path = field(default_factory=Path)

    state: SetupState = SetupState.NOT_READY
    temp_store: TmpStore = field(default_factory=TmpStore)

    def __post_init__(self):
        self._out_path = Path("results", self._attack_date)
        self._out_path.mkdir(parents=True, exist_ok=False)
        # Height of probe when moving onto the chip to avoid hitting cables etc.
        self.temp_store.movement_offset = 15

    def start(
        self,
        skip_init: bool = False,
        target_area: Rectangle | None = None,
        chip_surface_height: float | None = None,
    ):
        """
        Sets AutoPulse up for the attack.

        Args:
            skip_init: Skips image recognition of the chip, probe centering, and homing (if not required) when set
                to true. This option requires the arguments target_chip_position and printer_height to be specified.
            target_area: The targeted position for the attack. This value can be modified, to target only
                specific areas on the chip by modifying the center, width and height.
            chip_surface_height: The absolute height of the chip surface
        """

        if self.state != SetupState.NOT_READY:
            raise ValueError("Device in the wrong state, something went wrong %s", self.state)
        if skip_init:
            if not (target_area and chip_surface_height):
                raise ValueError(
                    "Target chip position and printer height must be provided when using skip_init"
                )

            # Home printer if necessary
            try:
                self.printer.move_rel(z=0.01)
                self.printer.move_rel(z=-0.01)
            except MovementError:
                self.printer.home()

            x_pos = target_area[0][0]
            y_pos = target_area[0][1]
            self.temp_store.abs_chip_position = Point2D(x_pos, y_pos)
            self.chip_position = (
                np.array(target_area[0]),
                np.array(target_area[1]),
                target_area[2],
            )
            self.chip_surface_height = chip_surface_height

            if not (x_pos, y_pos) == self.printer.query_position()[0:2]:
                movement_height = (
                    chip_surface_height + self.probe_height + self.temp_store.movement_offset
                )
                self.printer.move_to(movement_height)
                self.printer.move_to(x_pos, y_pos)

        else:
            self.survey_position()
            # Gets the probe offset and adjusts the final chip position by that amount
            self.finalize_setup()

        self.state = SetupState.WAITING_PROBE_STOW
        self.log.info(
            "=====================================\n"
            "Tilt the BLTouch out of the way!\n"
            "Then call /continue to start the attack.\n"
            "====================================="
        )

    def continue_experiment(self):
        # move just over the chip
        self.printer.move_to(z=(self.chip_surface_height + self.glitch_height))
        successes: list[AttackResults] = []
        # Test Loop
        at_position = 0
        first_loop = True
        try:
            while True and not self._stop_request:
                while True and not self._stop_request:
                    # The interface has to move on the first call
                    next_chip_coordinates = Point2D(0.0, 0.0)
                    world_coords = (0, 0)
                    if first_loop or self.attack.move():
                        try:
                            next_chip_coordinates: Point2D = next(self.movement_strategy)
                            self.log.info(f"Next coordinates: {next_chip_coordinates:.3f}")
                        except StopIteration:
                            self.log.warning("End of movement reached")
                            break

                        world_coords: tuple[float, float] = tuple(
                            self.chip_point_to_world(np.asarray(next_chip_coordinates.to_tuple()))
                        )
                        self.printer.move_to(*world_coords)
                        at_position = at_position + 1
                        first_loop = False
                        self.log.info("I'm at position %s", at_position)

                    # the chipwhisperer doing the attacking
                    self.attack_with_wiggle()
                    # getting results
                    successes.append(
                        AttackResults(
                            next_chip_coordinates.to_tuple(),
                            world_coords,
                            at_position,
                            results=self.attack.check_results(),
                        )
                    )
                at_position = 0
                self.movement_strategy.reset()
                self.attack.update()
        finally:
            with open(Path(self._out_path, "glitches.json"), "w") as results:
                json.dump(successes, results, indent=2, default=asdict)

            self.reset()
            self.log.info("Attack finished")

    def reset(self):
        self.state = SetupState.NOT_READY
        for i in self.__dict__.values():
            try:
                i.reset()
            except AttributeError:
                pass
        super().reset()

    def get_probe_center(self) -> Point2D:
        """
        Moves the probe to the probe camera and takes a picture.
        Then calculates the probe offset in regard to the probe mount, this accounts for
        slightly crooked probes.
        """

        def retry_circle():
            for _ in range(4):
                try:
                    return self.probe_camera.get_coordinate()
                except Exception as e:
                    self.log.error(e)
            raise ValueError("Could not find probe center")

        # adjust (get) to the offset between the probe and the probe mount port in the XY plane
        self.printer.move_to(x=10, y=0, speed=3000)
        self.printer.move_to(x=2, z=self.probe_camera.get_focus().at, speed=1000)
        # Don't set the offset yet, other coordinates will get more complicated otherwise
        # Turn on the light
        self.printer.send_gcode("SET_LED LED=probe_led WHITE=1")
        try:
            center = retry_circle()
        finally:
            # Turn off light
            self.printer.send_gcode("SET_LED LED=probe_led WHITE=0")
        return center

    def get_rectangle(self, autofocus: bool) -> Rectangle:
        self.pcb_camera.set_autofocus(autofocus)
        # Turn on light
        self.printer.send_gcode("SET_LED LED=chip_led WHITE=0.1")
        rectangles = None
        for _ in range(3):
            try:
                rectangles = next(self.pcb_camera.get_coordinate())
            except StopIteration:
                ...
            else:
                break
        self.printer.send_gcode("SET_LED LED=chip_led WHITE=0")
        if rectangles is not None:
            return rectangles
        raise ValueError("Couldn't find rectangle")

    def calculate_chip_offset(
        self, rectangle_center: Point2D, distance_factor: float = 1.0
    ) -> Point2D:
        """
        Calculate the distance to the chip in the XY plane.
        The `distance_factor` is required during the first phase, because the z-distance to the chip is unknown,
        but always less than the calibrated value at that point.

        Args:
            rectangle_center: The center of the chip in the image.
            distance_factor: The factor to multiply the distance with.

        Returns:
            The distance to the chip in the XY plane

        """
        self.log.info("Converting location: %s", rectangle_center)
        non_normalized_distance = rectangle_center - self.pcb_camera.get_resolution() / 2
        distance = self.pcb_camera.normalize_distance(non_normalized_distance)
        factored = distance * distance_factor
        self.log.info("non_normalized_distance: %s", non_normalized_distance)
        self.log.info("distance: %s", distance)
        self.log.info("factored distance: %s", factored)
        return factored

    def chip_point_to_world(self, point: np.ndarray) -> tuple[float, float]:
        """
        The input point represents a fraction in which 1 is the width, height of the chip and 0, 0
        the upper left corner.
        """
        center, size, angle = self.chip_position
        rotation = cv2.getRotationMatrix2D(center, -angle, 1)

        # Scale the point up to the size of the chip
        point *= size
        # shift the points to be centered around the chip
        point = point + center - size / 2

        # rotate
        rotated = cv2.transform(np.array([[point]]), rotation)[0][0]
        # noinspection PyTypeChecker
        return tuple(rotated)

    def find_chip(self) -> Rectangle:
        # get max values for all axes
        max_axes: Point2D = Point2D(*self.printer.get_limits()[:-1])

        # Move PCB Camera to the center to get the best image
        # This position is relative to the chipshouter mount-point, not the varying probe center
        self.printer.move_to(z=60)
        # Move to center, makes seeing the camera offset easier
        self.printer.move_to(*(max_axes / 2), speed=3000)
        # Center the camera on the build plate
        self.printer.move_rel(*(self.pcb_camera.camera_position * -1), speed=3000)
        self.printer.move_to(z=self.pcb_camera.get_focus().at)

        ##################################
        # take the image and find the IC.
        # The position won't be quite right yet,
        # because we don't know the exact distance to the chip
        # The solution is to move to a fixed distance to the chip,
        # then doing the edge detection again.
        # For this to work, the z axis needs to be homed to the height of the chip
        center = self.get_rectangle(True)[0]
        distance = self.calculate_chip_offset(Point2D(*center), 0.655)

        # move the touch probe to the position of the probe
        self.printer.move_rel(*(self.pcb_camera.get_camera_position() - self.touch_position))

        # move the touch probe to the approximate chip position
        self.printer.move_rel(*distance)

        height = self.printer.probe()
        self.log.info(f"Probed chip height: {height:.2f}")
        # Default offset between the probe and the BLTouch is 2.4mm
        # We need to set this here, because we override the offset from the `printer.cfg` with this.
        height -= 2.4

        # Set the offset
        # This overrides the default 0 position of the system.
        # Everything is relative to the height of the chip now
        self.printer.add_offset(z_offset=-height)

        # Move camera back over chip, centered this time and with the correct distance
        self.printer.move_rel(*(self.touch_position - self.pcb_camera.get_camera_position()))
        self.printer.move_to(z=self.pcb_camera.get_focus().at)
        # Use autofocus, we don't really need fixed focus at this wide of an angle
        chip_position = self.get_rectangle(True)
        self.log.info(f"Found final chip position: {chip_position}")
        with open(Path(self._out_path, "rectangle.json"), "w") as results:
            json.dump([center, chip_position], results)

        return chip_position

    def find_probe_center(self) -> Point2D:
        # Calculate the probe offset
        # Moves the printer, updates the offset value
        sleep(5)
        return self.get_probe_center()

    def survey_position(self):
        if self.state != SetupState.NOT_READY:
            raise ValueError("Device already initialized, call `reset` first!")

        self.log.info("Starting survey function")
        # home axes
        self.printer.home()

        # Use the camera to find the chip location and size
        self.temp_store.chip_position = self.find_chip()

        # Move the probe back to the approximate chip center
        self.printer.move_rel(*self.pcb_camera.get_camera_position())
        # Get current position
        self.temp_store.abs_chip_position = Point2D.from_iter(self.printer.query_position()[:-1])
        # position of the chip center
        distance = self.calculate_chip_offset(Point2D.from_iter(self.temp_store.chip_position[0]))
        self.temp_store.abs_chip_position -= distance
        # move to the new center
        self.printer.move_to(*self.temp_store.abs_chip_position)
        self.state = SetupState.WAITING_PROBE_STOW

    def finalize_setup(self):
        if not self.state.WAITING_PROBE_STOW:
            raise ValueError("Not in the correct state, the device needs to be initialized first!")
        self.state = SetupState.FINDING_PROBE

        self.probe_offset_xy = self.find_probe_center()
        self.log.info(f"Probe position: {self.probe_offset_xy:.2f}")

        # Add probe offset
        # Different direction, because the camera is mounted upside down
        self.temp_store.abs_chip_position -= self.probe_offset_xy

        # Calculate the chip position and size in world coordinates, including the probe offset
        self.log.info(f"The chip is at position {self.temp_store.abs_chip_position:.2f}")
        self.chip_position = (
            np.asarray((*self.temp_store.abs_chip_position,)),
            np.asarray(self.temp_store.chip_position[1]) * self.pcb_camera.get_focus().pixel_size,
            self.temp_store.chip_position[2],
        )
        self.log.info(f"Final chip rectangle: {self.chip_position}")

        self.printer.move_to(*self.temp_store.abs_chip_position)

        self.printer.move_to(z=10)

        self.state = SetupState.READY

    @retry(OverheatException, tries=3, delay=1, backoff=2)
    def attack_with_wiggle(self):
        try:
            self.attack.start()
        except OverheatException:
            self.log.error("Overheat detected, resetting")
            self.sleep_and_wiggle()
            raise

    def sleep_and_wiggle(self):
        sleep(10)
        # we need to move the printer a bit so the steppers don't shut down after all the sleeps
        self.printer.move_rel(z=1)
        self.printer.move_rel(z=-1)
