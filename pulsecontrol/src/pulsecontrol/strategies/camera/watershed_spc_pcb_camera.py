from dataclasses import dataclass

import cv2
import numpy as np

from pulsecontrol.strategies.camera.pcb_camera import PcbCamera


@dataclass(kw_only=True)
class WatershedSpcPcbCamera(PcbCamera):
    watershed: bool

    @staticmethod
    def get_mask(image: np.ndarray):
        raise NotImplementedError('')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0.5)
        edges = cv2.Canny(blurred, 0, 50, 3)
        return edges, None, None

    @staticmethod
    def filter_approximation(approximation) -> bool:
        return 4 <= len(approximation) < 8

    @staticmethod
    def combine_and_morph(edges: np.ndarray, *_) -> np.ndarray:
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.morphologyEx(edges, cv2.MORPH_DILATE, kernel, iterations=1)
        opened = cv2.morphologyEx(dilated, cv2.MORPH_OPEN, kernel)
        return opened

    @staticmethod
    def get_approximation(contour):
        return cv2.approxPolyDP(contour, 0.05 * cv2.arcLength(contour, True), True)
