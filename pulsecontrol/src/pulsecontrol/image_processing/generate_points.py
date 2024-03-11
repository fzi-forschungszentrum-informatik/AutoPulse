import json
from collections.abc import Iterator
from pathlib import Path
from typing import Callable, Iterable

import click
import cv2
import numpy as np
from PIL import Image
from more_itertools import take

# DATA_DIR = 'test/data/alternating-0.01'
DEBUG = False

# CENTER = (1984, 2881)

RADIUS = 700
MASK_RADIUS = 200

NamedImage = tuple[str, np.ndarray]
ImageIterator = Iterator[NamedImage]


def to_image(name: Path, image: np.ndarray):
    name.parent.mkdir(parents=True, exist_ok=True)
    # Path(os.path.dirname(name)).mkdir(parents=True, exist_ok=True)
    _, buffer = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_OPTIMIZE, 1, cv2.IMWRITE_JPEG_PROGRESSIVE, 1]
    )
    with open(name, "wb") as outfile:
        outfile.write(buffer.tobytes())


def conditional_load(
    path: Path,
    process: Callable[[np.ndarray, tuple[int, int]], np.ndarray],
    center: tuple[int, int],
) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        return process(np.load(path), center)
    else:
        return process(np.asarray(Image.open(path)), center)


def grayscale(data: ImageIterator) -> ImageIterator:
    for n, image in data:
        yield n, cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)


def invert_image(data: ImageIterator) -> ImageIterator:
    for n, image in data:
        invert = np.full(image.shape, 255, dtype=np.uint8) - image
        yield n, invert


def center_image(data: ImageIterator, center) -> ImageIterator:
    for name, image in data:
        smaller = image[
            center[0] - RADIUS : center[0] + RADIUS,
            center[1] - RADIUS : center[1] + RADIUS,
        ]
        # grey = grayscale(smaller)
        # invert = np.full(grey.shape, 255, dtype=np.uint8) - grey
        yield name, smaller


def red_filter(data: ImageIterator) -> ImageIterator:
    for name, image in data:
        h = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)[..., 0]
        only_red = cv2.inRange(h, 1, 8)
        # lower = cv2.inRange(h, 170, 180)
        # only_red = cv2.bitwise_or(only_red, lower)
        yield name, only_red


def morph_open(data: ImageIterator) -> ImageIterator:
    kernel = np.ones((3, 3), np.uint8)
    for n, image in data:
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        # image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        # image = cv2.medianBlur(image, 3)
        yield n, image


def morph_close(data: ImageIterator) -> ImageIterator:
    kernel = np.ones((3, 3), np.uint8)
    for n, image in data:
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        yield n, image


def post_process(data: ImageIterator, inner_mask: int, outer_mask: int) -> ImageIterator:
    kernel = np.ones((3, 3), np.uint8)
    for n, image in data:
        temp = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        temp = cv2.medianBlur(temp, 3)
        # to_image(f'test/data/out/blurred-{n}', temp)
        binary = cv2.inRange(temp, 40, 255)
        mask = np.zeros_like(binary)
        cv2.circle(
            mask,
            center=(RADIUS, RADIUS),
            radius=outer_mask,
            thickness=-1,
            color=255,
        )
        cv2.circle(
            mask,
            center=(RADIUS, RADIUS),
            radius=inner_mask,
            thickness=-1,
            color=0,
        )
        combined = cv2.bitwise_and(mask, binary)
        yield n, combined


def load_images(data: Iterable[Path]) -> ImageIterator:
    for path in data:
        if path.suffix.lower() == ".npy":
            yield path.name, np.load(path)
        else:
            yield path.name, np.asarray(Image.open(path))


def mask_images(data: ImageIterator, inner_mask: int, outer_mask: int) -> ImageIterator:
    # kernel = np.ones((3, 3), np.uint8)
    for name, image in data:
        # temp = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        # temp = cv2.medianBlur(temp, 3)
        # to_image(f'test/data/out/blurred-{name}', temp)
        # binary = cv2.inRange(temp, 40, 200)
        mask = np.zeros_like(image)
        cv2.circle(
            mask,
            center=(RADIUS, RADIUS),
            radius=outer_mask,
            thickness=-1,
            color=255,
        )
        cv2.circle(
            mask,
            center=(RADIUS, RADIUS),
            radius=inner_mask,
            thickness=-1,
            color=0,
        )
        combined = cv2.bitwise_and(mask, image)
        yield name, combined


def moving_average(
    image_stream: ImageIterator, window_size: int, enable: bool = True
) -> ImageIterator:
    if not enable:
        yield from image_stream
        return
    init_slice = list(take(window_size, image_stream))
    names: list[str] = [slice[0] for slice in init_slice]
    memory = np.stack([slice[1] for slice in init_slice])
    op_result = np.mean(memory, axis=0)  # .astype(memory[0].dtype)

    for i in range(window_size):
        result: np.ndarray = memory[i] - op_result
        yield names[i], result.clip(0, 255).astype(dtype=memory[0].dtype)

    for i, (name, image) in enumerate(image_stream):
        index = i % window_size
        memory[index] = image
        op_result = np.mean(memory, axis=0)  # .astype(memory[0].dtype)
        yield name, (memory[index] - op_result).clip(0, 255).astype(memory[0].dtype)


def line_filter(lines: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
    median = np.median(lines, axis=0)
    std = np.std(lines, axis=0)
    discarded = []
    accepted = []
    for line in lines:
        flag = True
        for i in range(4):
            # this is a very wide range, but it helps with filtering large outliers
            try:
                if np.abs(line[i] - median[i]) > 2 * std[i]:
                    discarded.append(line)
                    flag = False
                    break
            except IndexError:
                print("wtf", line)
        if flag:
            accepted.append(line)

    return np.asarray(accepted), discarded


def process_lines(lines: np.ndarray) -> np.ndarray:
    # cv2.kmeans()
    shape = lines.shape
    lines = lines.reshape((shape[0] * 2, 2))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, center = cv2.kmeans(
        lines.astype(np.float32),
        K=2,
        bestLabels=None,
        criteria=criteria,
        attempts=10,
        flags=cv2.KMEANS_PP_CENTERS,
    )
    return center.astype(lines[0].dtype)


def get_all_points(image: np.ndarray, hough_params: dict) -> np.ndarray:
    # HoughLines
    lines: np.ndarray = cv2.HoughLinesP(image, **hough_params)
    # line_image = np.stack((image.copy(),) * 3, axis=-1)
    if lines is not None:
        lines = lines.squeeze(1)
        return lines
    print("Couldn't find line")
    return np.zeros(
        shape=(2,),
    )


def get_best_point(name: str, image: np.ndarray, hough_params: dict) -> np.ndarray:
    # HoughLines
    lines: np.ndarray = cv2.HoughLinesP(image, **hough_params)
    line_image = np.stack((image.copy(),) * 3, axis=-1)
    if lines is not None:
        lines = lines.squeeze(1)
        lines, lines_discarded = line_filter(lines)
        for line in lines:
            cv2.line(line_image, line[:2], line[2:], (0, 255, 0), 1, cv2.LINE_AA)
        if lines.any():
            median_line = process_lines(lines)
            center = np.asarray((RADIUS, RADIUS))
            cv2.line(line_image, median_line[0], median_line[1], (0, 0, 255), 2, cv2.LINE_AA)
            to_image(Path(f"test/data/out/debug-{name}"), line_image)
            if np.linalg.norm(median_line[0] - center) > np.linalg.norm(median_line[1] - center):
                return median_line[0]
            else:
                return median_line[1]
    print("Couldn't find line")
    return np.zeros(
        shape=(2,),
    )


def draw_stuff():
    # for line in lines:
    # print(line)
    # x1, y1, x2, y2 = line
    # cv2.line(line_pic, (x1, y1), (x2, y2), (0, 255, 0), 1, cv2.LINE_AA)
    # start in blue
    # cv2.circle(line_pic, (x1, y1), radius=2, color=(255, 0, 0), thickness=-1)
    # # end in red
    # # cv2.circle(line_pic, (x2, y2), radius=2, color=(0, 0, 255), thickness=-1)
    # cv2.line(line_pic, (x1, y1), (x2, y2), (255, 0, 0), 2, cv2.LINE_AA)
    # # start in blue
    # # cv2.circle(line_pic, (x1, y1), radius=2, color=(120, 0, 120), thickness=-1)
    # # end in red
    # # cv2.circle(line_pic, (x2, y2), radius=2, color=(0, 120, 120), thickness=-1)
    #
    # cv2.circle(line_pic, main_point, radius=4, color=(0, 0, 255), thickness=-1)
    # # for line in lines_discarded:
    # #     # print(line)
    # #     x1, y1, x2, y2 = line
    # #     cv2.line(line_pic, (x1, y1), (x2, y2), (0, 0, 255), 1, cv2.LINE_AA)
    #
    # to_image(f'test/data/out/outside-{name}', line_pic)
    ...


def log_images(
    dataset_index: int, name: str, debug: bool = False
) -> Callable[[Iterator[tuple[str, np.ndarray]]], Iterator[tuple[str, np.ndarray]]]:
    def inner(
        data: Iterator[tuple[str, np.ndarray]],
    ) -> Iterator[tuple[str, np.ndarray]]:
        for i, (n, d) in enumerate(data):
            if debug:
                to_image(Path(f"test/data/out/{dataset_index}-{i}-{name}.jpg"), d)
            yield n, d

    return inner


def bounding_box(name: str, image: np.ndarray):
    # Bounding box stuff
    tree, hierarchy = cv2.findContours(
        image.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    bounding = np.stack((image.copy(),) * 3, axis=-1)

    cv2.drawContours(bounding, tree, -1, (0, 0, 255), 3)
    to_image(f"test/data/out/bounding-{name}", bounding)


@click.command()
@click.option("--debug/--no-debug", default=False, help="Set debug flag, enables debug output.")
@click.option(
    "--dataset",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to the dataset. All Pictures should be in this folder.",
)
@click.option("--b-center", type=(int, int), help="Center Pixel of the big hand")
@click.option("--s-center", type=(int, int), help="Center Pixel of the small hand")
@click.option("--average/--no-average", help="Subtract a moving mean on the images as a filter.")
def main(debug: bool, dataset: Path, b_center, s_center, average: bool):
    files = list(
        sorted(
            filter(lambda n: n.suffix.lower() == ".jpg", dataset.iterdir()),
        )
    )
    # if debug:
    #     files = [files[len(files) // 2]]

    # Hough parameters
    large_hand_params = dict(
        rho=1, theta=np.pi / 180 / 4, threshold=300, minLineLength=200, maxLineGap=100
    )
    small_hand_params = dict(
        rho=1, theta=np.pi / 180 / 4, threshold=50, minLineLength=40, maxLineGap=15
    )

    results: dict[str, list[tuple[int, int], tuple[int, int]]] = dict()
    masks = [
        dict(inner_mask=MASK_RADIUS, outer_mask=RADIUS),
        dict(inner_mask=10, outer_mask=130),
    ]
    # dataset_name = os.path.basename(os.path.dirname(files[0]))
    out_base_path = Path("test/data/out", dataset.parent.name, dataset.name)

    # earlystop = 0
    for i, (center, params) in enumerate(
        [(b_center, large_hand_params), (s_center, small_hand_params)]
    ):
        for original_name, (name, image) in zip(
            files,
            log_images(i, "open")(
                morph_open(
                    # log_images(i, 'close', debug)(
                    #     morph_close(
                    log_images(i, "averaged", debug)(
                        moving_average(
                            log_images(i, "masked", debug)(
                                mask_images(
                                    red_filter(
                                        log_images(i, "centered", debug)(
                                            center_image(load_images(files), center=center)
                                        )
                                    ),
                                    **masks[i],
                                ),
                            ),
                            window_size=5,
                            enable=average,
                        ),
                    ),
                ),
                # ),
                # ),
            ),
        ):
            line_pic = np.stack((image.copy(),) * 3, axis=-1)
            best_point = get_best_point(name, image, params)
            if best_point.any():
                cv2.circle(line_pic, best_point, radius=3, color=(0, 0, 255), thickness=-1)
                if not debug:
                    to_image(Path(out_base_path, f"{i}-point-{name}.jpg"), line_pic)
                else:
                    to_image(Path(out_base_path, f"debug-{i}-point-{name}.jpg"), line_pic)
                x, y = best_point
                selected: tuple[int, int] = (int(x), int(y))
            else:
                print("No Point: ", i, name)
                selected = (-1, -1)

            if i == 0:
                results[name] = [selected, (-1, -1)]
            elif i == 1:
                results[name][i] = selected

    if not debug:
        with open(Path(out_base_path, "result.json"), "w") as outfile:
            data = {
                "params": {"s_center": s_center, "b_center": b_center},
                "points": results,
            }
            json.dump(data, outfile, indent=2)


if __name__ == "__main__":
    main()
