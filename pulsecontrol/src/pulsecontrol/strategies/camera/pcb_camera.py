from abc import abstractmethod
from dataclasses import dataclass
from typing import Generator

import cv2
import numpy as np

from pulsecontrol.helpers import Rectangle
from pulsecontrol.strategies.camera.strategy import PiCameraWrapper


@dataclass(kw_only=True)
class PcbCamera(PiCameraWrapper):
    image_rotation: int | None = cv2.ROTATE_90_CLOCKWISE

    @staticmethod
    @abstractmethod
    def get_mask(image: np.ndarray, weakening_factor: float = 1.) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        raise NotImplementedError()

    @staticmethod
    def combine_and_morph(h, s, v) -> np.ndarray:
        kernel = np.ones((5, 5), np.uint8)
        s = cv2.morphologyEx(s, cv2.MORPH_OPEN, kernel)
        h = cv2.morphologyEx(h, cv2.MORPH_OPEN, kernel)
        v = cv2.morphologyEx(v, cv2.MORPH_OPEN, kernel)

        combined = cv2.bitwise_and(cv2.bitwise_and(h, s), v)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
        return cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)

    def filter_rectangle(self, rectangle: Rectangle | cv2.typing.RotatedRect) -> bool:
        _, (width, height), angle = rectangle
        ratio = width / height
        area = width * height
        if 0.6 <= ratio <= 1.4:
            if self._area_filter:
                return 10000 < area < 500000
            return True
        return False

    @staticmethod
    def filter_approximation(approximation) -> bool:
        return len(approximation) == 4

    @staticmethod
    @abstractmethod
    def get_approximation(contour: np.ndarray) -> np.ndarray:
        raise NotImplementedError()

    def sort_chip_candidates(self, rectangle: Rectangle):
        center = self.get_resolution() / 2
        distance_to_center = np.linalg.norm(np.asarray(rectangle[0]) - np.asarray((*center,)))
        return distance_to_center

    def get_coordinate(self) -> Generator[Rectangle, None, None]:
        image: np.ndarray = self.get_image()
        # Image mask
        masks = self.get_mask(image)
        combined = self.combine_and_morph(*masks)
        # contour stuff
        contours, hierarchy = cv2.findContours(combined, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        results = []
        for contour in contours:
            approx = self.get_approximation(contour)
            if self.filter_approximation(approx):
                min_area = cv2.minAreaRect(approx)
                if self.filter_rectangle(min_area):
                    _, (width, height), angle = min_area
                    # If the square is almost upright, noise in the image processing can cause the angle to be off
                    # This is a simple heuristic to correct that
                    new_angle = 90.0 - angle
                    if 0 < new_angle < angle:
                        angle = new_angle
                        width, height = height, width
                    results.append((min_area[0], (width, height), angle))

        yield from sorted(results, key=self.sort_chip_candidates)
