import json
from time import sleep

import pytest

from pulsecontrol.helpers.config_loader import from_dict_casts
from pulsecontrol.strategies.dut.chip_whisperer import Whisperer


@pytest.fixture
def chipwhisperer() -> Whisperer:
    with open('configuration/spc/bam.json') as f:
        data = json.load(f)['interface']
    return from_dict_casts(Whisperer, data)


def test_hs2(chipwhisperer: Whisperer):
    for _ in range(10):
        sleep(2)
        chipwhisperer.scope.arm()
        sleep(2)
