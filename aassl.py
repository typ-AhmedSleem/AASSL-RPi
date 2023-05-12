from time import time as current_time

from logger import Logger
from camera import Camera
from gps import GPS
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
        self.camera = Camera()
        if self.camera is None:
            self.logger.error("No camera was detected.")

        # GPS
        self.gps = GPS()
        if self.gps is None:
            self.logger.error("No GPS module was detected.")

        self.logger.info("System is ready to start...")

    def setup_system(self):
        self.car.setup()
        self.gps.setup()
        # self.camera.setup()
        self.accident_reporter.setup()

    def start_system(self):
        # Start system components
        self.car.start()
        self.gps.start()
        # self.camera.start()

    def stop_system(self):
        # Stop system components
        self.car.stop()
        self.gps.stop()
        # self.camera.stop()
        # Exit
        exit(0)

    def on_accident_happened(self):
        # Build accident
        timestamp = current_time() * 1000  # Timestamp in millis
        filename = f"{timestamp}.mp4"
        location = self.gps.last_known_location
        accident_payload = Accident(
            lat=location[0],
            lng=location[1],
            timestamp=timestamp,
            video_filename=filename
        ).as_dict(self.car)


if __name__ == '__main__':
    aassl = AASSL()
    aassl.setup_system()
    aassl.start_system()
    aassl.stop_system()
