from dataclasses import dataclass
from pathlib import Path

import click
import cv2
import numpy as np

from strategies.conftest import divide_into_ranges, display


@dataclass
class Store:
    hsv_image: np.ndarray


@click.group()
@click.option('--image', '-i', type=click.Path(path_type=Path), help='Image file')
@click.pass_context
def cli(ctx, image: Path):
    click.echo('Starting...')
    if image.name == '<latest>':
        image = sorted(filter(lambda n: n.is_file(), image.parent.iterdir()))[-1]
    image = cv2.imread(str(image))
    cv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    ctx.obj = Store(cv_image)


@cli.command()
@click.option('--lower', '-l', type=int, default=0, help='Lower bound')
@click.option('--upper', '-u', type=int, default=255, help='Upper bound')
@click.option('--step', '-s', type=int, default=30, help='Step size')
@click.pass_obj
def saturation(obj: Store, lower, upper, step):
    sat = obj.hsv_image[..., 1]  # 0 is hue, 1 is sat
    thresh, labels = divide_into_ranges(sat, lower, upper, step)
    display(thresh, labels, "sat")


@cli.command()
@click.option('--lower', '-l', type=int, default=0, help='Lower bound')
@click.option('--upper', '-u', type=int, default=180, help='Upper bound')
@click.option('--step', '-s', type=int, default=30, help='Step size')
@click.pass_obj
def hue(obj: Store, lower, upper, step):
    h = obj.hsv_image[..., 0]
    thresh, labels = divide_into_ranges(h, lower, upper, step)
    display(thresh, labels, "hue")


@cli.command()
@click.pass_obj
def hue2(obj: Store):
    # hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue = obj.hsv_image[..., 0]
    hue_vals = (60, 80)
    hue_list = (0, 20, 30, 50)

    h = cv2.inRange(hue, *hue_vals)
    for i in hue_list:
        h = cv2.bitwise_or(h, cv2.inRange(hue, i, i))
    display([h], ["hue"], "hue")


@cli.command()
@click.pass_obj
def zeros(obj: Store):
    img = obj.hsv_image
    h = np.zeros_like(img)
    s = np.zeros_like(img)
    v = np.zeros_like(img)
    h_zero = np.where(img[..., 0] == 0)
    h[h_zero] = 255
    s_zero = np.where(img[..., 1] == 0)
    s[s_zero] = 255
    v_zero = np.where(img[..., 2] == 0)
    v[v_zero] = 255
    display([h, s, v], ["hue", 'sat', 'val'], "All Zeros")


@cli.command()
@click.pass_obj
def maximums(obj: Store):
    img = obj.hsv_image
    h = np.zeros_like(img)
    s = np.zeros_like(img)
    v = np.zeros_like(img)
    h_zero = np.where(img[..., 0] == 180)
    h[h_zero] = 255
    s_zero = np.where(img[..., 1] == 255)
    s[s_zero] = 255
    v_zero = np.where(img[..., 2] == 255)
    v[v_zero] = 255
    display([h, s, v], ["hue", 'sat', 'val'], "All Max")


@cli.command()
@click.option('--lower', '-l', type=int, default=0, help='Lower bound')
@click.option('--upper', '-u', type=int, default=255, help='Upper bound')
@click.option('--step', '-s', type=int, default=30, help='Step size')
@click.pass_obj
def value(obj: Store, lower, upper, step):
    val = obj.hsv_image[..., 2]
    thresh, labels = divide_into_ranges(val, lower, upper, step)
    display(thresh, labels, "value")


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


if __name__ == '__main__':
    cli()
