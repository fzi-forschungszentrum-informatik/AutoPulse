from abc import ABC, abstractmethod
from dataclasses import dataclass, field, InitVar
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Iterable, Optional

import cv2
import numpy as np

from pulsecontrol.helpers import Point2D, Rectangle, HasLogger
from pulsecontrol.strategies import Strategy

try:
    from picamera2 import Picamera2
    from libcamera import controls
except ModuleNotFoundError:
    import logging
    from unittest.mock import MagicMock

    logging.error("Picamera Module not installed, this is OK if not executed on a pi.")
    # This is a stub which allows us to run the code in environments without the picamera module
    Picamera2 = MagicMock()


def to_image(name: Path, image: np.ndarray):
    name.parent.mkdir(parents=True, exist_ok=True)
    # Path(os.path.dirname(name)).mkdir(parents=True, exist_ok=True)
    _, buffer = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_OPTIMIZE, 1, cv2.IMWRITE_JPEG_PROGRESSIVE, 1]
    )
    with open(name, "wb") as outfile:
        outfile.write(buffer.tobytes())


@dataclass(kw_only=True)
class Focus:
    """
    Focus settings for the camera.
    """

    """
    The physical position of the printer end-effector, relative to the z-endstop.
    """
    at: float

    """
    Size of one pixel at this focus distance in millimeter. 
    Has to be manually measured using a reference image at the specified focus distance. 
    In mm/px.
    """
    pixel_size: float

    """
    The libcamera lens position for the focus distance. Not required when using autofocus.
    """
    lens_position: int | None = None


@dataclass(kw_only=True)
class Calibration:
    """
    Stores the calibration matrix and dist-coefficients
    """
    matrix_path: InitVar[Path]
    distortion_coefficients_path: InitVar[Path]

    matrix: np.ndarray = field(init=False)
    distortion_coefficients: np.ndarray = field(init=False)

    def __post_init__(self, matrix_path: Path, distortion_coefficients_path: Path):
        self.matrix = np.load(matrix_path)
        self.distortion_coefficients = np.load(distortion_coefficients_path)


@dataclass(kw_only=True)
class CameraStrategy(Strategy, ABC):
    strategy: str = "camera"

    # Position of the Camera relative to the mount-point of the chipshouter probe
    camera_position: Point2D | None = None
    focus: Focus = None

    # enable or disable autofocus
    _autofocus: bool = False
    _area_filter: bool = True

    def normalize_distance(self, difference: Point2D) -> Point2D:
        """
        Converts the center position of the chip from camera coordinates to the distance
        from the current position.
        Add this to the current position to get the resulting pcb center in the machines coordinates
        """
        difference.y *= -1
        distance_from_camera_position = difference * self.focus.pixel_size
        return distance_from_camera_position

    @abstractmethod
    def get_coordinate(self) -> Point2D | Iterable[Rectangle]:
        raise NotImplementedError()

    @staticmethod
    def encode_image(image: np.ndarray) -> np.ndarray:
        _, buffer = cv2.imencode(
            ".jpg",
            image,
            [cv2.IMWRITE_JPEG_OPTIMIZE, 1, cv2.IMWRITE_JPEG_PROGRESSIVE, 1],
        )
        return buffer

    @abstractmethod
    def get_image(self) -> np.ndarray:
        raise NotImplementedError()

    def get_camera_position(self) -> Point2D | None:
        return self.camera_position

    def get_focus(self) -> Focus:
        return self.focus

    def get_resolution(self) -> Point2D:
        raise NotImplementedError()

    def get_autofocus(self) -> bool:
        return self._autofocus

    def set_autofocus(self, val: bool):
        self._autofocus = val


@dataclass(kw_only=True)
class PiCameraWrapper(CameraStrategy, HasLogger, ABC):
    _camera: Optional[Picamera2] = field(init=True, repr=False, default=None)
    image_rotation: int | None = None
    index: int = 0

    calibration: Calibration | None = None

    @property
    def camera(self) -> Picamera2:
        if self._camera is None:
            self._camera = Picamera2(camera_num=self.index)
            match self.image_rotation:
                case cv2.ROTATE_90_CLOCKWISE | cv2.ROTATE_90_COUNTERCLOCKWISE:
                    res = self.get_resolution()[1], self.get_resolution()[0]
                case _:
                    res = self.get_resolution()
            camera_config = self._camera.create_still_configuration(
                main=dict(size=(*res,), format="RGB888"),
                buffer_count=1,
            )
            self._camera.configure(camera_config)
        return self._camera

    def rotate_image(self, image: np.ndarray) -> np.ndarray:
        return cv2.rotate(image, self.image_rotation)

    def get_image(self) -> np.ndarray:
        self.log.info("This is the thing that was called: %s", self.__class__.__name__)
        self.camera.start(show_preview=False)
        self.log.info("Setting controls")
        if not self.get_autofocus():
            self.log.info("Manual Focus mode enabled")
            self.camera.set_controls(
                dict(AfMode=controls.AfModeEnum.Manual, LensPosition=self.focus.lens_position))
            sleep(2)
            self.log.info("Slept for a moment")
        else:
            self.log.info("Autofocus enabled")
            self.camera.set_controls(
                dict(AfMode=controls.AfModeEnum.Auto, AfRange=controls.AfRangeEnum.Macro)
            )
            self.log.info("Waiting for focus")
            focused = self.camera.autofocus_cycle()
            self.log.info(f"Autofocus success: {focused}")
        image = self.camera.capture_array("main")
        if self.calibration:
            image = cv2.undistort(image, self.calibration.matrix, self.calibration.distortion_coefficients, None)
        self.camera.stop()
        # to_image(Path("results/", datetime.now().strftime("%Y-%m-%dT%H%M%S-pre-rot.jpg")), image)
        self.log.info("The Image rotation is: %s", self.image_rotation)
        if self.image_rotation is not None:
            image = self.rotate_image(image)
        to_image(Path("results/", datetime.now().strftime("%Y-%m-%dT%H%M%S.jpg")), image)
        return image

    def reset(self):
        if self._camera is not None:
            self._camera.stop()
        self._camera = None

    def get_resolution(self) -> Point2D:
        match self.image_rotation:
            case cv2.ROTATE_90_CLOCKWISE | cv2.ROTATE_90_COUNTERCLOCKWISE:
                return Point2D(2592, 4608)
            case _:
                return Point2D(4608, 2592)
