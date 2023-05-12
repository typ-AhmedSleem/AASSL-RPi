from time import time as current_time

from logger import Logger
from gps import GPS, Coordinates
from car import Car, CarInfo, CrashDetectorCallback
from accident_reporter import AccidentReporter, Accident


class AASSL(CrashDetectorCallback):

    def __init__(self) -> None:
        self.logger = Logger('AASSL')
        self.logger.info("Starting AASSL...")

        # Car
        self.car = Car(CarInfo.get_default(), self)

        # AccidentReporter
        self.accident_reporter = AccidentReporter()

        # Camera
        self.camera = None
        if self.camera is None:
            self.logger.error("No camera was detected.")

        # GPS
        self.gps = GPS()
        if self.gps is None:
            self.logger.error("No GPS module was detected.")

        # GSM
        self.gsm = None
        if self.gsm is None:
            self.logger.error("No GSM module was detected.")

        self.logger.info("System is ready to start...")

    def setup_system(self):
        # Setup car
        self.car.setup()

        # Setup AccidentReporter
        self.accident_reporter.setup()

        # Setup GPS

        # Setup Camera

    def start_system(self):
        pass

    def stop_system(self):
        # Stop system components
        # Exit
        exit(0)

    def on_accident_happened(self):
        # Build accident
        timestamp = current_time() * 1000  # Timestamp in millis
        filename = f"{timestamp}.mp4"
        location = self.gps.last_known_location
        accident_payload = Accident(
            lat=location.lat,
            lng=location.lng,
            timestamp=timestamp,
            video_filename=filename
        ).as_dict(self.car)


if __name__ == '__main__':
    aassl = AASSL()
    aassl.start_system()
    aassl.stop_system()
