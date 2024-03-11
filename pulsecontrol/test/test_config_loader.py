from dataclasses import dataclass

import pytest
from dacite import from_dict, Config
from pytest_mock import MockerFixture

from pulsecontrol.helpers import Point2D
from pulsecontrol.helpers.config_loader import load_remote
from pulsecontrol.helpers.http_wrapper import HttpWrapperHelper
from pulsecontrol.strategies.camera import CameraStrategies, NxpPcbCamera
from pulsecontrol.strategies.camera.http_wrapper import HttpWrapperLocal, HttpWrapperRemote
from pulsecontrol.strategies.integrator import Integrator
from pulsecontrol.strategies.movement import MovementStrategy


@dataclass(kw_only=True)
class MockIntegrator(Integrator):
    pcb_camera: CameraStrategies | HttpWrapperLocal

    def start(self):
        pass


@pytest.fixture()
def remote_config():
    return {
        "pcb_camera": {
            "remote_device": "http://localhost:5001",
            "config": {"subtype": "nxp", "camera_position": [-55, -6]},
        }
    }


def test_remote_config_integrity(requests_mock, mocker: MockerFixture, remote_config):
    mocker.patch("pulsecontrol.strategies.camera.http_wrapper.app")
    data = remote_config["pcb_camera"]
    nxp = from_dict(
        NxpPcbCamera,
        data["config"],
        config=Config(cast=[tuple], type_hooks={Point2D: Point2D.from_iter}),
    )
    assert isinstance(nxp, NxpPcbCamera)

    def remote_callback(request, context):
        on_remote = load_remote("camera", request.json())
        assert isinstance(on_remote, HttpWrapperRemote)

    requests_mock.post("http://localhost:5001/camera/load", text=remote_callback)

    wrapper = from_dict(
        HttpWrapperLocal,
        data,
        config=Config(cast=[tuple], type_hooks={Point2D: Point2D.from_iter}),
    )
    assert isinstance(wrapper, HttpWrapperLocal)


def test_remote_config_loader(mocker: MockerFixture, remote_config):
    mocker.patch("pulsecontrol.strategies.camera.http_wrapper.app")
    data = remote_config["pcb_camera"]

    wrapper = from_dict(
        HttpWrapperLocal,
        data,
        config=Config(cast=[tuple], type_hooks={Point2D: Point2D.from_iter}),
    )
    assert isinstance(wrapper, HttpWrapperLocal)
    thing = wrapper.get_jpg()
    print(thing)
    abc = wrapper.get_image()
    print(abc)


def test_endpoint_generator(requests_mock):
    requests_mock.post("http://localhost/initialize")

    @dataclass
    class Mock(HttpWrapperHelper, MovementStrategy):
        def __next__(self):
            return 0, 0

        def do_something(self):
            return self.get_remote()

    instance = Mock(remote_device="http://localhost", config={}, endpoints={}, strategy="movement")
    assert "http://localhost/movement/do_something" == instance.do_something()
