import logging
from datetime import datetime
from pathlib import Path


def setup_logging():
    name = datetime.now().strftime("%Y-%m-%dT%H%M%S.log")
    full_path = Path("logs")
    full_path.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(filename=full_path / name, mode="a")
    fh.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[fh, ch],
    )


