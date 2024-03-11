import os

import cv2
import numpy as np
from matplotlib import pyplot as plt


def display_image(test_image: np.ndarray):
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


if __name__ == "__main__":
    for name in filter(lambda n: n.endswith(".npy"), os.listdir("test/data")):
        image = np.load(f"test/data/{name}")
        display_image(image)
