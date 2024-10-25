import json
import logging
import threading
from threading import Thread

from flask import Flask, Response, request, abort

from pulsecontrol.helpers.config_loader import ConfigLoader, load_integrator
from pulsecontrol.setup_logging import setup_logging
from pulsecontrol.strategies.integrator import Integrator

logger = logging.getLogger("Frontend")
app = Flask(__name__)
app.config.from_prefixed_env(
    "PULSECTL"
)  # gets all env variables that are prefixed with `PULSECTL_`
logger.info(app.config)

config_loader: ConfigLoader | None = ConfigLoader()
integrator: Integrator | None = None
experiment: Thread | None = None

setup_logging()


@app.post("/load/integrator/<strategy>")
def initialize_strategy(strategy):
    reset()
    global integrator
    logger.info("Initializing the integrator (%s)", strategy)
    if integrator is not None:
        return abort(400)

    data = request.get_json()
    logger.info("Got data:\n%s", json.dumps(data, indent=2))
    integrator = load_integrator(integrator=strategy, config=data)
    return Response("Ok")


@app.route("/continue")
def continue_experiment():
    """
    Call this if the integrator requires a manual intervention to continue
    """
    global integrator
    global experiment
    if integrator is None:
        logger.error("No integrator loaded. Initialize and start it first.")
        return abort(400)

    experiment = threading.Thread(target=integrator.continue_experiment)
    experiment.start()
    return Response("Ok")


@app.route("/start")
def start():
    global integrator
    global experiment
    if experiment is not None:
        try:
            experiment.join()
        except Exception as e:
            logger.error("Last run lead to an exception: %s", e)

    # parameter handling
    target_area = request.args.get("target_area")
    chip_surface_height = request.args.get("chip_surface_height")
    skip_init = request.args.get("skip_init")
    if target_area is None and chip_surface_height is None and skip_init is not None:
        logger.error("Missing parameters, add target_area and surface_height")
        return abort(400)

    logger.info("Starting Run")
    experiment = threading.Thread(
        target=integrator.start,
        kwargs={
            "target_area": target_area,
            "chip_surface_height": chip_surface_height,
            "skip_init": skip_init,
        },
    )
    experiment.start()

    return Response("Ok")


@app.route("/reset")
def reset():
    global config_loader
    global integrator
    global experiment
    if integrator is not None:
        integrator.reset()
        integrator = None
    if config_loader is not None:
        config_loader.reset()
    config_loader = None
    if experiment is not None:
        try:
            experiment.join(10)
        except Exception as e:
            logger.error("Got error: %s" % e)
        experiment = None
    return Response("Ok")


@app.get("/healthcheck")
def health_check():
    return Response("Ok")

