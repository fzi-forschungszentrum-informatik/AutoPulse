import json
from pathlib import Path

import click
import numpy as np


@click.command()
@click.option(
    "--dataset",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path),
    help="Path either to the normalized.json or to the folder containing it.",
)
@click.option("--margin-percent", type=float, default=0.05)
@click.option(
    "--allow-wrong-direction/--no-allow-wrong-direction",
    default=False,
    help="Make sure you validated the combined values with the raw images when setting this flag.\n"
    "This allows values that are negative (in the wrong order). "
    "This sometimes happens when the zero point wasn't 100% perfect and needs to manually corrected."
    "But it could be possible this happened naturally, to this flag was created to allow those values.",
)
def main(dataset: Path, margin_percent: float, allow_wrong_direction: bool):
    if dataset.name != "combined.json":
        if dataset.is_dir():
            dataset = Path(dataset, "combined.json")
        else:
            raise ValueError("This only works on already combined data.")

    step_size = dataset.parent.name
    print(f"This dataset has a step size of {step_size}")

    with open(dataset, "r") as infile:
        result = np.asarray(json.load(infile))

    eps = 0.01  # allow small deviations in the wrong direction, zero-point errors are very big
    if not allow_wrong_direction:
        for n in range(result.size - 1):
            dist = result[n] - result[n + 1]
            print(dist)
            if (step_size * 3) < dist < 0.1:
                raise ValueError(
                    "Values in the wrong order, zero point error? "
                    "Use `--allow-wrong-direction` if you cleaned up any zero-point errors. "
                    f"At {n}: {result[n]:.5f}, {result[n + 1]:.5f}"
                )

    # print(result)
    a = result[1:]
    b = result[:-1]
    diffs = a - b
    remove = np.int32(np.around(margin_percent * result.size))
    if remove > 0:
        diffs = diffs[remove:-remove]

    with open(Path(dataset.parent, "distance_between.csv"), "w") as outfile:
        outfile.write("target,real\n")
        for value in diffs:
            outfile.write(f"{step_size},{value:.6f}\n")

    with open(Path(dataset.parent, "statistics.csv"), "w") as outfile:
        outfile.write("mean,std\n")
        outfile.write(f"{diffs.mean()},{diffs.std()}\n")


if __name__ == "__main__":
    main()
