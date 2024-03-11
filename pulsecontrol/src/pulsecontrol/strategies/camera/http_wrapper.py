import datetime
import pickle
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from dacite import from_dict, Config
from flask import request

from pulsecontrol.helpers import Point2D, HasLogger
from pulsecontrol.helpers.http_wrapper import HttpWrapperHelper
from pulsecontrol.strategies.camera.probe_camera import ProbeCamera
from pulsecontrol.strategies.camera.strategy import CameraStrategy
from pulsecontrol.strategies.endpoint.http import app


@dataclass(kw_only=True)
class HttpWrapperLocal(CameraStrategy, HttpWrapperHelper, HasLogger):
    def get_image(self) -> np.ndarray:
        # remote = '/'.join((self.remote_device, self.strategy, self.endpoints['get_image']))
        self.log.info("Called get image")
        return self._raw_result()

    def get_jpg(self):
        # remote = '/'.join((self.remote_device, self.strategy, self.endpoints['get_jpg']))
        self.log.info("Called get jpg")
        return self._raw_result()

    def get_coordinate(self) -> Point2D:
        self.log.info("Called get coordinate")
        return pickle.loads(self._raw_result())

    def get_camera_position(self) -> Point2D | None:
        self.log.info("Called get camera position")
        return pickle.loads(self._raw_result())

    def get_min_focus_distance(self) -> float:
        self.log.info("Called get min focus distance")
        return pickle.loads(self._raw_result())

    def get_calibrated_focus_distance(self) -> float:
        self.log.info("Called get calibrated focus distance")
        return pickle.loads(self._raw_result())

    def get_size_per_pixel_at_focus_distance(self) -> float:
        self.log.info("Called get size per pixel at focus distance")
        return pickle.loads(self._raw_result())

    def get_resolution(self) -> Point2D:
        self.log.info("Called resolution distance")
        return pickle.loads(self._raw_result())

    def get_autofocus(self) -> bool:
        self.log.info("Called autofocus getter")
        return pickle.loads(self._raw_result())

    def set_autofocus(self, val: bool):
        self.log.info("Called autofocus setter with %s", val)
        self._request(params=dict(value=int(val)))


@dataclass(kw_only=True)
class HttpWrapperRemote(CameraStrategy, HasLogger):
    container: ProbeCamera | None = None

    endpoints: list[str] = field(
        default_factory=lambda: [
            "get_image",
            "get_jpg",
            "get_coordinate",
            "get_camera_position",
            "get_min_focus_distance",
            "get_calibrated_focus_distance",
            "get_size_per_pixel_at_focus_distance",
            "get_resolution",
            "get_autofocus",
            "set_autofocus",
        ]
    )

    def __post_init__(self):
        self.log.info("Setting up endpoints for the camera strategies")

        app.post("/" + self.strategy + "/" + "load")(self.load)
        for endpoint in self.endpoints:
            try:
                app.get("/" + self.strategy + "/" + endpoint)(getattr(self, endpoint))
            except AttributeError:
                self.log.error(
                    "This endpoint (%s) has no function, "
                    "either remote the endpoint or create a new function with this name",
                    endpoint,
                )
                raise

    def load(self) -> str:
        self.log.info("Loading specific camera strategy")
        # if self.container is not None:
        #     self.container.reset()
        self.container: ProbeCamera = from_dict(
            ProbeCamera,
            dict(request.get_json()),
            config=Config(type_hooks={Point2D: Point2D.from_iter}, cast=[tuple, Enum]),
        )
        return "Ok"

    def get_jpg(self):
        self.log.info("JPG endpoint called")
        start = datetime.datetime.utcnow()
        io_buffer = self.container.get_image()
        return (
            self.encode_image(io_buffer).tobytes(),
            200,
            {"timestamp": start, "Content-Type": "image/jpg"},
        )

    def get_image(self):
        self.log.info("Image endpoint called")
        start = datetime.datetime.utcnow()
        io_buffer = self.container.get_image()
        return (
            io_buffer.tobytes(),
            200,
            {"timestamp": start, "Content-Type": "application/octet-stream"},
        )

    def get_coordinate(self):
        self.log.info("Coordinate endpoint called")
        start = datetime.datetime.utcnow()
        point: Point2D = self.container.get_coordinate()

        return (
            pickle.dumps(point),
            200,
            {"timestamp": start, "Content-Type": "application/octet-stream"},
        )

    def get_camera_position(self):
        self.log.info("Camera position endpoint called")
        start = datetime.datetime.utcnow()
        point: Point2D = self.container.get_camera_position()

        return (
            pickle.dumps(point),
            200,
            {"timestamp": start, "Content-Type": "application/octet-stream"},
        )

    def get_resolution(self):
        self.log.info("Camera resolution endpoint called")
        start = datetime.datetime.utcnow()
        resolution: Point2D = self.container.get_resolution()

        return (
            pickle.dumps(resolution),
            200,
            {"timestamp": start, "Content-Type": "application/octet-stream"},
        )

    def get_autofocus(self):
        start = datetime.datetime.utcnow()
        autofocus = self.container.get_autofocus()
        self.log.info("Autofocus is %s locally", autofocus)
        return (
            pickle.dumps(autofocus),
            200,
            {"timestamp": start, "Content-Type": "application/octet-stream"},
        )

    def set_autofocus(self, *args, **kwargs):
        self.log.info("Set autofocus endpoint called")
        data = request.args.get("value")
        self.container.set_autofocus(bool(data))
        return "Ok"

    def reset(self):
        self.container.reset()
        self.container = None
