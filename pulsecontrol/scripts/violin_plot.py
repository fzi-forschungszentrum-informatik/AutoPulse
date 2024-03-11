import math
import re
from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns
from pandas import read_csv, DataFrame


def path_to_float(data: Path) -> float:
    number = re.search(r'\d(?:\.\d+)?', data.name)
    return float(number.group())


def read_data(dataset: Path):
    with open(dataset, "r") as infile:
        return list(
            map(
                float,
                map(str.strip, map(lambda n: n.split(",")[-1], infile.readlines()[1:])),
            )
        )


def normalize(data: DataFrame) -> tuple[DataFrame, DataFrame]:
    data['measured'] = data['measured'] - 110
    data['measured'] = data['measured'] * -1
    # Convert millimeter to microns
    data['measured'] *= 1000
    data['measured'] = data['measured'].diff()
    # data['measured'] = data['measured'].fillna(0)
    # Delete first and last value
    data = data[1:-1]

    two_half_percent = math.ceil(len(data) * 0.025)
    data = data[two_half_percent:-two_half_percent]

    z_scores = np.abs(stats.zscore(data['measured']))
    # outliers = data['measured'].between(data['measured'].quantile(0.25), data['measured'].quantile(0.75))
    # outliers = data[outliers]
    outliers = data[(z_scores > 3)]
    return data, outliers


@click.command()
@click.option(
    "--dataset",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    nargs=1,
)
@click.option(
    "--pre-process/--no-pre-process",
    default=True,
)
def main(dataset: Path, pre_process: bool):
    """
    Compares two movement modes (step-back vs. direct) for each step size.
    """

    # If the intermediate files exist, skip calculation
    direct = sorted(list(dataset.glob("rel_direct_*")), key=path_to_float)
    step_back = sorted(list(dataset.glob("abs_step_back_*")), key=path_to_float)
    for dr, sb in zip(direct, step_back):
        print(dr, sb)
        step_size = path_to_float(dr)
        name = str(step_size)

        index = 0 if not pre_process else None
        dr = read_csv(dr, index_col=index)
        sb = read_csv(sb, index_col=index)
        # remove first and last points
        if pre_process:
            dr, outliers_dr = normalize(dr)
            sb, outliers_sb = normalize(sb)

            # The measurement device has internal positions that indicate the start and end of each half of the entire range
            # Traversing those points resets any missed steps, which can lead to a sudden jump in the measured distance
            # These resets help when measuring the distance traveled in a single direction,
            # but they are not useful when measuring the motion between two steps
            # due to the nature of these resets, they are much more impactful during small moves
            # they are less impactful during large moves, because they are no longer measurable
            Path(dataset, "outliers").mkdir(exist_ok=True)
            with open(Path(dataset, 'outliers', 'outliers.txt'), 'a') as file:
                file.write(f'name: {name}\n')
                file.write('DR\n')
                file.write(f'{outliers_dr}\n')
                file.write('SB\n')
                file.write(f'{outliers_sb}\n')

            dr.to_csv(Path(dataset, "outliers", f"rel_direct_{name}.csv"), index=True, na_rep='NaN')
            sb.to_csv(Path(dataset, "outliers", f"abs_step_back_{name}.csv"), index=True)

        dr = dr.rename(columns={"measured": "direct"})
        sb = sb.rename(columns={"measured": "step-back"})
        combined = pd.concat([dr, sb], axis=1)
        # combined = rel.merge(sb, how="left", left_on="target", right_on="target")
        del combined["movement"]
        # print(combined)

        # Create a violin plot
        fig, ax = plt.subplots()

        sns.violinplot(
            data=combined,
            ax=ax,
            inner_kws=dict(box_width=10, whis_width=2, color="0.8"),
        )
        # sns.violinplot(
        #     data=[rel, sb], ax=ax, inner_kws=dict(box_width=10, whis_width=2, color="0.8")
        # )

        # Add strip plot next to violins
        # sns.stripplot(data=[rel, sb], color="black", size=2, jitter=True, ax=ax)
        sns.stripplot(
            data=combined,
            color="black",
            size=2,
            jitter=True,
            ax=ax,
            alpha=0.5,
        )

        # Customize the plot
        # ax.set_xticks([0, 1])
        # ax.set_xticklabels(["relative", "step-back"])
        ax.set_ylabel("step size [μm]")
        # plt.gca().yaxis.set_major_locator(MultipleLocator(1))
        # plt.gca().yaxis.set_major_formatter(FormatStrFormatter("%d um"))

        ax.yaxis.grid(True)
        ax.set_title(f"distance traveled with step size {step_size}mm")

        # Add a solid line across the y-axis
        ax.axhline(y=step_size * 1000, color="red", linestyle="-", linewidth=2)
        # Add a label for the y-axis line
        ax.text(0.5, step_size * 1000, f"{step_size * 1000:.0f}", color="red", ha="right", va="bottom")

        # Show the plot
        plt.savefig(Path(dataset, f"{name}.pdf"))
        plt.show()
        plt.close()


if __name__ == "__main__":
    main()
