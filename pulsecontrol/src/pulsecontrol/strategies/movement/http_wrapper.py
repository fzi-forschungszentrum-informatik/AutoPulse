from dataclasses import dataclass

import requests

from pulsecontrol.helpers import Point2D
from pulsecontrol.helpers.http_wrapper import HttpWrapperHelper
from pulsecontrol.strategies.endpoint.http import app
from pulsecontrol.strategies.movement import MovementStrategy


@dataclass(kw_only=True)
class HttpWrapper(HttpWrapperHelper, MovementStrategy):
    endpoints = {"__next__": "next"}

    def __post_init__(self):
        for fnk, endpoint in self.endpoints.items():
            app.get("/" + self.strategy + "/" + endpoint)(getattr(self, fnk + "endpoint"))

    def __next__endpoint(self):
        return next(self.config[self.strategy])

    def __next__(self) -> Point2D:
        remote = self.get_remote()
        x, y = map(float, requests.get(remote).text.split())
        return x, y
