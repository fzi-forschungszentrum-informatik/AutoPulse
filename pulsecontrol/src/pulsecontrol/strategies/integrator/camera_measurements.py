from dataclasses import dataclass
from datetime import datetime
from time import sleep

import cv2
import numpy as np

from pulsecontrol.helpers import HasLogger, Point2D
from pulsecontrol.strategies.camera import RectangleCamera
from pulsecontrol.strategies.camera.http_wrapper import HttpWrapperLocal as CameraWrapper
from pulsecontrol.strategies.control.moonraker import Moonraker
from pulsecontrol.strategies.integrator import Integrator
from pulsecontrol.strategies.movement.fix_point import FixPoint
from pulsecontrol.strategies.movement.gaussian import Gaussian

# Approximate location of the rectangles
# Measured by moving the carriage manually
APPROX_RECT_SMALL = (247.00, 147)
APPROX_RECT_LARGE = (140.00, 99)


def to_image(name: str, image: np.ndarray):
    _, buffer = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_OPTIMIZE, 1, cv2.IMWRITE_JPEG_PROGRESSIVE, 1]
    )
    with open(name + ".jpg", "wb") as outfile:
        outfile.write(buffer.tobytes())


@dataclass(kw_only=True)
class CameraMeasurements(Integrator, HasLogger):
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

    # filename prefix
    file_prefix: str

    # Printer Control
    printer: Moonraker

    # Camera
    pcb_camera: CameraWrapper | RectangleCamera
    # pcb_camera: CameraWrapper

    # Approx. Rectangle position
    approx_center: Point2D

    # Used if the mode is `move around`
    movement: Gaussian | FixPoint

    def start(self):
        self.init_printer()
        self.pcb_camera.set_autofocus(False)
        self.log.info(f"Approx center: {self.approx_center}")

        # Test Loop
        for test_counter, point in enumerate(self.movement):
            self.log.info(f"Next Point: {point}")
            # only a call to `/reset` can stop the test
            if self._stop_request:
                break

            self.printer.move_to(*(self.approx_center - point))
            sleep(1)

            #########################
            # 4. take picture, find center
            image = self.pcb_camera.get_image()
            name = f'test/data/camera/{self.file_prefix}-{test_counter}-{datetime.now().strftime("%Y-%m-%dT%H%M%S")}'
            np.save(name, image)
            to_image(name, image)

            # rectangle = next(self.pcb_camera.get_coordinate())[0]
            # relative = rectangle - self.pcb_camera.resolution / 2
            # # this value is in pixels, not in mm, so it needs to be converted
            # final_distance = relative * self.pcb_camera.size_per_pixel_at_focus_distance
            # self.log.info(
            #     f'final value on test ({test_counter}): {rectangle:.4f}, relative: {relative:.4f}, final distance: {final_distance:.4f}'
            # )

            sleep(0.5)

        if self._stop_request:
            self.log.info("Stopping due to reset, not done with the test!")
        else:
            self.log.info("Stopping...")

    def init_printer(self):
        self.log.info("Starting survey function")
        # home axes
        self.printer.home()
        # best focus distance for the camera
        self.printer.move_to(*self.approx_center, z=self.pcb_camera.get_focus().at)
