from pathlib import Path

import click
import matplotlib.pyplot as plt
import seaborn as sns
from pandas import read_csv


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
    """
    Creates two violin plots for comparing end-stop/homing accuracy.
    """
    homing = Path(dataset, "homing")
    no_homing = Path(dataset, "no_homing")

    homing_file = Path(homing, "distance_between.csv")
    no_homing_file = Path(no_homing, "distance_between.csv")

    for test in [homing_file, no_homing_file]:
        data = read_csv(test).rename(columns={"real": test.parent.name})

        # Create a violin plot
        fig, ax = plt.subplots()

        sns.violinplot(
            data=data,
            ax=ax,
            inner_kws=dict(box_width=10, whis_width=2, color="0.8"),
        )

        # Add strip plot next to violins
        # sns.stripplot(data=[rel, sb], color="black", size=2, jitter=True, ax=ax)
        sns.stripplot(
            data=data,
            color="black",
            size=2,
            jitter=True,
            ax=ax,
            alpha=0.5,
        )

        # Customize the plot
        # ax.set_xticks([0, 1])
        # ax.set_xticklabels(["relative", "step-back"])
        ax.set_ylabel("position [mm]")
        ax.yaxis.grid(True)
        ax.set_title("repeatability of moving to the same position")

        # Add a solid line across the y-axis
        # ax.axhline(y=float(step_size), color="red", linestyle="-", linewidth=2)
        # Add a label for the y-axis line
        # ax.text(0.5, float(step_size), step_size, color="red", ha="right", va="bottom")

        # Show the plot
        plt.savefig(Path(dataset, f"{test.parent.name}.pdf"))
        plt.show()
        plt.close()


if __name__ == "__main__":
    main()
