import json
from pathlib import Path

import click
import numpy as np


@click.command()
@click.option(
    "--dataset",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Path either to the json with the rectangle centers.",
)
@click.option(
    "--zero-mean/--no-zero-mean",
    default=False,
)
def main(dataset: Path, zero_mean: bool):
    if dataset.suffix != ".json":
        raise ValueError("This only works on json data")

    new_name = dataset.name[:-5]

    with open(dataset, "r") as infile:
        result = json.load(infile)
        if len(result[0]) == 3:
            # this is a list of rectangles, not points
            t = []
            for d in result:
                t.append(d[0])
            result = np.asarray(t)
        if len(result[0]) == 2:
            # this is a list of points
            result = np.asarray(result)

    print("Shape:", result.shape)

    average_center = np.average(result, 0)
    if zero_mean:
        result = result - average_center

    distances = np.linalg.norm(result - np.array([0.0, 0.0]), axis=-1)
    print(average_center)
    print(result)

    points = Path(dataset.parent, new_name + ".csv")
    if points.is_file():
        raise ValueError("File exists, delete manually to confirm: %s" % points)
    dist_file = Path(dataset.parent, new_name + "-distances.csv")
    if dist_file.is_file():
        raise ValueError("File exists, delete manually to confirm: %s" % dist_file)

    with open(points, "w") as outfile:
        outfile.write("x,y\n")
        for value in result:
            outfile.write(f"{value[0]:.6f},{value[1]:.6f}\n")

    with open(dist_file, "w") as outfile:
        outfile.write("distance\n")
        for value in distances:
            outfile.write(f"{value:.6f}\n")


if __name__ == "__main__":
    main()
