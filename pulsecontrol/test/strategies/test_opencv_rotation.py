import os
from pathlib import Path

import cv2
import numpy as np
from pytest import fixture


@fixture(params=[
    "data/r1.png",
    "data/r2.png",
    "data/r3.png",
    "data/r4.png",
    "data/r6.png",
    "data/r7.png",
])
def image(request) -> np.ndarray:
    print(os.getcwd())
    return cv2.imread(str(request.param))


def test_rotation(image: Path):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv[..., 1], 100, 255)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.minAreaRect(c) for c in contours]
    for r in rects:
        (x, y), (width, height), angle = r
        new_angle = 90.0 - angle
        if 0 < new_angle < angle:
            angle = new_angle
            width, height = height, width
        print(f"Center: {x}, {y}")
        print(f"Angle: {angle}")
        print(f"Width: {width}")
        print(f"Height: {height}")

