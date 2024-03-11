from pathlib import Path

import click
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
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


def plot_it(data_one, title: str, fn: Path):
    # Create a violin plot
    fig, ax = plt.subplots()
    sns.violinplot(
        data=data_one,
        ax=ax,
        inner_kws=dict(box_width=10, whis_width=2, color="0.8"),
    )
    # sns.violinplot(
    #     data=data_two,
    #     ax=ax,
    #     inner_kws=dict(box_width=10, whis_width=2, color="0.8"),
    # )

    # Add strip plot next to violins
    sns.stripplot(data=data_one, color="black", size=2, jitter=True, ax=ax)
    # sns.stripplot(data=data_two, color="black", size=2, jitter=True, ax=ax)

    # Customize the plot
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["small", "large"])
    ax.set_ylabel("distance")
    ax.yaxis.grid(True)
    ax.set_title(title)

    # Show the plot
    plt.savefig(fn)
    plt.show()
    plt.close()


@click.command()
@click.argument(
    "dataset",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    nargs=1,
)
def main(dataset: Path):
    things = ["gauss-position", "static-position"]
    sizes = ["small", "large"]

    gauss_small = Path(dataset, things[0], sizes[0] + "-normalized-positions-distances.csv")
    static_small = Path(dataset, things[1], sizes[0] + "-result-distances.csv")
    gauss_large = Path(dataset, things[0], sizes[1] + "-normalized-positions-distances.csv")
    static_large = Path(dataset, things[1], sizes[1] + "-result-distances.csv")

    gs = read_csv(gauss_small).rename(columns={"distance": "small"})
    gl = read_csv(gauss_large).rename(columns={"distance": "large"})
    gauss = pd.concat([gs, gl], axis=1)
    print(gauss)
    plot_it(
        gauss,
        "changing positions",
        fn=Path(dataset, "gauss-violin.pdf"),
    )

    ss = read_csv(static_small).rename(columns={"distance": "small"})
    sn = read_csv(static_large).rename(columns={"distance": "large"})
    static = pd.concat([ss, sn], axis=1) * 0.02
    plot_it(
        static,
        "static position",
        fn=Path(dataset, "static-violin.pdf"),
    )


if __name__ == "__main__":
    main()
