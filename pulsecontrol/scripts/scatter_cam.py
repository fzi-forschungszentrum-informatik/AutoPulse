from pathlib import Path

import click
import matplotlib.pyplot as plt
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


def gauss_plot(data, title: str):
    # Create a violin plot
    fig, ax = plt.subplots()
    sns.scatterplot(
        data=data,
        ax=ax,
        x="x",
        y="y",
        hue=range(1, len(data) + 1),
        palette="viridis",
    )

    # sns.scatterplot(
    #     data=data_large,
    #     ax=ax,
    # )

    # Add strip plot next to violins
    # sns.stripplot(data=[data_small, data_large], color="black", size=2, jitter=True, ax=ax)

    # Customize the plot
    # ax.set_xticks([0, 1])
    # ax.set_xticklabels(["small", "large"])
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    # ax.yaxis.grid(True)
    ax.set_title(title)


@click.command()
@click.argument(
    "dataset",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    nargs=1,
)
def main(dataset: Path):
    things = ["gauss-position", "static-position"]
    sizes = ["small", "large"]

    # gauss_small_path = Path(dataset, things[0], sizes[0] + "-normalized-positions.csv")
    # static_small_path = Path(dataset, things[1], sizes[0] + "-result.csv")
    gauss_large_path = Path(dataset, things[0], sizes[1] + "-normalized-positions.csv")
    # static_large_path = Path(dataset, things[1], sizes[1] + "-result.csv")

    gauss_large = read_csv(gauss_large_path)
    # gauss_small = read_csv(gauss_small_path)
    #
    # static_small = read_csv(static_small_path) * 0.02
    # static_large = read_csv(static_large_path) * 0.02

    # gauss_plot(gauss_small, "small rectangle, changing positions")
    # plt.savefig(Path(dataset, "gauss-small.pdf"))
    # # Show the plot
    # plt.show()
    # plt.close()
    # gauss_plot(static_small, "small rectangle, static position")
    # plt.savefig(Path(dataset, "static-small.pdf"))
    # # Show the plot
    # plt.show()
    # plt.close()

    gauss_plot(gauss_large, "large rectangle, changing positions")
    plt.savefig(Path(dataset, "gauss-large.pdf"))
    # Show the plot
    plt.show()
    plt.close()
    # gauss_plot(static_large, "large rectangle, static position")
    # plt.savefig(Path(dataset, "static-large.pdf"))
    # # Show the plot
    # plt.show()
    # plt.close()


if __name__ == "__main__":
    main()
