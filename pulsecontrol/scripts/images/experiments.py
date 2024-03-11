from dataclasses import dataclass
from pathlib import Path

import click
import cv2
import numpy as np
from matplotlib import pyplot as plt

from strategies.conftest import display


@dataclass
class Store:
    gray: np.ndarray
    hsv: np.ndarray
    original: np.ndarray


@click.group()
@click.option('--image', '-i', type=click.Path(exists=True, path_type=Path, dir_okay=False), help='Image file')
@click.pass_context
def cli(ctx, image: Path):
    click.echo('Starting...')
    image = cv2.imread(str(image))
    cv_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    ctx.obj = Store(cv_image, hsv, image)


@cli.command()
@click.pass_obj
def canny(obj: Store):
    # blurred = obj.gray
    blurred = cv2.GaussianBlur(obj.gray, (7, 7), 0)
    edges = cv2.Canny(blurred, 8, 55, 5)
    plt.imshow(edges, cmap='gray')
    plt.show()
    # display([edges], ['canny'], "canny")


@cli.command()
@click.pass_obj
def watershed(obj: Store):
    # blur strongly
    blurred = cv2.GaussianBlur(obj.hsv, (13, 13), 5)

    def masking(hsv: np.ndarray):
        h = hsv[..., 0]
        mask1 = cv2.inRange(h, 0, 7)
        mask2 = cv2.inRange(h, 177, 180)
        m = cv2.bitwise_or(mask1, mask2)

        v = hsv[..., 2]
        m = cv2.bitwise_and(m, cv2.inRange(v, 160, 200))

        s = hsv[..., 1]
        m = cv2.bitwise_and(m, cv2.inRange(s, 140, 200))

        kernel = np.ones((5, 5), np.uint8)
        opening = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel, iterations=1)
        dilate = cv2.morphologyEx(opening, cv2.MORPH_DILATE, kernel, iterations=1)
        return dilate

    mask = masking(obj.hsv)
    center = np.mean(np.nonzero(mask), axis=1).astype(int)
    # mask
    new_mask = np.zeros_like(mask)
    left_upper_corner = (center[1] - 100, center[0] - 100)
    right_lower_corner = (center[1] + 100, center[0] + 100)
    cv2.rectangle(new_mask, left_upper_corner, right_lower_corner, 255, -1)
    # unknown
    unknown = np.zeros_like(mask)
    left_upper_corner = (center[1] - 300, center[0] - 300)
    right_lower_corner = (center[1] + 300, center[0] + 300)
    cv2.rectangle(unknown, left_upper_corner, right_lower_corner, 255, -1)
    unknown = cv2.subtract(unknown, new_mask)

    ret, markers = cv2.connectedComponents(new_mask)
    # The background is one marker as well
    markers = markers + 1
    markers[unknown == 255] = 0
    image = obj.original.copy()
    water = cv2.watershed(image, markers)
    image[water == -1] = [255, 0, 0]

    display([obj.gray, blurred, new_mask, unknown, markers, water],
            ['gray', 'blurred', 'mask', 'unknown', 'markers', 'water'],
            "blurred")


@cli.command()
@click.pass_obj
def std_filter(obj: Store):
    # blur strongly
    blurred = cv2.GaussianBlur(obj.gray, (13, 13), 8)
    blurred2 = cv2.GaussianBlur(obj.gray * obj.gray, (13, 13), 8)
    abs = cv2.absdiff(blurred2, blurred * blurred)
    abs = abs.astype(dtype=np.float32)
    sigma = cv2.sqrt(abs)

    # dilated = cv2.dilate(blurred, kernel, iterations=1)
    # plt.imshow(dilated, cmap='gray')
    # plt.show()
    display([obj.gray, blurred, blurred2, abs, sigma], ['gray', 'blurred', 'blurred2', 'abs', 'sigma'], "blurred")


if __name__ == '__main__':
    cli()
