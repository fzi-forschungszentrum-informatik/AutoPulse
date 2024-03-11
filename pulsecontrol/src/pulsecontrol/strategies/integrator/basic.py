import json
from dataclasses import field, dataclass
from datetime import datetime
from pathlib import Path
from time import sleep

import cv2
import numpy as np
from chipshouter.com_tools import Firmware_State_Exception

from pulsecontrol.helpers import Rectangle, Point2D
from pulsecontrol.strategies.camera import CameraStrategies
from pulsecontrol.strategies.camera.http_wrapper import (
    HttpWrapperLocal as CameraWrapper,
)
from pulsecontrol.strategies.control.moonraker import Moonraker
from pulsecontrol.strategies.dut.basic_uart import BasicUart
from pulsecontrol.strategies.dut.simple_target import SimpleTarget
from pulsecontrol.strategies.injector.chip_shouter import ChipShouter
from pulsecontrol.strategies.integrator import Integrator
from pulsecontrol.strategies.movement.fix_point import FixPoint
from pulsecontrol.strategies.movement.gaussian import Gaussian
from pulsecontrol.strategies.movement.grid import Grid
from pulsecontrol.strategies.movement.http_wrapper import HttpWrapper as MovementWrapper

DEBUG = False


@dataclass(kw_only=True)
class Basic(Integrator):
    # Cameras
    # They are the only devices that should be on the other PI
    probe_camera: CameraWrapper
    pcb_camera: CameraStrategies

    # Printer Control
    printer: Moonraker

    # ChipShouter
    chipshouter: ChipShouter

    # Movement
    movement_strategy: FixPoint | Gaussian | Grid | MovementWrapper

    # Basic Uart interface
    interface: BasicUart | SimpleTarget
    # # Logging tool
    # file_logger: FileLogger

    chip_position: tuple[np.ndarray, np.ndarray, float] = field(init=False)
    probe_offset_xy: Point2D = field(init=False)

    # Position of the touch probe in relation to the chip-shouter probe
    touch_position: Point2D = field(default_factory=lambda: Point2D(-20.6, -30.7))

    # Height at which to glitch. Relative to the chip surface.
    glitch_height: float
    # Height difference between the probe and the BLTouch device
    probe_height: float

    _attack_date: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%dT%H%M%S")
    )
    _out_path: Path = field(init=False)

    def __post_init__(self):
        self._out_path = Path("results", self._attack_date)
        self._out_path.mkdir(parents=True, exist_ok=False)

    def start(self):
        if not DEBUG:
            self.survey_position()
        else:
            self.chip_position = (
                np.array([134.19, 117.16]),
                np.array([6.15, 6.48]),
                0.3558,
            )

        # move just over the chip
        self.printer.move_to(z=self.glitch_height)
        self.printer.move_rel(z=-self.probe_height)
        try:
            self.chipshouter.arm()
        except Firmware_State_Exception:
            ...
        else:
            sleep(1)

        self.interface.start()

        success_map: list[
            tuple[tuple[float, float], tuple[float, float], list[str]]
        ] = []
        # Test Loop
        at_position = 0
        while True and not self._stop_request:
            print(at_position)
            # The interface has to move on the first call
            if self.interface.move():
                at_position = 0
                try:
                    next_chip_coordinates: Point2D = next(self.movement_strategy)
                    self.log.info(f"Next coordinates: {next_chip_coordinates:.3f}")
                except StopIteration:
                    self.log.warning("End of movement reached")
                    break

                world_coords = tuple(
                    self.chip_point_to_world(
                        np.asarray(next_chip_coordinates.to_tuple())
                    )
                )
                success_map.append((next_chip_coordinates.to_tuple(), world_coords, []))
                self.printer.move_to(*world_coords)
            at_position += 1

            self.interface.start()
            self.chipshouter.inject(1)
            sleep(1)
            result = self.interface.check_success()
            print(result)
            success_map[-1][2].append(result.name)

        self.chipshouter.disarm()
        with open(Path(self._out_path, "glitches.json"), "w") as results:
            json.dump(success_map, results)

    def reset(self):
        self.chipshouter.disarm()
        super().reset()

    def get_probe_center(self) -> Point2D:
        """
        Moves the probe to the probe camera and takes a picture.
        Then calculates the probe offset in regard to the probe mount, this accounts for
        slightly crooked probes.
        """

        def retry_circle():
            for _ in range(3):
                try:
                    return self.probe_camera.get_coordinate()
                except Exception as e:
                    self.log.error(e)
            raise ValueError("Could not find probe center")

        # adjust (get) to the offset between the probe and the probe mount port in the XY plane
        self.printer.move_to(x=10, y=10, speed=3000)
        self.printer.move_to(
            x=0, y=0, z=self.probe_camera.get_min_focus_distance(), speed=1000
        )
        # Don't set the offset yet, other coordinates will get more complicated otherwise
        # Turn on the light
        self.printer.send_gcode("SET_LED LED=probe_led WHITE=1")
        center = retry_circle()
        # Turn off light
        self.printer.send_gcode("SET_LED LED=probe_led WHITE=0")
        return center

    def get_rectangle(self, autofocus: bool) -> Rectangle:
        self.pcb_camera.set_autofocus(autofocus)
        for _ in range(3):
            try:
                rectangles = next(self.pcb_camera.get_coordinate())
            except StopIteration:
                ...
            else:
                return rectangles
        raise ValueError("Couldn't find rectangle")

    def calculate_chip_offset(self, rectangle_center: Point2D) -> Point2D:
        self.log.info("Converting location: %s", rectangle_center)
        non_normalized_distance = (
            rectangle_center - self.pcb_camera.get_resolution() / 2
        )
        distance = self.pcb_camera.normalize_distance(non_normalized_distance)
        self.log.info("non_normalized_distance: %s", non_normalized_distance)
        self.log.info("distance: %s", distance)
        return distance

    def chip_point_to_world(self, point: np.ndarray) -> np.ndarray:
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
        return rotated

    def survey_position(self):
        self.log.info("Starting survey function")
        # get max values for all axes
        max_axes: Point2D = Point2D(*self.printer.get_limits()[:-1])

        # home axes
        self.printer.home()
        # clearance for move
        self.printer.move_rel(z=30)

        # Moves the printer, updates the offset value
        if not DEBUG:
            self.probe_offset_xy = self.get_probe_center()
        else:
            self.probe_offset_xy = Point2D(1.03, -1.79)
        self.log.info(f"Probe position: {self.probe_offset_xy:.2f}")

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
        if not DEBUG:
            center = self.get_rectangle(True)[0]
            self.log.info(f"Rectangle for the approximate location: {center}")
            distance = self.calculate_chip_offset(Point2D(*center))
        else:
            center = ((0, 0), (0, 0), 0)
            distance = Point2D(3.195, -4.146)
        self.printer.move_rel(*distance)

        # move the touch probe in position
        self.printer.move_rel(
            *(self.pcb_camera.get_camera_position() - self.touch_position)
        )
        height = self.printer.probe()
        self.log.info(f"Probed chip height: {height:.2f}")
        # The offset contains the offset from the print config as well, so we need to add that
        height -= 2.4
        self.printer.add_offset(z_offset=-height)

        # Move camera back over chip, centered this time and with the correct distance
        self.printer.move_rel(
            *(self.touch_position - self.pcb_camera.get_camera_position())
        )
        self.printer.move_to(z=self.pcb_camera.get_focus().at)
        chip_position = self.get_rectangle(False)
        self.log.info(f"Found final chip position: {chip_position}")
        with open(Path(self._out_path, "rectangle.json"), "w") as results:
            json.dump([center, chip_position], results)

        # Move the probe back to the approximate chip center
        self.printer.move_rel(*self.pcb_camera.get_camera_position())
        # Get current position
        abs_chip_position = Point2D.from_iter(self.printer.query_position()[:-1])
        # position of the chip center
        distance = self.calculate_chip_offset(Point2D.from_iter(chip_position[0]))
        abs_chip_position += distance
        # move to the new center
        self.printer.move_to(*abs_chip_position)
        sleep(1)
        # Add probe offset
        abs_chip_position += self.probe_offset_xy

        # Calculate the chip position and size in world coordinates, including the probe offset
        self.log.info(f"The chip is at position {abs_chip_position:.2f}")
        self.chip_position = (
            np.asarray((*abs_chip_position,)),
            np.asarray(chip_position[1])
            * self.pcb_camera.get_focus().pixel_size,
            chip_position[2],
        )
        self.log.info(f"Final chip rectangle: {self.chip_position}")

        self.printer.move_to(*abs_chip_position)
        self.printer.move_to(z=10)
