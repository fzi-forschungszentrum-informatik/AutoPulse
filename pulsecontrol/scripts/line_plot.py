from pathlib import Path

import click
import matplotlib.pyplot as plt
import seaborn as sns

# noinspection PyUnresolvedReferences
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

        # rel = read_data(rel)
        # sb = read_data(sb)
        rel = read_csv(rel)
        sb = read_csv(sb)

        rel = rel.rename(columns={"real": "relative"})
        sb = sb.rename(columns={"real": "step-back"})
        # rel.set_index("request", inplace=True)
        # sb.set_index("request", inplace=True)
        # both = pd.concat((rel, sb), axis=1, sort=False).reset_index()
        # both.rename(columns={"index": "request"})
        merged = rel.merge(sb, how="left", left_on="request", right_on="request")

        # Create a violin plot
        fig, ax = plt.subplots()
        # sns.lineplot(data=[rel, sb], ax=ax, inner_kws=dict(box_width=10, whis_width=2, color="0.8"))
        print(merged)
        sns.lineplot(data=merged, y="request", x="step-back")
        sns.lineplot(data=merged, y="request", x="relative")

        # sns.lineplot(data=sb, x="real", y="request")

        # Add strip plot next to violins
        # sns.stripplot(data=[rel, sb], color="black", size=2, jitter=True, ax=ax)

        # Customize the plot
        # ax.set_xticks([0, 1])
        # ax.set_xticklabels(["relative", "step-back"])
        # ax.set_ylabel("step size")
        # ax.yaxis.grid(True)
        ax.set_title(f"requested and measured distance with step  {step_size}")

        # Add a solid line across the y-axis
        # ax.axhline(y=float(step_size), color="red", linestyle="-", linewidth=2)
        # Add a label for the y-axis line
        # ax.text(0.5, float(step_size), step_size, color="red", ha="right", va="bottom")

        # Show the plot
        plt.show()

        # fig, ax = plt.subplots()
        # ax.violinplot([rel, sb], showmeans=True)
        # ax.set_xticks([1, 2])
        # ax.set_xticklabels(["relative", "step-back"])
        # ax.set_ylabel("step size")
        # ax.set_title(step_size)
        # fig.show()


if __name__ == "__main__":
    main()
