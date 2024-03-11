import math
from pathlib import Path

import cv2
import numpy as np
import pytest
from matplotlib import pyplot as plt


def divide_into_ranges(
        data: np.ndarray, lower_bound, high_bound, step_size
) -> tuple[list[np.ndarray], list[str]]:
    thresh: list[np.ndarray] = []
    labels: list[str] = []
    if step_size == 1:
        for i in range(lower_bound, high_bound+1):
            thresh.append(cv2.inRange(data, i, i))
            labels.append(f"{i}")
    else:
        last = lower_bound
        for i, value in enumerate(range(lower_bound + step_size, high_bound, step_size)):
            thresh.append(cv2.inRange(data, last, value))
            labels.append(f"{last} -> {value}")
            last = value
        thresh.append(cv2.inRange(data, last, high_bound))
        labels.append(f"{last} -> {high_bound}")
    return thresh, labels


def show_image(ax_or_plt, image: np.ndarray):
    if len(image.shape) == 2:
        ax_or_plt.imshow(image, cmap="gray")
    else:
        ax_or_plt.imshow(image)


def display(images: list, labels: list, name: str = ""):
    # Display.
    edge = math.ceil(math.sqrt(len(images)))
    # plt.figure(dpi=1200)
    if len(images) == 1:
        show_image(plt, images[0])
        plt.suptitle(labels[0])
        plt.axis("off")
        plt.show()
        return
    fig, axes = plt.subplots(edge, edge, figsize=(edge * 4, edge * 4), dpi=300)
    for i in range(edge):
        for j in range(edge):
            if i * edge + j < len(images):
                ax = axes[i, j]
                show_image(ax, images[i * edge + j])
                ax.set_title(labels[i * edge + j])
                ax.axis("off")
            else:
                axes[i, j].axis("off")  # Turn off empty subplots

    # for index, (image, label) in enumerate(zip(images, labels)):
    #     plt.subplot(220 + index + 1)
    #     plt.imshow(image, cmap='gray')
    #     plt.title(label)
    #     plt.axis(False)
    plt.subplots_adjust(wspace=0.1, hspace=0.1)
    if name:
        plt.suptitle(name)
    plt.show()


@pytest.fixture()
def image_data(request) -> np.ndarray:
    p = Path(request.param)
    if p.name == '<latest>':
        p = sorted(filter(lambda n: n.is_file(), p.parent.iterdir()))[-1]
    assert p.exists()
    image = cv2.imread(str(p))
    return image
