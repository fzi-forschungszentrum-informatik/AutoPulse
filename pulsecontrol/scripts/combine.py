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
@click.option("--interpolate/--no-interpolate", default=False)
def main(dataset: Path, interpolate: bool):
    if dataset.is_dir() and dataset.name != "normalized.json":
        dataset = Path(dataset, "normalized.json")

    step_size = dataset.parent.name
    print(f"This dataset has a step size of {step_size}")

    if (combined := Path(dataset.parent, "combined.json")).is_file():
        raise ValueError("File exists. Confirm and delete manually")
    else:
        with open(dataset, "r") as infile:
            data = json.load(infile)

        big = np.asarray(data["big"])
        small = np.asarray(data["small"])
        print(len(big), len(small))
        result = big

        if interpolate:
            for n, s in enumerate(small):
                steps = None
                interpolation_step = None
                if 0.067 < big[n] < 0.085:
                    if interpolation_step is None:
                        low = small[n - 1]
                        for i in range(n, big.size - 1):
                            if not (0.067 < big[i] < 0.085):
                                upper = small[i]
                                steps = 0
                                interpolation_step = (upper - low) / (i - n)
                                break
                    steps += 1
                    interpolated = interpolation_step * steps
                    print(f"Interpolation at {n}", s, low + interpolated)
                    small[n] = low + interpolated
                else:
                    steps = None
                    interpolation_step = None
                    low = small[n]

        small = np.int32(small)
        result += small / 10

        combined = Path(dataset.parent, "combined.json")
        with open(combined, "w") as outfile:
            json.dump(result.tolist(), outfile)


if __name__ == "__main__":
    main()
