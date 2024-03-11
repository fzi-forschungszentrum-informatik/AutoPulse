import importlib
from enum import Enum
from pathlib import Path

from dacite import from_dict, MissingValueError, Config

from pulsecontrol.helpers import HasLogger, ConfigurationError, Point2D
from pulsecontrol.helpers.remote_loader import RemoteInit


def load_integrator(integrator: str, config: dict):
    return load_dacite("integrator", module_name=integrator, config=config)


def load_remote(strategy_type: str, config: dict) -> RemoteInit:
    return load_dacite(
        strategy_type,
        module_name="http_wrapper",
        config=config,
        class_name="HttpWrapperRemote",
    )


def from_dict_casts(strategy, data: dict):
    return from_dict(
        strategy,
        data=data,
        config=Config(cast=[tuple, Enum, Path], type_hooks={Point2D: Point2D.from_iter}),
    )


def load_dacite(strategy_type: str, module_name: str, config: dict, class_name: str = ""):
    # module_name = reduce(lambda x, y: x + ('_' if y.isupper() else '') + y, class_name).lower()
    if not class_name:
        class_name = module_name.title().replace("_", "")
    path = Path(f"src/pulsecontrol/strategies/{strategy_type}/{module_name}.py")
    if not path.is_file():
        raise ConfigurationError(
            "There is no %s strategy with this name: %s" % (strategy_type, module_name)
        )
    try:
        mod = importlib.import_module(f"pulsecontrol.strategies.{strategy_type}.{module_name}")
    except ModuleNotFoundError as e:
        raise ConfigurationError(
            "Selected strategy doesn't exist, do you have a typo in the config?"
        ) from e

    try:
        strategy = getattr(mod, class_name)
    except AttributeError as e:
        raise ConfigurationError("Selected strategy not found %s" % class_name) from e
    try:
        strategy = from_dict_casts(strategy, config)
    except MissingValueError as e:
        raise ConfigurationError("Config variables don't fit the strategy you selected") from e

    return strategy


class ConfigLoader(HasLogger):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._http_wrappers: dict[str, RemoteInit] = dict()

    def add(self, strategy: str, config: dict):
        self._http_wrappers["strategy"] = load_remote(strategy, config)

    def reset(self):
        for strats in self._http_wrappers.values():
            strats.reset()
        self._http_wrappers.clear()
