from dataclasses import dataclass

import cv2
import numpy as np

from pulsecontrol.helpers import Rectangle
from pulsecontrol.strategies.camera.pcb_camera import PcbCamera


@dataclass(kw_only=True)
class SpcPcbCamera(PcbCamera):
    spc: bool

    @staticmethod
    def get_mask(image: np.ndarray, weakening_factor: float = 1.):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hue = hsv[..., 0]
        hue_vals = (60, 120)
        saturation = hsv[..., 1]
        saturation_values = (5, 55)
        value = hsv[..., 2]
        value_values = (35, 75)

        h = cv2.bitwise_or(cv2.inRange(hue, *hue_vals), cv2.inRange(hue, 0, 0))
        saturation = cv2.inRange(saturation, *saturation_values)
        value = cv2.inRange(value, *value_values)
        return h, saturation, value

    @staticmethod
    def get_approximation(contour):
        return cv2.approxPolyDP(contour, 0.05 * cv2.arcLength(contour, True), True)

    def filter_rectangle(self, rectangle: Rectangle | cv2.typing.RotatedRect) -> bool:
        _, (width, height), angle = rectangle
        ratio = width / height
        area = width * height
        if 0.9 <= ratio <= 1.1:
            if self._area_filter:
                return 70000 < area < 150000
            return True
        return False