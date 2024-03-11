from dataclasses import dataclass

from pulsecontrol.strategies import Strategy


@dataclass(kw_only=True)
class Logger(Strategy):
    """
    This is only designed to set up the default python logger with certain default parameters.
    """

    strategy: str = "logger"
