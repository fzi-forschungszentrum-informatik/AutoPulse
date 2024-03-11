from dataclasses import dataclass

from pulsecontrol.strategies.injector import InjectorStrategy


@dataclass(kw_only=True)
class Mock(InjectorStrategy):
    def inject(self, count: int):
        pass

    def arm(self):
        pass

    def disarm(self):
        pass

    def reset(self):
        pass

    test: str = "test"
