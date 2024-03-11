from dataclasses import dataclass
from time import sleep

from pulsecontrol.helpers import HasLogger
from pulsecontrol.strategies.camera.http_wrapper import HttpWrapperLocal as CameraWrapper
from pulsecontrol.strategies.integrator import Integrator


@dataclass(kw_only=True)
class WipCameraAutofocus(Integrator, HasLogger):
    """
    This tests only purpose is to test the autofocus endpoint, because it's both a property and
    is used as a setter.
    """

    def reset(self):
        super().reset()
        for thing in self.__dict__.values():
            try:
                thing.reset()
            except AttributeError:
                pass
            else:
                self.log.info("Stopped (%s)", thing.__class__)

    # Short description of the nature of the test
    description: str = ""

    # Camera
    pcb_camera: CameraWrapper

    def start(self):
        self.log.info("Got autofocus: %s", self.pcb_camera.get_autofocus())
        sleep(1)
        self.pcb_camera.set_autofocus(True)
        sleep(1)
        self.log.info("Got autofocus: %s", self.pcb_camera.get_autofocus())
