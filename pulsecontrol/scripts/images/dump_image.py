from datetime import datetime
from enum import Enum
from pathlib import Path
from time import sleep as time_sleep

import click
import cv2
import numpy as np
import pytest
from dacite import from_dict, Config
from pytest import fixture

from pulsecontrol.strategies.camera import GenericPcbCamera
from pulsecontrol.strategies.camera.probe_camera import ProbeCamera, Probe
from pulsecontrol.strategies.camera.strategy import Focus
from pulsecontrol.strategies.control.moonraker import Moonraker
import logging

log = logging.getLogger(__name__)


@fixture
def moonraker():
    return Moonraker(endpoint="http://localhost", strategy="")


@fixture
def probe_camera(config: dict) -> ProbeCamera:
    return from_dict(ProbeCamera, config["Basic"]["probe_camera"], config=Config(cast=[Enum]))


@fixture()
def home_printer(moonraker: Moonraker, probe_camera: ProbeCamera, config: dict):
    moonraker.home_xy()
    x, y = moonraker.get_limits()[:2]
    moonraker.home_z((x / 2, y / 2))

    height_offset = config["Basic"]["probe_height"]
    moonraker.add_offset(z_offset=height_offset)


@pytest.mark.skip("Probe camera")
def test_save_image(moonraker, probe_camera: ProbeCamera):
    # move the carriage all the way to the camera
    # moonraker.home_x()
    # moonraker.move_to(z=probe_camera.focus_height)
    # time_sleep(1)
    # take the image
    image = probe_camera.get_image()
    np.save(f'test/data/{datetime.now().strftime("%Y-%m-%dT%H%M%S")}', image)


def to_image(name: str, image: np.ndarray):
    _, buffer = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_OPTIMIZE, 1, cv2.IMWRITE_JPEG_PROGRESSIVE, 1]
    )
    with open(name + ".jpg", "wb") as outfile:
        outfile.write(buffer.tobytes())


# @pytest.mark.skip('only needed to generate the data')
@click.command()
@click.option('--autofocus/--no-autofocus')
@click.option('--cam', type=int, default=0, help='Camera index from libcamera')
@click.option('--focus', type=float, default=0, help='set focus in libcamera')
@click.option('--iterations', type=int, default=30, help='Number of images to dump')
def dump_image(autofocus: bool, cam: int, focus: float, iterations: int):
    kwargs = dict(
        index=cam,
        _autofocus=autofocus,
        # is ignored if autofocus is True
        focus=Focus(
            pixel_size=0,
            lens_position=focus,
            at=0,
        )
    )
    match cam:
        case 0:
            camera = GenericPcbCamera(
                **kwargs
            )
        case 1:
            camera = ProbeCamera(probe_type=Probe.SMALL, **kwargs)
        case _:  # pragma: no cover
            raise ValueError("Unknown camera index, %s" % cam)

    for i in range(iterations):
        image = camera.get_image()
        name = Path(f'data/image_capture/simple-dump_{cam}_{i}_{datetime.now().strftime("%Y-%m-%dT%H%M%S")}')
        name.parent.mkdir(parents=True, exist_ok=True)
        np.save(name, image)
        to_image(str(name), image)
        time_sleep(2)


if __name__ == "__main__":
    dump_image()
