from itertools import product
from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from numpy.fft import fft, fftfreq
from pandas import read_csv


def path_to_float(data: Path) -> float:
    return float(data.name)


def read_data(dataset: Path):
    with open(dataset, "r") as infile:
        return list(
            map(
                float,
                map(str.strip, map(lambda n: n.split(",")[-1], infile.readlines()[1:])),
            )
        )


def gauss_plot(path, title: str, step_size: str):
    data = read_csv(path)

    base = data["real"]
    mean = base - np.mean(base)

    fft_result = fft(mean)
    freq = fftfreq(n=len(mean), d=float(step_size))
    y: np.ndarray = np.abs(fft_result)[: len(freq) // 2]
    max = y.argmax()
    fig, ax = plt.subplots()
    sns.lineplot(x=freq[: len(freq) // 2], y=y)
    plt.axvline(x=freq[max], color="red", label="max")

    ticks = plt.xticks()[0].tolist()[2:-1]
    ax.set_xticks([*ticks, freq[max]])

    # Customize the plot
    ax.set_xlabel("Hz")
    ax.set_ylabel("Magnitude")
    ax.set_title(f"{title} {step_size}mm")

    # Show the plot
    plt.savefig(Path(path.parent.parent, f"{title}-{step_size}-frequency.pdf"))
    plt.show()
    plt.close()


@click.command()
@click.argument(
    "dataset",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    nargs=1,
)
def main(dataset: Path):
    things = ["relative", "step-back"]
    step_sizes = [0.001, 0.005, 0.1, 0.05]

    for movement_type, step_size in product(things, step_sizes):
        path = Path(dataset, movement_type, str(step_size), "distance_between.csv")
        gauss_plot(path, movement_type, float(step_size))

    # relative = Path(dataset, things[0], str(step_sizes[0]), "distance_between.csv")
    # step_back = Path(dataset, things[1], str(step_sizes[0]), "distance_between.csv")
    # relative_05 = Path(dataset, things[0], str(step_sizes[1]), "distance_between.csv")

    # gauss_plot(relative, "relative movement", 1 / 1000)
    # gauss_plot(step_back, "step-back movement", 1 / 1000)
    # gauss_plot(relative_05, "relative movement 0.005", 0.005)


if __name__ == "__main__":
    main()
