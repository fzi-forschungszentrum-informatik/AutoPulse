from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# noinspection PyUnresolvedReferences
from pandas import read_csv


def path_to_float(data: Path) -> float:
    return float(data.name)


T = 5.0  # Sample Period
fs = 30.0  # sample rate, Hz
cutoff = 2  # desired cutoff frequency of the filter, Hz ,      slightly higher than actual 1.2 Hznyq = 0.5 * fs  # Nyquist Frequencyorder = 2       # sin wave can be approx represented as quadratic
n = int(T * fs)  # total number of samples


@click.command()
@click.argument(
    "dataset",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    nargs=1,
)
def main(dataset: Path):
    names = []

    relative = sorted(list(dataset.glob("relative/0.*")), key=path_to_float)
    step_back = sorted(list(dataset.glob("step-back/0.*")), key=path_to_float)
    for rel, sb in zip(relative, step_back):
        step_size = rel.name
        names.append(rel.name)
        rel = Path(rel, "accumulative.csv")
        sb = Path(sb, "accumulative.csv")

        rel = read_csv(rel)
        sb = read_csv(sb)

        rel = rel.rename(columns={"real": "relative"})
        sb = sb.rename(columns={"real": "step-back"})
        merged = rel.merge(sb, how="left", left_on="request", right_on="request")

        merged["relative"] = np.gradient(merged["relative"])
        merged["step-back"] = np.gradient(merged["step-back"])

        # Create a violin plot
        fig, ax = plt.subplots()
        # sns.lineplot(data=[rel, sb], ax=ax, inner_kws=dict(box_width=10, whis_width=2, color="0.8"))
        print(merged)
        sns.lineplot(data=merged, y="step-back", x=range(len(merged["step-back"])))
        sns.lineplot(data=merged, y="relative", x=range(len(merged["relative"])))

        ax.set_title(f"Gradient of the movement distances graph, step size of {step_size}mm")

        # Add a solid line across the y-axis
        ax.axhline(y=float(step_size), color="red", linestyle="-", linewidth=2)
        # Add a label for the y-axis line
        ax.text(10, float(step_size), step_size, color="red", ha="right", va="bottom")

        # Show the plot
        plt.savefig(Path(dataset, step_size + "-grad.pdf"))
        plt.show()
        plt.close()


if __name__ == "__main__":
    main()
