import cv2
import numpy as np
import pytest
from matplotlib import pyplot as plt
from pytest_mock import MockerFixture

from pulsecontrol.helpers.config_loader import from_dict_casts
from pulsecontrol.strategies.camera import RectangleCamera

TEST_IMAGES = ["rectangle.jpg"]
TEST_IMAGE = TEST_IMAGES[0]


@pytest.fixture()
def rectangle_pcb():
    return from_dict_casts(
        RectangleCamera,
        {
            "rectangle": True,
            "min_focus_distance": 16.99975,
            "size_per_pixel_at_focus_distance": 0.019479,
            "camera_position": [-53.448, -2.593],
        },
    )


@pytest.fixture(autouse=True)
def patch_camera(mocker: MockerFixture, image_data: np.ndarray, rectangle_pcb):
    mock = mocker.MagicMock()
    rectangle_pcb.get_image = mock
    rectangle_pcb.get_image.return_value = image_data
    yield


@pytest.mark.parametrize(
    "image_data",
    [TEST_IMAGE],
    indirect=True,
)
def test_draw_some_points(rectangle_pcb, image_data):
    rectangle = next(rectangle_pcb.get_coordinate())
    center, size, angle = rectangle
    size = np.asarray(size)
    rotation = cv2.getRotationMatrix2D(center, -angle, 1)
    center = np.asarray(center)
    points = np.asarray([(0.3, 0.1), (0.6, 0.3), (0.6, 0.8), (0.1, 0.5), (0.9, 0.9)])
    points *= size
    points += center
    points -= size / 2
    rotated = cv2.transform(np.array([points]), rotation)[0]

    cv2.circle(
        image_data,
        np.around(center).astype(np.uint16),
        radius=30,
        color=(255, 0, 0),
        thickness=-1,
    )
    for n, point in enumerate(rotated, 1):
        rounded = np.around(point)
        from_center = rounded.astype(np.uint16)
        color = 255 // n
        cv2.circle(image_data, from_center, radius=30, color=(0, 0, color), thickness=-1)

    plt.imshow(image_data)
    plt.title("Points")
    plt.show()
