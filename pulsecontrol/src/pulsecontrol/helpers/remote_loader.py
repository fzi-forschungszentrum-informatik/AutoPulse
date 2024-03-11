from dataclasses import dataclass, InitVar

import requests

from pulsecontrol.strategies import Strategy

# Represents the base url for further api access
# Represents the protocol, hostname/IP and Port
URL = str


@dataclass(kw_only=True)
class RemoteInit(Strategy):
    """
    Use this in the config to initialize a remote device.
    """

    remote_device: URL
    config: InitVar[dict]

    def __post_init__(self, config: dict):
        requests.post(
            "/".join((self.remote_device, self.strategy, "load")),
            json=config,
        )

    def reset(self):
        requests.get(self.remote_device + "/reset")
