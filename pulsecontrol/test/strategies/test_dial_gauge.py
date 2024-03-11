import os

import cv2
import numpy as np
import pytest

from test.strategies.conftest import divide_into_ranges, display


@pytest.fixture()
def image_data(request) -> np.ndarray:
    image = cv2.imread(os.path.join("test/data", request.param))
    return image


@pytest.mark.skip("Test for finding the best saturation")
@pytest.mark.parametrize(
    "image_data", ["rectangle/Large-4-2023-11-20T125018.jpg"], indirect=True
)
def test_image_sat(image_data: np.ndarray):
    cv_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)

    saturation = cv_image[..., 1]  # 0 is hue, 1 is sat
    thresh, labels = divide_into_ranges(saturation, 30, 5 * 30, 10)
    display(thresh, labels)


# @pytest.mark.skip('Test for finding the best hue value')
@pytest.mark.parametrize(
    # "image_data", ["dataset/tinysteps/alternating/0.001/IMG_6169.JPG"], indirect=True
    "image_data",
    ["dataset/alternating/no_homing/IMG_9201.JPG"],
    indirect=True,
)
def test_image_hue(image_data: np.ndarray):
    cv_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)
    hue = cv_image[..., 0]
    thresh, labels = divide_into_ranges(hue, 0, 10, 1)
    display(thresh, labels)
    # thresh, labels = divide_into_ranges(hue, 170, 180, 1)
    # display(thresh, labels)


# @pytest.mark.skip('Test for finding the best value')
@pytest.mark.parametrize(
    "image_data", ["dataset/tinysteps/alternating/0.001/IMG_6169.JPG"], indirect=True
)
def test_image_value(image_data: np.ndarray):
    cv_image = cv2.cvtColor(image_data, cv2.COLOR_RGB2HSV)
    value = cv_image[..., 2]
    thresh, labels = divide_into_ranges(value, 0, 255, 20)
    display(thresh, labels)


@pytest.mark.skip("Used validate the combined maps")
def test_combined(image_data: np.ndarray):
    cv_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)

    hue = cv_image[..., 0]
    saturation = cv_image[..., 1]
    default_chip_color = cv2.inRange(hue, 70, 95)

    saturation = cv2.inRange(saturation, 40, 100)

    ds = cv2.bitwise_and(default_chip_color, saturation)
    display(
        [
            default_chip_color,
            saturation,
            ds,
        ],
        ["default", "saturation", "d+s"],
    )


@pytest.mark.skip("ignore")
@pytest.mark.parametrize("image_data", ["board.png"], indirect=True)
def test_generic(image_data: np.ndarray):
    hsv = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)
    hue = hsv[..., 0]
    hue_center = 90  # 178 / 2  # from gimp, out of 360
    saturation = hsv[..., 1]
    saturation_center = 56  # 23 * 255 / 100  # between 17 and 25 out of 100 in gimp
    value = hsv[..., 2]
    value_center = 63  # 25 * 255 / 100  # 20-30

    kernel = np.ones((5, 5), np.uint8)

    hue = cv2.inRange(hue, hue_center - 10, hue_center + 6)
    saturation = cv2.inRange(saturation, saturation_center - 12, saturation_center + 12)
    value = cv2.inRange(value, value_center - 10, value_center + 10)
    saturation = cv2.morphologyEx(saturation, cv2.MORPH_CLOSE, kernel)
    hue = cv2.morphologyEx(hue, cv2.MORPH_CLOSE, kernel)
    value = cv2.morphologyEx(value, cv2.MORPH_CLOSE, kernel)

    combined = cv2.bitwise_and(cv2.bitwise_and(hue, saturation), value)
    display(
        [hue, saturation, value, combined], ["hue", "saturation", "value", "combined"]
    )
