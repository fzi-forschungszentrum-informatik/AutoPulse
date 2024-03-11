import json
from enum import Enum
from pathlib import Path

import click
from dacite import from_dict, Config

from pulsecontrol.helpers import Point2D

# noinspection PyUnresolvedReferences
from pulsecontrol.setup_logging import setup_logging  # noqa: F401
from pulsecontrol.strategies.camera import RectangleCamera


def load_log_positions(log: Path) -> list[Point2D]:
    data_lines = []
    with open(log, "r") as infile:
        while line := infile.readline():
            if "Moving to " in line:
                xy = line.split("Moving to")[-1].strip()
                x = float(xy.split()[0][1:])
                y = float(xy.split()[1][1:])
                point = Point2D(x, y)
                data_lines.append(point)
    return data_lines


@click.command()
@click.option(
    "--rectangles",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to the list of rectangles",
    required=True,
)
@click.option(
    "--logs",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to the log output of the system. "
    "Can be used to extract the position at the time of the picture.",
)
def main(rectangles: Path, logs: Path | None):
    dataset = rectangles.name.split("-")[0]
    if "small" == dataset:
        approx_center_pos = Point2D(246.0, 147.0)
    else:
        approx_center_pos = Point2D(140, 99)

    true_positions = None
    if logs is not None:
        true_positions = load_log_positions(logs)
        print(len(true_positions))

    with open(rectangles, "r") as infile:
        rectangle_data = json.load(infile)

    # first position is the manually entered approximate position of the rectangle
    true_positions = true_positions[1:]

    pcb_camera = from_dict(
        RectangleCamera,
        {
            "rectangle": True,
            "min_focus_distance": 16.99975,
            "size_per_pixel_at_focus_distance": 0.019479,
            "camera_position": [-53.448, -2.593],
        },
        config=Config(cast=[tuple, Enum], type_hooks={Point2D: Point2D.from_iter}),
    )
    # basic = Basic(
    #     probe_camera=None,
    #     pcb_camera=pcb_camera,
    #     printer=None,
    #     chipshouter=None,
    #     movement_strategy=None,
    #     interface=None,
    #     file_logger=None,
    # )

    calculated_positions = []
    for true_position, (center, (_, _), _) in zip(true_positions, rectangle_data):
        center = Point2D.from_iter(center)

        non_norm_dist = Point2D.from_iter(center) - pcb_camera.get_resolution() / 2
        offset_mm = pcb_camera.normalize_distance(non_norm_dist)
        calc_center_position = true_position + offset_mm
        calculated_positions.append(offset_mm)
        print(f"Rectangles: {center:.2f}: {offset_mm:.2f}mm")
        print(
            f"Base pos: {approx_center_pos:.2f}, Calculated Position: {calc_center_position:.2f}, true position: {true_position:.2f}"
        )

    with open(Path(rectangles.parent, f"{dataset}-offsets.json"), "w") as outfile:
        json.dump(list(map(lambda n: n.to_tuple(), calculated_positions)), outfile)

    if true_positions is not None:
        normalized = []
        for t, calc in zip(true_positions, calculated_positions):
            normalized.append(t + calc)

        with open(Path(rectangles.parent, f"{dataset}-normalized-positions.json"), "w") as outfile:
            json.dump(list(map(lambda n: n.to_tuple(), normalized)), outfile)


if __name__ == "__main__":
    main()
