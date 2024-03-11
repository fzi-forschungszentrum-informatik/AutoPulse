from dataclasses import dataclass, field
from enum import Enum

import cv2
import numpy as np

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.camera.strategy import PiCameraWrapper

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import logging
    from unittest.mock import MagicMock

    logging.error("RPi Module not installed, this is OK if not executed on a pi.")
    # This is a stub which allows us to run the code in environments without the picamera module
    GPIO = MagicMock()


class Probe(Enum):
    LARGE = 4
    SMALL = 1


@dataclass(kw_only=True)
class ProbeCamera(PiCameraWrapper):
    """
    STL measured centers
    Nozzle:
        x: 173.289
        y: -59.238

    Shouter Mount-point:
        x: 164.23
        y: -65.81

    Delta:
        x: 9.059 mm
        y: 6.572 mm
    """

    """
    The real position of the center pixel in relation to the probe
    got this from gimp:

    Mount (measured at z=-20 without the probe attached):
        dist: 923 px
        measured: 26.1 mm
        => 0.028277 mm/px

    Probe:

    Delta:
    """
    image_rotation: int | None = cv2.ROTATE_90_CLOCKWISE
    calibrated_center: Point2D = field(default_factory=lambda: Point2D(1220, 2304))

    # Parameters for cropping to the probe
    crop_upper_edge: Point2D = field(default_factory=lambda: Point2D(900, 2000))
    crop_width: int = 650

    probe_type: Probe

    def crop_image(self, image):
        return image[
               self.crop_upper_edge.y: self.crop_upper_edge.y + self.crop_width,
               self.crop_upper_edge.x: self.crop_upper_edge.x + self.crop_width,
               ...,
               ]

    @staticmethod
    def preprocess_image(image):
        blurred = cv2.GaussianBlur(image, (7, 7), 0)
        hue: np.ndarray = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)[..., 0]
        my_range: np.ndarray = cv2.inRange(hue, 35, 80)

        kernel = np.ones((3, 3), np.uint8)
        return cv2.morphologyEx(my_range, cv2.MORPH_OPEN, kernel)

    def get_best_circle(self, image) -> tuple[int, int]:
        match self.probe_type:
            case Probe.SMALL:
                self.log.info("Using small probe parameters")
                params = dict(
                    dp=2,
                    minDist=1,
                    param1=255,
                    param2=38,
                    maxRadius=80,
                    minRadius=10,
                )
            case Probe.LARGE:
                self.log.info("Using large probe parameters")
                params = dict(
                    dp=1.7,
                    minDist=1,
                    param1=255,
                    param2=40,
                    maxRadius=100,
                    minRadius=50,
                )
            case x:
                raise ValueError("Unknown probe type, %s" % x)

        circles = cv2.HoughCircles(image, cv2.HOUGH_GRADIENT, **params)
        if circles is not None:
            # round to pixel values
            circles = np.uint16(np.around(circles))
            no_radius = circles[0, ..., 0:-1]
            point = np.around(np.average(no_radius, axis=0)).astype(np.uint16)
            return point
        else:
            raise ValueError("No circles found, please double check the image parameters")

    def normalize_distance(self, difference: Point2D) -> Point2D:
        """
        Converts the center position of the chip from camera coordinates to the distance
        from the current position.
        Add this to the current position to get the resulting pcb center in the machines coordinates
        """
        # swap and invert axis
        # TODO is this still needed after the image rotation?
        # temp = difference.x
        # difference.x = difference.y
        # difference.y = temp * -1
        # difference *= -1

        distance_from_camera_position = difference * self.focus.pixel_size
        return distance_from_camera_position

    def get_coordinate(self) -> Point2D:
        image = self.get_image()
        image = self.crop_image(image)
        image = self.preprocess_image(image)
        point = Point2D.from_iter(self.get_best_circle(image))
        self.log.info(f"Got point: {point:.2f}")

        point += self.crop_upper_edge
        self.log.info(f"In image coordinates: {point:.2f}")
        difference = point - self.calibrated_center
        self.log.info(f"As offset: {difference:.2f}")
        # return Point2D(2.5093, 1.2656)  # Hand measured
        normalized = self.normalize_distance(difference)
        self.log.info(f"Normalized: {normalized:.2f}")
        return normalized
