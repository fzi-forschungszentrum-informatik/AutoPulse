from dataclasses import dataclass

import cv2
import numpy as np

from pulsecontrol.helpers import Rectangle
from pulsecontrol.strategies.camera.pcb_camera import PcbCamera


@dataclass(kw_only=True)
class SimplePcbCamera(PcbCamera):
    simple: bool

    @staticmethod
    def get_mask(image: np.ndarray):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        hue = hsv[..., 0]
        hue_vals = (80, 110)
        saturation = hsv[..., 1]
        saturation_values = (190, 250)
        value = hsv[..., 2]
        value_values = (45, 85)

        hue = cv2.inRange(hue, *hue_vals)
        saturation = cv2.inRange(saturation, *saturation_values)
        value = cv2.inRange(value, *value_values)
        return hue, saturation, value

    @staticmethod
    def get_approximation(contour):
        return cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)

    def filter_rectangle(self, rectangle: Rectangle) -> bool:
        _, (width, height), angle = rectangle
        ratio = width / height
        area = width * height
        if 0.80 <= ratio <= 1.2:
            if area > 1000:
                return True
        return False
