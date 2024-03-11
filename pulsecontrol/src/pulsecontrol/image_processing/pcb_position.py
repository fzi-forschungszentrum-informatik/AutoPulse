import json
from enum import Enum
from pathlib import Path

import click
import cv2
from dacite import from_dict, Config

from pulsecontrol.helpers import Point2D
from pulsecontrol.image_processing.generate_points import load_images, to_image
from pulsecontrol.strategies.camera import RectangleCamera


def load_image(path: Path):
    def inner():
        return load_image(path)

    return inner


def find_index(path: Path) -> int:
    name = path.name
    split = int(name.split("-")[1])
    return split


@click.command()
@click.option(
    "--dataset",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to the dataset. All Pictures should be in this folder.",
)
def main(dataset: Path):
    rectangle_processor = from_dict(
        RectangleCamera,
        {
            "rectangle": True,
            "min_focus_distance": 16.99975,
            "size_per_pixel_at_focus_distance": 0.019479,
            "camera_position": [-53.448, -2.593],
        },
        config=Config(cast=[tuple, Enum], type_hooks={Point2D: Point2D.from_iter}),
    )

    result = []
    for name, image in load_images(
        sorted(filter(lambda n: n.suffix == ".npy", dataset.iterdir()), key=find_index)
    ):
        # print(name, image.shape)
        rectangle_processor.get_image = lambda *_, **__: image
        something = next(rectangle_processor.get_coordinate())
        print(something)
        result.append(something)

        center = something[0]
        x = int(center[0])
        y = int(center[1])
        cv2.circle(
            image,
            center=(x, y),
            radius=5,
            thickness=-1,
            color=(255, 0, 0),
        )
        to_image(Path("test", "data", "out", "center", name + ".jpg"), image)

    with open(
        Path(dataset.parent, dataset.name + "-result.json"),
        "w",
    ) as outfile:
        json.dump(result, outfile)


if __name__ == "__main__":
    main()
