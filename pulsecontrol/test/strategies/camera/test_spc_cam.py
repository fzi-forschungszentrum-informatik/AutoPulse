
import cv2
import numpy as np
import pytest
from pytest_mock import MockerFixture

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.camera.canny_spc_pcb_camera import CannySpcPcbCamera
from pulsecontrol.strategies.camera.pcb_camera import PcbCamera
from pulsecontrol.strategies.camera.spc_pcb_camera import SpcPcbCamera
from pulsecontrol.strategies.camera.strategy import Focus
from strategies.conftest import display


@pytest.fixture()
def pcb_camera(request):
    match request.param:
        case 'spc':
            return SpcPcbCamera(
                spc=True,
                camera_position=Point2D(-53.188, 2.891),
                index=0,
                focus=Focus(at=50, pixel_size=0.0445625),
            )
        case 'canny':
            return CannySpcPcbCamera(
                canny=True,
                camera_position=Point2D(-53.188, 2.891),
                index=0,
                focus=Focus(at=50, pixel_size=0.0445625),
            )


@pytest.fixture(autouse=True)
def patch_pcb_camera(
        mocker: MockerFixture,
        image_data: np.ndarray,
        pcb_camera,
):
    mock = mocker.MagicMock()
    pcb_camera.get_image = mock
    pcb_camera.get_image.return_value = image_data

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
        # ("calibration/spc@61.png", "spc"),
        # ("calibration/spc@plain.jpg", "spc"),
        # ("results/2024-05-08T171756.jpg", "spc"),
        # ("results/2024-05-13T090456.jpg", "spc"),
        # ("results/2024-05-14T174525.jpg", 'spc'),
        ('results/<latest>', 'spc'),
        # ("calibration/spc@pre.jpg", "spc"),
        # ("results/2024-05-07T163606.jpg", "spc"),
        # ("calibration/spc@61.png", "canny"),
    ],
    indirect=True,
)
def test_pcb_cameras(image_data: np.ndarray, pcb_camera: PcbCamera):
    blocked = pcb_camera.get_mask(image_data)
    combined = pcb_camera.combine_and_morph(*blocked)

    # contour stuff
    contours, hierarchies = cv2.findContours(combined, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    gray: np.ndarray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)

    bounding = np.stack((gray.copy(),) * 3, axis=-1)
    cv2.drawContours(bounding, contours, -1, (0, 0, 255), 3)
    loose = np.stack((gray.copy(),) * 3, axis=-1)
    # filtered_size = np.stack((gray.copy(),) * 3, axis=-1)
    # filtered_smaller = np.stack((gray.copy(),) * 3, axis=-1)

    for contour, hierarchy in zip(contours, hierarchies[0]):
        approx = pcb_camera.get_approximation(contour)
        if pcb_camera.filter_approximation(approx):
            min_area = cv2.minAreaRect(approx)
            if pcb_camera.filter_rectangle(min_area):
                box = np.int32(cv2.boxPoints(min_area))
                cv2.drawContours(loose, [box], -1, (255, 0, 0), 3)

    match blocked:
        case canny, None, None:
            display(
                [canny, combined, bounding, loose],
                ["canny", "mask", "bounding", "loose"],
            )
        case _:
            display(
                [*blocked, combined, loose],
                ["h", "s", "v", "mask", "loose"],
            )
