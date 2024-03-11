from dataclasses import dataclass

import cv2
import numpy as np

from pulsecontrol.helpers import Rectangle
from pulsecontrol.strategies.camera.pcb_camera import PcbCamera


@dataclass(kw_only=True)
class RectangleCamera(PcbCamera):
    # This is a stub value, only used to let dacite know which camera we selected
    rectangle: bool

    @staticmethod
    def get_mask(image: np.ndarray):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        hue = hsv[..., 0]
        hue_center = 57.5  # 45 <-> 70
        saturation = hsv[..., 1]
        saturation_center = 115  # ~ 80 <-> 150
        value = hsv[..., 2]
        value_center = 120  # 70 <-> 170

        hue = cv2.inRange(hue, hue_center - 12.5, hue_center + 12.5)
        saturation = cv2.inRange(saturation, saturation_center - 35, saturation_center + 35)
        value = cv2.inRange(value, value_center - 50, value_center + 50)
        return hue, saturation, value

    @staticmethod
    def get_approximation(contour):
        return cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)

    @staticmethod
    def filter_rectangle(rectangle: Rectangle) -> bool:
        _, (width, height), angle = rectangle
        if width > height:
            ratio = width / height
        else:
            ratio = height / width

        area = width * height

        if 1.9 <= ratio <= 2.1 and 10000 < area < 600000:
            return True
        return False
