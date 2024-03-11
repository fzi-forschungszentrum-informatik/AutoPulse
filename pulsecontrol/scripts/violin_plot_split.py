from pathlib import Path

import click
import matplotlib.pyplot as plt
import seaborn as sns
from pandas import DataFrame


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

    data = dict()
    for rel, sb in zip(relative, step_back):
        step_size = rel.name
        names.append(rel.name)
        rel = Path(rel, "distance_between.csv")
        sb = Path(sb, "distance_between.csv")

        rel = read_data(rel)
        sb = read_data(sb)
        data[step_size] = [rel, sb]

    df = DataFrame(data)
    fig, ax = plt.subplots()

    sns.violinplot(data=df, ax=ax, inner_kws=dict(box_width=10, whis_width=2, color="0.8"))
    plt.show()
    exit()
    # Create a violin plot
    sns.violinplot(data=[rel, sb], ax=ax, inner_kws=dict(box_width=10, whis_width=2, color="0.8"))

    # Add strip plot next to violins
    sns.stripplot(data=[rel, sb], color="black", size=2, jitter=True, ax=ax)

    # Customize the plot
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["relative", "step-back"])
    ax.set_ylabel("step size")
    ax.yaxis.grid(True)
    ax.set_title(f"distance traveled with step size {step_size}")

    # Add a solid line across the y-axis
    ax.axhline(y=float(step_size), color="red", linestyle="-", linewidth=2)
    # Add a label for the y-axis line
    ax.text(0.5, float(step_size), step_size, color="red", ha="right", va="bottom")

    # Show the plot
    plt.show()


if __name__ == "__main__":
    main()
