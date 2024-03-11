from pathlib import Path
from typing import Iterable

import click


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


def write(dataset: Path, data: Iterable[tuple[str, float]]):
    # if dataset.is_file():
    #     raise ValueError("File should not exist, delete manually and try again. %s" % dataset)
    with open(dataset, "w") as outfile:
        outfile.write("request,real\n")
        for step, value in data:
            outfile.write(f"{step:.6f},{value:.6f}\n")


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
        step_size = float(rel.name)
        names.append(rel.name)
        rel = Path(rel, "distance_between.csv")
        sb = Path(sb, "distance_between.csv")

        data_rel = read_data(rel)
        data_sb = read_data(sb)

        steps_rel = []
        steps_sb = []
        for i in range(1, len(data_rel)):
            data_rel[i] += data_rel[i - 1]
            steps_rel.append(i * step_size)
        for i in range(1, len(data_sb)):
            data_sb[i] += data_rel[i - 1]
            steps_sb.append(i * step_size)

        write(Path(rel.parent, "accumulative.csv"), zip(steps_rel, data_rel))
        write(Path(sb.parent, "accumulative.csv"), zip(steps_sb, data_sb))


if __name__ == "__main__":
    main()
