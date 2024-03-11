import sys
from dataclasses import dataclass
from typing import Union, Dict, List, Tuple

import requests

from pulsecontrol.helpers.remote_loader import RemoteInit


@dataclass(kw_only=True)
class HttpWrapperHelper(RemoteInit):
    def get_remote(self, how_much_back: int = 1):
        base = sys._getframe()
        for _ in range(how_much_back):
            base = base.f_back

        return "/".join((self.remote_device, self.strategy, base.f_code.co_name))

    def _raw_result(self, params: Union[Dict, List[Tuple], bytes] = None):
        data = self._request(how_much_back=3, params=params)
        match data.status_code:
            case 200:
                return data.content
            case _:
                raise ValueError("Server error!", data)

    def _json_result(self, params: Union[Dict, List[Tuple], bytes] = None):
        return self._request(how_much_back=3, params=params).json()

    def _request(self, how_much_back=2, params: Union[Dict, List[Tuple], bytes] = None):
        return requests.get(self.get_remote(how_much_back=how_much_back), params=params)
