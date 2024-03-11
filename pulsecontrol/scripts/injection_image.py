import json
from pathlib import Path

import click
import cv2
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pandas import DataFrame


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

    # Customize the plot
    # ax.set_xticks([0, 1])
    # ax.set_xticklabels(["small", "large"])
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    # ax.yaxis.grid(True)
    ax.set_title(title)


def point_to_image_coordinates(chip_rectangle, point: np.ndarray) -> np.ndarray:
    """
    The input point represents a fraction in which 1 is the width, height of the chip and 0, 0
    the upper left corner.
    """
    center, size, angle = chip_rectangle
    center = np.asarray(center)
    size = np.asarray(size)
    rotation = cv2.getRotationMatrix2D(center, -angle, 1)

    # Scale the point up to the size of the chip
    point *= size
    # shift the points to be centered around the chip
    point = point + center - size / 2

    # rotate
    rotated = cv2.transform(np.array([[point]]), rotation)[0][0]
    return rotated


@click.command()
@click.option("--hist/--no-hist", default=False)
@click.argument(
    "glitch",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    nargs=1,
)
def main(hist: bool, glitch: Path):
    center_image = sorted(glitch.glob("*.jpg"))[-1]

    with open(Path(glitch, "glitches.json"), "r") as infile:
        glitches = json.load(infile)

    with open(Path(glitch, "rectangle.json"), "r") as infile:
        rectangle = json.load(infile)[-1]

    base_image = cv2.imread(str(Path(glitch, center_image)))
    # base_image = cv2.cvtColor(base_image, cv2.COLOR_BGR2GRAY)
    print(base_image.shape)

    rectangle[0] = [rectangle[0][0] - 2000, rectangle[0][1] - 900]
    base_image = base_image[900 : 900 + 700, 2000 : 2000 + 600, ...]

    print(base_image.shape)

    coords = []
    data = []
    for fraction_pos, _, results in glitches:
        image_cords = point_to_image_coordinates(rectangle, fraction_pos)
        image_cords = np.around(image_cords).astype(np.uint32)
        coords.append(image_cords)
        if not hist:
            if "SUCCESS" in results or "RESET" in results:
                if "SUCCESS" in results:
                    cv2.circle(
                        base_image,
                        image_cords,
                        radius=8,
                        color=(0, 255, 0, 255),
                        thickness=-1,
                    )
                    print("success")
                if "RESET" in results:
                    cv2.circle(
                        base_image,
                        image_cords,
                        radius=6,
                        color=(0, 0, 255, 255),
                        thickness=-1,
                    )
                    print("reset")
            else:
                cv2.circle(
                    base_image,
                    image_cords,
                    radius=6,
                    color=(0, 130, 130, 255),
                    thickness=-1,
                )
                print("nothing")
        if hist:
            successes = results.count("SUCCESS") / len(results)
            resets = results.count("RESET") / len(results)

            # Create a 1x2 subplot using Seaborn
            # Create a histogram on the right axis using Seaborn
            data.append(dict(x=image_cords[0], y=image_cords[1], success=successes, reset=resets))

    if hist:
        fig, ax = plt.subplots()

        # Display the image on the left axis using Seaborn
        sns.heatmap(base_image, cmap="gray", ax=ax, cbar=False)
        ax.set_title("Image")
        df = DataFrame(data)
        df["x"] -= 2000
        df["y"] -= 900
        print(df)
        # print(df)
        sns.histplot(
            df,
            x="x",
            y="y",
            bins=20,
            hue="success",
            ax=ax,
            palette="viridis",
        )
        # sns.histplot(
        #     df,
        #     x='x',
        #     y='y',
        #     bins=20,
        #     hue='reset',
        #     ax=ax,
        #     palette="flare",
        # )
        ax.set_xlabel("x position [px]")
        ax.set_ylabel("y position [px]")
        # ax.set_title('Histogram')

        # Adjust layout to prevent clipping of titles
        plt.tight_layout()

        # Show the plot
        plt.show()
    else:
        cv2.imwrite(str(Path(glitch, "points.png")), base_image)


if __name__ == "__main__":
    main()
