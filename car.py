
from time import sleep
from json import dumps as to_json
from threading import Thread, Event

from logger import Logger
from crash_reporter import CarKeys
from constants import IS_TESTING, IOPins

from utils import isempty, config_file_path, data_dir_exists, config_file_exists

if IS_TESTING:
    from pc_toolkit import gpio
else:
    import RPi.GPIO as gpio


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
        return CarInfo(
            id='',
            model='',
            owner='',
            emergency=''
        )


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
            self.power_signal.clear()

    def suspend(self):
        if self.detection_signal.is_set():
            self.detection_signal.clear()
            self.logger.info("Service suspended.")

    def resume(self):
        if not self.detection_signal.is_set():
            self.detection_signal.set()
            self.logger.info("Service resumed.")

    def __crash_detector_job(self):
        # Setup gpio (if needed)
        gpio.setmode(gpio.BCM)
        gpio.setwarnings(False)
        gpio.setup(IOPins.PIN_CRASHING_BUTTON, gpio.IN, gpio.PUD_DOWN)
        prev_state = gpio.LOW
        # Start detection
        self.logger.success("CrashDetection service started running.")
        while self.detection_signal.wait():
            # Check if crashing button was pressed
            state = gpio.input(IOPins.PIN_CRASHING_BUTTON)
            if IS_TESTING:
                #HACK START
                prev_state = gpio.LOW
                sleep(5)
                state = gpio.HIGH
                #HACK END
            if prev_state != state:
                if prev_state == gpio.LOW and state == gpio.HIGH:
                    # Crashhhhhhhhhhhhh ~(@-^-@)~
                    self.suspend()  # Suspend thread.
                    self.logger.info("Crash detected. Notifying system...")
                    self.callback.on_accident_happened()  # Notify callback.
                # Update previous state
                prev_state = state
            # Stop detection if power signal is not set
            if not self.power_signal.is_set():
                self.logger.info("Stopping service...")
                self.suspend()
                break
            sleep(0.1)
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

    @staticmethod
    def get_default_info():
        return CarInfo.get_default()

    @staticmethod
    def build_car_info(id: str, model: str, owner: str, emergency: str):
        return CarInfo(id, model, owner, emergency)

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
        # Check car info
        if not self.missing_info:
            return

        # Retreive info from config
        self.retreive_info_from_config()

        # Check for missings
        if not self.has_chassisid:
            self.logger.info("No chassis id was set. Asking user to add it...")
            self.info.mapped[CarKeys.CAR_ID] = input('Enter chassis id: ')
            if not self.has_chassisid:
                self.logger.error("Car chassis-id can't be empty.")
                raise ValueError

        if not self.has_model:
            self.logger.info("No model was set. Asking user to add it...")
            self.info.mapped[CarKeys.CAR_MODEL] = input('Enter car model: ')
            if not self.has_model:
                self.logger.error("Car model can't be empty.")
                raise ValueError

        if not self.has_owner:
            self.logger.info("No owner for this car. Asking user to add it...")
            self.info.mapped[CarKeys.CAR_OWNER] = input('Enter car owner: ')
            if not self.has_owner:
                self.logger.error("Car owner can't be empty.")
                raise ValueError

        if len(self.emergency_contacts) == 0:
            self.logger.info("No chassis id was set. Asking user to add it...")

            pri_emerg = input('Enter primary emergency contact: ')
            if isempty(pri_emerg):
                self.logger.error("Primary contact can't be empty.")
                raise ValueError
            sec_emerg = input('Enter secondary emergency contact: ')
            if isempty(sec_emerg):
                self.logger.warning("Secondary contact you entered is empty but it's optional.")

            self.info.mapped[CarKeys.EMERGENCY] = f"{pri_emerg},{sec_emerg}"

        # Save info to config
        if data_dir_exists():
            with open(config_file_path(), 'w') as config:
                config.writelines([
                    f"{CarKeys.CAR_ID},{self.chassis_id}\n",
                    f"{CarKeys.CAR_MODEL},{self.model}\n",
                    f"{CarKeys.CAR_OWNER},{self.owner}\n",
                    f"{CarKeys.EMERGENCY},{self.emergency_contacts}\n",
                ])
                
        self.logger.info(f"CarInfo was set:\n{self.info}")

    def start(self):
        self.crash_detector.start()

    def stop(self):
        self.crash_detector.stop()

    def retreive_info_from_config(self):
        # Retrev info from config (if found)
        if config_file_exists():
            self.logger.info("Found config file. Retreving car info...")
            with open(config_file_path(), 'r') as config:
                for line in config.readlines():
                    if isempty(line):
                        continue
                    fields = line.split(',')
                    key = fields[0]
                    if isempty(key) or (key not in CarKeys.as_list()):
                        continue
                    if key == CarKeys.EMERGENCY:
                        if len(fields[1:]) == 2:
                            value = f"{fields[1]},{fields[2]}"
                        else:
                            value = f"{fields[1].strip()},"
                    else:
                        value = fields[1]
                    self.info.mapped[key] = value.strip()

    @property
    def missing_info(self):
        return not self.has_chassisid or not self.has_model or not self.has_owner or len(self.emergency_contacts) == 0

    @property
    def chassis_id(self):
        return self.info.mapped.get(CarKeys.CAR_ID, '')

    @property
    def has_chassisid(self):
        return not isempty(self.chassis_id)

    @property
    def model(self):
        return self.info.mapped.get(CarKeys.CAR_MODEL, '')

    @property
    def has_model(self):
        return not isempty(self.model)

    @property
    def owner(self):
        return self.info.mapped.get(CarKeys.CAR_OWNER, '')

    @property
    def has_owner(self):
        return not isempty(self.owner)

    @property
    def emergency_contacts(self):
        return self.info.mapped.get(CarKeys.EMERGENCY, '')


class InterruptionService:

    class Callback:

        def on_interrupt(self):
            pass

    def __init__(self, callback: Callback) -> None:
        self.switcher = Event()
        self.callback = callback

    def start(self):
        if not self.switcher.is_set():
            self.switcher.set()
            Thread(name="InterruptionService", target=self.__service_job()).start()

    def __service_job(self):
        while self.switcher.is_set():
            try:
                sleep(0.05)
            except KeyboardInterrupt:
                self.callback.on_interrupt()
                self.switcher.clear()
                break


class TestCallback(CrashDetectorCallback):

    def on_accident_happened(self):
        sleep(2)
        car.crash_detector.resume()


if __name__ == '__main__':
    car = Car(CarInfo.get_default(), TestCallback())
    car.setup()
    car.start()
