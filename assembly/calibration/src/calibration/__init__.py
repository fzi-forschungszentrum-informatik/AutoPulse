from os import environ
from pathlib import Path

import click
import cv2
import numpy as np


DEBUG = environ.get("DEBUG", False)


@click.command()
@click.option("--out-path", type=click.Path(exists=True, path_type=Path))
def generate(out_path: Path):
    cols = 5
    rows = 6
    square_size = 400
    marker_size = 0.8 * square_size
    aruco = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
    board = cv2.aruco.CharucoBoard(
        (cols, rows),
        square_size,
        marker_size,
        aruco,
    )
    from_cv = board.generateImage((cols * square_size, rows * square_size))

    cv2.imwrite(out_path, from_cv)
    cv2.imshow("charuco", from_cv)
    cv2.waitKey(0)


def load_images(path: Path) -> np.ndarray:
    images = np.array([cv2.imread(str(image)) for image in path.glob("*.png")])
    return images


def chessboard(
    images: np.ndarray, board: cv2.aruco.CharucoBoard
) -> tuple[list, np.ndarray]:
    corners: list = []
    ids: list = []
    image_size = np.array([0, 0])
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)
    detector = cv2.aruco.CharucoDetector(board)

    for image in images:
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image_size = grayscale.shape
        char_corners, char_ids, marker_corners, marker_ids = detector.detectBoard(
            grayscale
        )
        if DEBUG:
            output = image.copy()
            cv2.aruco.drawDetectedMarkers(output, marker_corners, marker_ids)
            cv2.aruco.drawDetectedCornersCharuco(output, char_corners, char_ids)
            cv2.imshow("output", output)
            cv2.waitKey(0)

        if (char_ids is not None) and char_ids.size > 0:
            refined_corners = cv2.cornerSubPix(
                grayscale, char_corners, (5, 5), (-1, -1), criteria
            )
            corners.append(refined_corners)
            ids.append(char_ids)

    calibration, cameraMatrix, distCoeffs, _, _ = cv2.aruco.calibrateCameraCharuco(
        charucoCorners=corners,
        charucoIds=ids,
        board=board,
        imageSize=image_size,
        cameraMatrix=None,
        distCoeffs=None,
    )

    print(calibration)
    print(cameraMatrix)
    print(distCoeffs)
    return cameraMatrix, distCoeffs


def undistort(image_path: Path, cameraMatrix, distCoeffs):
    image: np.ndarray = cv2.imread(str(image_path))
    undistorted = cv2.undistort(image, cameraMatrix, distCoeffs, None)
    cv2.namedWindow("both", cv2.WINDOW_NORMAL)
    cv2.imshow("both", np.concatenate((image, undistorted), axis=1))
    cv2.waitKey(0)


@click.command()
@click.option(
    "--image-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to camera matrix",
)
@click.option(
    "--matrix-path",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to camera matrix",
)
@click.option(
    "--dist-path",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to distortion coefficients",
)
def calibration(image_path: Path, matrix_path: Path, dist_path: Path):
    if matrix_path.is_file() and dist_path.is_file():
        cameraMatrix = np.load(matrix_path)
        distCoeffs = np.load(dist_path)
    else:
        images = load_images(image_path)
        print(images.shape)
        aruco = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
        cols = 5
        rows = 6
        square_size = 400
        marker_size = 0.8 * square_size
        board = cv2.aruco.CharucoBoard(
            (cols, rows),
            square_size,
            marker_size,
            aruco,
        )
        cameraMatrix, distCoeffs = chessboard(images, board)
        print(type(cameraMatrix), type(distCoeffs))

    matrix_path.parent.mkdir(exist_ok=True)
    dist_path.parent.mkdir(exist_ok=True)
    np.save(matrix_path, cameraMatrix)
    np.save(dist_path, distCoeffs)
    undistort(next(image_path.glob("*.png")), cameraMatrix, distCoeffs)
