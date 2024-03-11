from dataclasses import dataclass, field
from multiprocessing import Process, SimpleQueue
from time import time, sleep

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import logging
    from unittest.mock import MagicMock

    logging.error("RPi Module not installed, this is OK if not executed on a pi.")
    # This is a stub which allows us to run the code in environments without the picamera module
    GPIO = MagicMock()

from pulsecontrol.helpers import HasLogger
from pulsecontrol.strategies.dut import DutStrategy, InjectionResult

MULTI = False


@dataclass(kw_only=True)
class SimpleTarget(DutStrategy, HasLogger):
    simple_target: bool  # selection flag for dacite
    run_pin: int = 2
    fault_pin: int = 3
    reset_pin: int = 4

    _counter: int = field(default=0, repr=False)
    move_after: int = 20

    _state: InjectionResult = field(default=InjectionResult.FAILURE, repr=False)
    _queue: SimpleQueue = field(default_factory=SimpleQueue, repr=False)
    _gpio_waiter: Process = field(init=False, repr=False, default=None)

    def move(self) -> bool:
        return not bool(self._counter % self.move_after)

    def set_waiter(self):
        self._gpio_waiter = Process(
            target=self.busy_wait, name="gpio-waiter", args=(self._queue,), daemon=True
        )

    def restart_board(self):
        # clear queue
        GPIO.event_detected(self.fault_pin)
        GPIO.output(self.reset_pin, False)
        start = time()
        while not GPIO.event_detected(self.fault_pin) and start + 1 > time():
            sleep(0.1)

        # clear queue
        GPIO.event_detected(self.run_pin)
        GPIO.output(self.reset_pin, True)
        start = time()
        while not GPIO.event_detected(self.run_pin) and start + 1 > time():
            sleep(0.1)

        # clear queue again
        GPIO.event_detected(self.run_pin)
        GPIO.event_detected(self.fault_pin)

    def __post_init__(self):
        GPIO.setmode(GPIO.BCM)
        if MULTI:
            self.set_waiter()

    def start(self):
        # GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.reset_pin, GPIO.OUT)
        if not MULTI:
            GPIO.setup(self.fault_pin, GPIO.IN)
            GPIO.setup(self.run_pin, GPIO.IN)
            GPIO.remove_event_detect(self.fault_pin)
            GPIO.remove_event_detect(self.run_pin)
            GPIO.add_event_detect(self.fault_pin, edge=GPIO.BOTH, bouncetime=20)
            GPIO.add_event_detect(self.run_pin, edge=GPIO.BOTH, bouncetime=20)

        # Pull up to turn board on
        GPIO.output(self.reset_pin, True)

        if MULTI:
            self.set_waiter()
            self._gpio_waiter.start()

    def busy_wait(self, messages: SimpleQueue):
        last = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.fault_pin, GPIO.IN)
        GPIO.setup(self.run_pin, GPIO.IN)
        while True:
            if GPIO.input(self.fault_pin):
                messages.put(InjectionResult.SUCCESS)
                return

            if GPIO.input(self.run_pin):
                last = time()
                self.log.info("last: ", last)

            if last + 3.0 < time():
                messages.put(InjectionResult.RESET)
                return

    def check_success(self) -> InjectionResult:
        self._counter += 1

        if MULTI:
            if self._gpio_waiter.is_alive():
                return InjectionResult.FAILURE

            result = self._queue.get()
            match result:
                case InjectionResult.SUCCESS:
                    self.log.info("Injection successful!")
                    self._counter = 0
                case InjectionResult.RESET:
                    self.log.info("Board unresponsive, resetting")
                    self.restart_board()

            self.set_waiter()
            self._gpio_waiter.start()
            return result
        else:
            if GPIO.event_detected(self.fault_pin):
                self.log.info("Injection successful!")
                # self._counter = 0
                return InjectionResult.SUCCESS
            if not GPIO.event_detected(self.run_pin):
                self.log.info("Board unresponsive, resetting")
                self.restart_board()
                return InjectionResult.RESET
            else:
                return InjectionResult.FAILURE

    def reset(self):
        super().reset()
        GPIO.cleanup()
        if MULTI:
            self._queue.close()
            self._gpio_waiter.terminate()
            self._gpio_waiter.join()
            self._queue = SimpleQueue()
            self.set_waiter()
        self._counter = 0
