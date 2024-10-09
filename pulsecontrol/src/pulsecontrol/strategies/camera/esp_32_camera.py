from dataclasses import dataclass

import cv2
import numpy as np

from pulsecontrol.helpers import Rectangle
from pulsecontrol.strategies.camera.pcb_camera import PcbCamera


@dataclass(kw_only=True)
class ESPPcbCamera(PcbCamera):
    # This flag is required to let dacite know which class to load
    esp32: bool

    @staticmethod
    def get_mask(image: np.ndarray, weakening_factor: float = 1.0):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hue = hsv[..., 0]
        hue_vals = (60, 120)
        saturation = hsv[..., 1]
        saturation_values = (50, 180)
        value = hsv[..., 2]
        value_values = (0, 250)

        h = cv2.inRange(hue, *hue_vals)
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
                # if area größer 100 print
                return 10000 < area < 45000
                # return area > 100
            return True
        return False
