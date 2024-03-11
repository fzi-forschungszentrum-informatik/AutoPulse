from dataclasses import dataclass

import cv2
import numpy as np

from pulsecontrol.helpers import Rectangle
from pulsecontrol.strategies.camera.pcb_camera import PcbCamera


@dataclass(kw_only=True)
class NxpPcbCamera(PcbCamera):
    nxp: bool

    @staticmethod
    def get_mask(image: np.ndarray):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        hue = hsv[..., 0]
        hue_center = 110
        saturation = hsv[..., 1]
        saturation_center = 50
        value = hsv[..., 2]
        value_center = 40

        hue = cv2.inRange(hue, hue_center - 15, hue_center + 12)
        saturation = cv2.inRange(saturation, saturation_center - 18, saturation_center + 14)
        value = cv2.inRange(value, value_center - 12, value_center + 12)
        return hue, saturation, value

    @staticmethod
    def get_approximation(contour):
        return cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)

    @staticmethod
    def filter_rectangle(rectangle: Rectangle) -> bool:
        # print(f'Rectangle: {rectangle[1][0] * rectangle[1][1]}')
        return super(NxpPcbCamera, NxpPcbCamera).filter_rectangle(rectangle)

    @staticmethod
    def filter_approximation(approximation) -> bool:
        # print(f"Approx: {len(approximation)}")
        return super(NxpPcbCamera, NxpPcbCamera).filter_approximation(approximation)
