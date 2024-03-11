import logging
from multiprocessing import set_start_method

# noinspection PyUnresolvedReferences
from .strategies.endpoint.http import app

keep_alive = []


print(__name__)
if __name__ == "pulsecontrol.main":
    logger = logging.getLogger("MAIN")
    set_start_method("forkserver")

    # this will automatically start the frontend
    print("Starting", app)
    print(app.url_map)
