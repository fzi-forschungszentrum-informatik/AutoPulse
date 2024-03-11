from dataclasses import dataclass

import cv2
import numpy as np

from pulsecontrol.strategies.camera.pcb_camera import PcbCamera


@dataclass(kw_only=True)
class GenericPcbCamera(PcbCamera):
    generic: bool

    @staticmethod
    def get_mask(image: np.ndarray):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        hue = hsv[..., 0]
        hue_center = 90  # 178 / 2  # from gimp, out of 360
        saturation = hsv[..., 1]
        saturation_center = 56  # 23 * 255 / 100  # between 17 and 25 out of 100 in gimp
        value = hsv[..., 2]
        value_center = 63  # 25 * 255 / 100  # 20-30

        hue = cv2.inRange(hue, hue_center - 10, hue_center + 6)
        saturation = cv2.inRange(saturation, saturation_center - 12, saturation_center + 12)
        value = cv2.inRange(value, value_center - 10, value_center + 10)
        return hue, saturation, value

    @staticmethod
    def get_approximation(contour):
        return cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
