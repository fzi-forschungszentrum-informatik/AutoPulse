import cv2
import matplotlib.pyplot as plt
import numpy as np
import pytest
from pulsecontrol.strategies.camera.strategy import Focus
from pytest_mock import MockerFixture

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.camera.probe_camera import Probe
from strategies.conftest import divide_into_ranges, display

TEST_IMAGES = [
    "probe/probe.jpg",
    "probe/large.jpg",
    "probe/small.jpg",
    "dataset/Manual pictures/light0.jpg",
    "dataset/Manual pictures/light1.jpg",
    "dataset/Manual pictures/light2.jpg",
    "dataset/Manual pictures/light3.jpg",
    "results/2024-05-07T164108.jpg",
    "calibration/large.png",
    "results/<latest>"
]
TEST_IMAGE = TEST_IMAGES[-1]


@pytest.fixture()
def probe_camera():
    from pulsecontrol.strategies.camera.probe_camera import ProbeCamera

    return ProbeCamera(
        index=1,
        calibrated_center=Point2D(1220, 2304),
        focus=Focus(at=27, pixel_size=0.028277),
        probe_type=Probe.LARGE,
        crop_width=650,
        crop_upper_edge=Point2D(900, 2000)
    )


@pytest.mark.parametrize("image_data", ["results/2024-05-07T170809.jpg"], indirect=True)
def test_crop(probe_camera):
    image = probe_camera.get_image()
    cv2.imwrite('results/tmp/raw.png', image)
    image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    crop = probe_camera.crop_image(image)
    cv2.imwrite('results/tmp/crop.png', crop)
    preprocess = probe_camera.preprocess_image(crop)
    cv2.imwrite('results/tmp/pp.png', preprocess)


@pytest.fixture(autouse=True)
def patch_probe_camera(mocker: MockerFixture, image_data: np.ndarray, probe_camera):
    mock = mocker.MagicMock()
    probe_camera.get_image = mock
    probe_camera.get_image.return_value = image_data
    yield


@pytest.mark.parametrize("image_data", [TEST_IMAGE], indirect=True)
def test_find_center(probe_camera):
    x, y = probe_camera.get_coordinate()
    assert x != 0
    assert y != 0


@pytest.mark.skip("saturation is useless for the probe pictures")
@pytest.mark.parametrize(
    "image_data",
    [TEST_IMAGE],
    indirect=True,
)
def test_image_sat(image_data: np.ndarray):
    cv_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)

    saturation = cv_image[..., 1]  # 0 is hue, 1 is sat
    # 0..255
    thresh, labels = divide_into_ranges(saturation, 0, 255, 30)
    display(thresh, labels, "sat")


@pytest.mark.skip("value is useless for the probe pictures")
@pytest.mark.parametrize("image_data", [TEST_IMAGE], indirect=True)
def test_image_value(image_data: np.ndarray):
    cv_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)
    value = cv_image[..., 2]
    # 0..255
    thresh, labels = divide_into_ranges(value, 0, 255, 30)

    display(thresh, labels, "value")


@pytest.mark.skip("hue")
@pytest.mark.parametrize("image_data", [TEST_IMAGE], indirect=True)
def test_image_hue(image_data: np.ndarray):
    blurred = cv2.GaussianBlur(image_data, (7, 7), 0)
    cv_image = cv2.cvtColor(blurred, cv2.COLOR_RGB2HSV)
    hue = cv_image[..., 0]
    # 0..180
    thresh, labels = divide_into_ranges(hue, 90, 125, 5)
    my_range = cv2.inRange(hue, 90, 120)
    thresh.append(my_range)
    labels.append("my range")
    display(thresh, labels, "hue")


@pytest.mark.skip()
@pytest.mark.parametrize("image_data", [TEST_IMAGE], indirect=True)
def test_display_only_hue(image_data: np.ndarray):
    cv_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)
    hue = cv_image[..., 0] / 180 * 255
    plt.imshow(hue)
    plt.title("Only hue channel")
    plt.colorbar()
    plt.show()


@pytest.mark.skip()
@pytest.mark.parametrize("image_data", [TEST_IMAGE], indirect=True)
def test_image_canny_circle(image_data: np.ndarray):
    xy = Point2D(2000, 900)
    width, height = 650, 650
    # true_center = Point2D(2398, 1188)
    # cropped_true_center = true_center - xy
    cropped = image_data[xy.y: xy.y + height, xy.x: xy.x + width, ...]
    # gray = cv2.cvtColor(cropped, cv2.COLOR_RGB2GRAY)
    # blurred = cv2.GaussianBlur(cropped, (7, 7), 0)
    # gray_blur = cv2.GaussianBlur(gray, (7, 7), 0)
    hue: np.ndarray = cv2.cvtColor(cropped, cv2.COLOR_RGB2HSV)[..., 0]
    edges = cv2.Canny(hue, threshold1=1200, threshold2=2400, apertureSize=7)
    plt.imshow(edges)
    plt.title("Canny")
    plt.colorbar()
    plt.show()


# @pytest.mark.skip()
@pytest.mark.parametrize("image_data", [TEST_IMAGE], indirect=True)
def test_image_hue_circle(image_data: np.ndarray):
    xy = Point2D(900, 2000)
    width, height = 650, 650
    # true_center = Point2D(2398, 1188)
    # cropped_true_center = true_center - xy
    cropped = image_data[xy.y: xy.y + height, xy.x: xy.x + width, ...]
    gray = cv2.cvtColor(cropped, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(cropped, (7, 7), 0)
    gray_blur = cv2.GaussianBlur(gray, (7, 7), 0)
    hue: np.ndarray = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)[..., 0]
    my_range: np.ndarray = cv2.inRange(hue, 35, 80)

    kernel = np.ones((3, 3), np.uint8)
    opened = cv2.morphologyEx(my_range, cv2.MORPH_OPEN, kernel)
    # with_circles = np.stack((cropped.copy(),) * 3, axis=-1)
    with_circles = cropped.copy()

    # Small Probe Parameters
    # circles = cv2.HoughCircles(
    #     opened,
    #     cv2.HOUGH_GRADIENT,
    #     dp=2,
    #     minDist=1,
    #     param1=255,
    #     param2=40,
    #     maxRadius=80,
    #     minRadius=10,
    # )
    # Large Probe Parameters
    circles = cv2.HoughCircles(
        opened,
        cv2.HOUGH_GRADIENT,
        1.7,
        1,
        param1=255,
        param2=40,
        maxRadius=100,
        minRadius=50,
    )
    if circles is not None:
        # round to pixel values
        circles = np.uint16(np.around(circles))
        no_radius = circles[0, ..., 0:-1]
        point = np.around(np.average(no_radius, axis=0)).astype(np.uint16)
        for i in circles[0, :]:
            center = i[0], i[1]
            radius = i[2]
            # circle center
            cv2.circle(with_circles, center, 1, (0, 100, 100), 3)
            # circle outline
            cv2.circle(with_circles, center, radius, (255, 0, 255), 3)
            print(radius)
        cv2.circle(with_circles, point, 1, (255, 0, 0), 3)
    else:
        print("No circle detected")

    # circles = cv2.GaussianBlur(opened, (5, 5), 0)
    # my_range = my_range.astype(np.uint8)
    # circles = cv2.HoughCircles(cropped, cv2.HOUGH_GRADIENT, 1, 10, maxRadius=50)

    display(
        [cropped, gray_blur, my_range, opened, with_circles],
        ["cropped", "gray_blur", "range", "opened", "with_circles"],
        "combined",
    )
