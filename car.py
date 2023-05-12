from time import sleep
from utils import gpio
from data import CarKeys
from logger import Logger
from json import dumps as to_json
from threading import Thread, Event
from constants import CarConstants, IOPins


class CarInfo:

    def __init__(self, id: str = '', model: str = '', owner: str = '', emergency: str = '') -> None:
        self.mapped = {
            CarKeys.CAR_ID: id,
            CarKeys.CAR_MODEL: model,
            CarKeys.CAR_OWNER: owner,
            CarKeys.EMERGENCY: emergency
        }

    def __repr__(self) -> str:
        return str(to_json(self.mapped, indent=2))

    @staticmethod
    def get_default():
        return CarConstants.DEFAULT_CAR_INFO


class CrashDetectorCallback:

    def on_accident_happened(self):
        pass


class CrashDetector:

    def __init__(self, callback: CrashDetectorCallback, power_signal: Event, detection_signal: Event) -> None:
        self.logger = Logger("Car:CrashDetector")
        # Callback & Signals
        self.callback = callback
        self.power_signal = power_signal
        self.detection_signal = detection_signal

    def start(self):
        if not self.power_signal.is_set():
            self.power_signal.set()
            self.detection_signal.set()
            Thread(name="CrashDetector", target=self.__crash_detector_job).start()

    def stop(self):
        if self.power_signal.is_set():
            self.detection_signal.clear()
            self.power_signal.clear()

    def __crash_detector_job(self):
        # Setup gpio (if needed)
        gpio.setmode(gpio.BCM)
        gpio.setup(pin=IOPins.PIN_CRASHING_BUTTON, mode=gpio.IN, pullup=True)
        prev_state = gpio.LOW
        # Start detection
        self.logger.success("CrashDetection service started running.")
        while self.detection_signal.wait():
            # Check if crashing button was pressed
            state = gpio.input(IOPins.PIN_CRASHING_BUTTON)
            # Fire callback if button is pushed
            if prev_state != state:
                if prev_state == gpio.LOW and state == gpio.HIGH:
                    # Crash happened
                    prev_state = state # Update prev state.
                    self.detection_signal.clear()  # Suspend thread.
                    self.callback.on_accident_happened() # Fire callback.
            # Stop detection if power signal is not set
            if not self.power_signal.is_set():
                self.detection_signal.clear()
                break
        gpio.cleanup(assert_exists=False)
        self.logger.info("CrashDetection service stopped running.")


class Car:

    def __init__(self, info: CarInfo, callback: CrashDetectorCallback) -> None:
        self.logger = Logger("Car")

        self.info = info
        self.callback = callback

        # CrashDetector signals
        self.power_signal = Event()
        self.detection_signal = Event()

        # Check car info
        if self.missing_info:
            self.logger.warning("There's no info associated with this car.")

    def setup(self):
        self.logger.info("Intializing car...")

        # Set car info (if needed)
        self.set_car_info()

        # Setup CrashDetector
        self.power_signal.clear()
        self.detection_signal.clear()
        self.crash_detector = CrashDetector(self.callback, self.power_signal, self.detection_signal)

        self.logger.success("Car is ready.")

    def set_car_info(self):
        if len(self.chassis_id) == 0:
            self.logger.warning("No chassis id was set. Asking user to add it...")
            self.info.mapped[CarKeys.CAR_ID] = input('Enter chassis id: ')

        if len(self.model) == 0:
            self.logger.warning("No model was set. Asking user to add it...")
            self.info.mapped[CarKeys.CAR_MODEL] = input('Enter car model: ')

        if len(self.owner) == 0:
            self.logger.warning("No owner for this car. Asking user to add it...")
            self.info.mapped[CarKeys.CAR_OWNER] = input('Enter car owner: ')

        if len(self.emergency_contacts) == 0:
            self.logger.warning("No chassis id was set. Asking user to add it...")
            pri_emerg = input('Enter primary emergency contact: ')
            sec_emerg = input('Enter secondary emergency contact: ')
            self.info.mapped[CarKeys.EMERGENCY] = f"{pri_emerg},{sec_emerg}"

        self.logger.info(f"CarInfo was set: {self.info}")

    def start(self):
        self.crash_detector.start()

    def stop(self):
        self.crash_detector.stop()

    @property
    def missing_info(self):
        return len(self.chassis_id) == 0 or len(self.model) == 0 or len(self.owner) == 0 or len(self.emergency_contacts) == 0

    @property
    def chassis_id(self):
        return self.info.mapped.get(CarKeys.CAR_ID, '')

    @property
    def model(self):
        return self.info.mapped.get(CarKeys.CAR_MODEL, '')

    @property
    def owner(self):
        return self.info.mapped.get(CarKeys.CAR_OWNER, '')

    @property
    def emergency_contacts(self):
        return self.info.mapped.get(CarKeys.EMERGENCY, '')
