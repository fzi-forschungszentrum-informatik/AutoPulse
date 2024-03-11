import json
from pathlib import Path

import click
import numpy as np

from pulsecontrol.image_processing.generate_points import RADIUS

CENTER = np.asarray((RADIUS, RADIUS))


def angle(p1, p2):
    ang = np.degrees(
        np.arctan2(p2[1] - CENTER[1], p2[0] - CENTER[0])
        - np.arctan2(p1[1] - CENTER[1], p1[0] - CENTER[0])
    )
    return ang + 360 if ang < 0 else ang


def all_angles(zero, points, factor: float, invert: bool = False) -> list:
    measurements = []
    for index, p in enumerate(points):
        if p[0] < 0 or p[1] < 0:
            measurements.append(-1)

        deg = angle(p, zero)
        if invert:
            deg = 360 - deg
        print(index, deg)
        result = deg / 360 / factor
        # print(result)
        measurements.append(result)
    return measurements


def test_angles():
    points = [
        ("1", [1266, 1028]),
        ("9", [1221, 238]),
        ("3", [528, 1314]),
        ("6", [135, 296]),
        ("8", [873, 11]),
    ]
    b_zero = [1369, 625]
    for n, point in points:
        res = angle(b_zero, point)
        thing = res / 360 / 10
        print(n, res, thing)


@click.command()
@click.option(
    "--b-zero",
    type=(int, int),
    help="Pixel on the axis from the center to the zero value of the clock.",
)
@click.option(
    "--s-zero",
    type=(int, int),
    help="Pixel on the axis from the center to the zero value of the clock.",
)
@click.option(
    "--dataset",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path),
    help="Path either to the result.json or to the folder containing it.",
)
def main(b_zero: tuple[int, int], s_zero: tuple[int, int], dataset: Path):
    if dataset.name != "result.json":
        dataset = Path(dataset, "result.json")

    with open(dataset, "r") as infile:
        data = json.load(infile)

    data = list(map(lambda n: n[1], sorted(data["points"].items(), key=lambda n: n[0])))
    points = np.asarray(data)

    big_hand_points = points[:, 0, :]
    small_hand_points = points[:, 1, :]
    measurements = dict()
    measurements["big"] = all_angles(b_zero, big_hand_points, factor=10, invert=True)
    measurements["small"] = all_angles(s_zero, small_hand_points, factor=0.1)

    with open(Path(dataset.parent, "normalized.json"), "w") as outfile:
        json.dump(measurements, outfile)


if __name__ == "__main__":
    main()
