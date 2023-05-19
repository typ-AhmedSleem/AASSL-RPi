import math
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
        self.crash_reporter = AccidentReporter()

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
        self.camera.setup()
        self.crash_reporter.setup()

    def start_system(self):
        # Start system components
        self.car.start()
        self.gps.start()
        self.camera.start()

    def stop_system(self):
        # Stop system components
        self.car.stop()
        self.gps.stop()
        self.camera.stop()
        # Exit
        exit(0)

    def on_accident_happened(self):
        self.logger.info("Received crash signal from CrashDetector. Handling...")
        
        # Build accident #
        timestamp = math.floor(current_time() * 1000)  # Timestamp in millis
        filename = self.camera.save_captured_video(timestamp)
        location = self.gps.last_known_location
        accident = Accident(
            lat=location[0],
            lng=location[1],
            timestamp=timestamp,
            video_filename=filename
        )
        
        # Report accident
        self.logger.info("Build accident record:\n{}".format(accident.as_json(self.car)))
        self.crash_reporter.report_accident(accident.as_dict(self.car))


if __name__ == '__main__':
    aassl = AASSL()
    aassl.setup_system()
    aassl.start_system()
    # aassl.stop_system()
