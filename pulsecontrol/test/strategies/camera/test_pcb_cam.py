from enum import Enum

import cv2
import numpy as np
import pytest
from dacite import from_dict, Config
from pytest_mock import MockerFixture

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.camera import SimplePcbCamera
from pulsecontrol.strategies.camera.generic_pcb_camera import GenericPcbCamera
from pulsecontrol.strategies.camera.pcb_camera import PcbCamera
from pulsecontrol.strategies.camera.rectangle_camera import RectangleCamera
from strategies.conftest import display


@pytest.fixture()
def pcb_camera(request):
    match request.param:
        case "simple":
            data = {"simple": True}
            cam = SimplePcbCamera

        case _:
            raise ValueError("Camera launch config missing")

    common = {
        "min_focus_distance": 17,
        "size_per_pixel_at_focus_distance": 0.02,
        "camera_position": [-53.448, 1.2],
    }
    common.update(data)
    return from_dict(
        cam,
        common,
        config=Config(cast=[tuple, Enum], type_hooks={Point2D: Point2D.from_iter}),
    )


@pytest.fixture()
def generic_pcb():
    return GenericPcbCamera(
        strategy="camera",
        camera_position=Point2D(5, 0.5),
        size_per_pixel_at_focus_distance=0.02,
    )


@pytest.fixture()
def simple_pcb():
    return from_dict(
        SimplePcbCamera,
        {
            "simple": True,
            "min_focus_distance": 17,
            "size_per_pixel_at_focus_distance": 0.02,
            "camera_position": [-53.448, -2.593],
        },
        config=Config(cast=[tuple, Enum], type_hooks={Point2D: Point2D.from_iter}),
    )


@pytest.fixture()
def rectangle_pcb() -> RectangleCamera:
    return from_dict(RectangleCamera, {})


@pytest.fixture()
def patch_pcb_camera(
    mocker: MockerFixture,
    generic_pcb,
    image_data: np.ndarray,
    pcb_camera,
    rectangle_pcb,
    simple_pcb,
):
    mock = mocker.MagicMock()
    generic_pcb.get_image = mock
    generic_pcb.get_image.return_value = image_data
    pcb_camera.get_image = mock
    pcb_camera.get_image.return_value = image_data
    rectangle_pcb.get_image = mock
    rectangle_pcb.get_image.return_value = image_data

    yield


# @pytest.fixture(autouse=True)
# def patch_picam(mocker: MockerFixture):
#     magic = mocker.patch('snapper.strategies.camera.Picamera2')
#     picam = mocker.MagicMock()
#
#     picam.capture_array = mocker.MagicMock()
#     picam.capture_array.return_value = np.load('test/data/probe.4.npy')
#
#     magic.return_value = picam
#     yield picam


@pytest.mark.skip()
def test_find_chip(pcb_camera):
    x, y, width, height = pcb_camera.get_coordinate()
    assert x != 0
    assert y != 0
    assert width != 0
    assert height != 0




@pytest.mark.skip("Used validate the combined maps")
def test_combined(image_data: np.ndarray):
    cv_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)

    hue = cv_image[..., 0]
    saturation = cv_image[..., 1]
    default_chip_color = cv2.inRange(hue, 70, 95)

    saturation = cv2.inRange(saturation, 40, 100)

    ds = cv2.bitwise_and(default_chip_color, saturation)
    display(
        [default_chip_color, saturation, ds],
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


# @pytest.mark.skip()
@pytest.mark.parametrize(
    "image_data,pcb_camera",
    [
        # ('board.png', GenericPcbCamera),
        # ('nxp.jpg', NxpPcbCamera),
        # ("rectangle/Large-4-2023-11-20T125018.jpg", "rectangle"),
        ("rectangle/simple-focus-6.jpg", "simple"),
    ],
    indirect=True,
)
def test_pcb_cameras(image_data: np.ndarray, pcb_camera: PcbCamera):
    gray: np.ndarray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
    # print(cv_image.shape)
    # blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    # _, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)
    # print("Thresh: ", type(thresh), thresh.shape)
    # adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 7, 2)
    # print("Adaptive", type(adaptive), adaptive.shape)
    blocked = pcb_camera.get_mask(image_data)
    combined = pcb_camera.combine_and_morph(*blocked)

    # contour stuff
    tree, hierarchy = cv2.findContours(combined, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    print("Hierarchy", hierarchy.shape)

    bounding = np.stack((gray.copy(),) * 3, axis=-1)
    cv2.drawContours(bounding, tree, -1, (0, 0, 255), 3)
    loose = np.stack((gray.copy(),) * 3, axis=-1)
    # filtered_size = np.stack((gray.copy(),) * 3, axis=-1)
    # filtered_smaller = np.stack((gray.copy(),) * 3, axis=-1)

    for index, rectangle in enumerate(
        sorted(
            filter(
                pcb_camera.filter_rectangle,
                map(
                    cv2.minAreaRect,
                    filter(
                        pcb_camera.filter_approximation,
                        map(pcb_camera.get_approximation, tree),
                    ),
                ),
            ),
            key=pcb_camera.sort_chip_candidates,
        )
    ):
        box = np.int32(cv2.boxPoints(rectangle))
        cv2.drawContours(loose, [box], -1, (255, 0, 0), 3)

    display(
        [*blocked, combined, bounding, loose],
        ["h", "s", "v", "mask", "bounding", "loose"],
    )
