import cv2
import numpy
import numpy as np
import pytest
from matplotlib import pyplot as plt

from pulsecontrol.strategies.camera.probe_camera import ProbeCamera


@pytest.fixture()
def image_tool():
    return ProbeCamera(calibrated_center=(0.0, 0.0), focus_height=47.0)


@pytest.fixture()
def test_image():
    return numpy.load("test/data/nxp.npy")


@pytest.mark.skip("only needed to generate the data")
def test_to_image(test_image):
    _, buffer = cv2.imencode(
        ".jpg",
        test_image,
        [cv2.IMWRITE_JPEG_OPTIMIZE, 1, cv2.IMWRITE_JPEG_PROGRESSIVE, 1],
    )
    with open("test/data/outfile.jpg", "wb") as outfile:
        outfile.write(buffer.tobytes())


def to_image(image, name):
    _, buffer = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_OPTIMIZE, 1, cv2.IMWRITE_JPEG_PROGRESSIVE, 1]
    )
    with open(name, "wb") as outfile:
        outfile.write(buffer.tobytes())


@pytest.mark.skip("only needed to generate the data")
def test_probe_center(image_tool, test_image: np.ndarray):
    print(test_image.shape)
    cv_image = cv2.cvtColor(test_image, cv2.COLOR_RGB2HSV)
    # Crop center

    print(type(cv_image), cv_image.shape)

    # (2592, 4608, 3)
    x = 2592 / 2
    y = 4608 / 2
    center = 800

    left_border = int(x - center)
    right_border = int(x + center)
    top_border = int(y - center)
    low_border = int(y + center)

    hue = cv_image[left_border:right_border, top_border:low_border, 0]
    sat = cv_image[left_border:right_border, top_border:low_border, 1]
    val = cv_image[left_border:right_border, top_border:low_border, 2]
    normal = test_image[left_border:right_border, top_border:low_border, :]

    # Display.
    plt.figure(figsize=(20, 7))
    plt.subplot(221)
    plt.imshow(hue)
    plt.title("Hue")
    plt.axis(False)
    plt.subplot(222)
    plt.imshow(sat)
    plt.title("Saturation")
    plt.axis(False)
    plt.subplot(223)
    plt.imshow(val)
    plt.title("Lightness")
    plt.axis(False)
    plt.subplot(224)
    plt.imshow(normal)
    plt.title("Normal")
    plt.axis(False)
    plt.show()
