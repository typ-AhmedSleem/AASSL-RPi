from logger import Logger
from data import Accident
from car import Car, CarKeys
from accident_reporter import AccidentReporter


class AASSL:

    def __init__(self) -> None:
        # Logger
        self.logger = Logger('AASSL')
        self.logger.info("Starting AASSL...")

        # Car
        self.car = Car()
        if self.car.missing_info:
            self.logger.warning("There's no info associated with car.")
        else:
            self.logger.info(f"CarInfo: {self.car.info}")
            
        # AccidentReporter
        self.firebase = AccidentReporter()

        # Camera
        self.camera = None
        if self.camera is None:
            self.logger.error("No camera was detected.")

        # GPS
        self.gps = None
        if self.gps is None:
            self.logger.error("No GPS module was detected.")

        # GSM
        self.gsm = None
        if self.gsm is None:
            self.logger.error("No GSM module was detected.")

        self.logger.info("System is ready to start...")

    def start_system(self):
        # Setup car
        self.car.setup()
        
        # Setup AccidentReporter
        self.firebase.setup()
        
        # Setup Camera
        
        # Setup GSM
        
        # Setup GPS

    def stop_system(self):
        # Stop system components
        # Exit
        exit(0)


if __name__ == '__main__':
    aassl = AASSL()
    aassl.start_system()
    aassl.stop_system()