from multiprocessing import set_start_method

import pytest
from dacite import from_dict, Config

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.dut.simple_target import SimpleTarget


@pytest.fixture(autouse=True)
def multiprocessing_mode():
    set_start_method("forkserver")


@pytest.fixture()
def simple_target() -> SimpleTarget:
    return from_dict(
        SimpleTarget,
        data={
            "simple_target": True,
            "run_pin": 2,
            "fault_pin": 3,
            "reset_pin": 4,
            "move_after": 20,
        },
        config=Config(type_hooks={Point2D: Point2D.from_iter}, cast=[tuple]),
    )


def test_infinite_run(simple_target):
    simple_target.start()
    while True:
        simple_target.check_success()
