import datetime
import logging
from dataclasses import dataclass, field
from pathlib import Path

from pulsecontrol.strategies.loggers import Logger


@dataclass(kw_only=True)
class FileLogger(Logger):
    base_path: Path
    current_file: Path | None = field(init=False)

    def __post_init__(self):
        self.setup_handlers()

    def setup_handlers(self):
        name = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S.log")
        fh = logging.FileHandler(filename=Path(self.base_path, name), mode="a")
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARN)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[fh, ch],
        )

    def reset(self):
        self.setup_handlers()
