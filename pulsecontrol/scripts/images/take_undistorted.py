import click
from picamera2 import Picamera2

try:
    from libcamera import controls
except ModuleNotFoundError:
    import logging
    from unittest.mock import MagicMock

    logging.error("libcamera Module not installed, this is OK if not executed on a pi.")
    # This is a stub which allows us to run the code in environments without the picamera module
    controls = MagicMock()

from pathlib import Path

import numpy as np

import cv2


@click.command()
@click.option('--output', '-o', type=click.Path(path_type=Path), default='data/undistorted.png', help='Output file')
@click.option('--matrix', type=click.Path(path_type=Path), default='calibration/matrix.npy', help='Camera matrix')
@click.option('--distortion', type=click.Path(path_type=Path), default='calibration/dist.npy',
              help='Distortion coefficients')
def take(output: Path, matrix: Path, distortion: Path):
    matrix = np.load(matrix)
    distortion = np.load(distortion)

    resolution = (4608, 2592)
    camera = Picamera2(camera_num=0)
    camera_config = camera.create_still_configuration(
        main=dict(size=(*resolution,), format="RGB888"),
        buffer_count=1,
    )
    camera.configure(camera_config)
    camera.start(show_preview=False)
    camera.set_controls(
        dict(AfMode=controls.AfModeEnum.Auto, AfRange=controls.AfRangeEnum.Macro)
    )
    print("Waiting for focus")
    focused = camera.autofocus_cycle()
    print(f"Autofocus success: {focused}")
    image = camera.capture_array('main')
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(Path(output.parent, output.stem + 'distorted.png')), image)

    undistorted = cv2.undistort(image, matrix, distortion, None)
    cv2.imwrite(str(output), undistorted)


if __name__ == '__main__':
    take()
