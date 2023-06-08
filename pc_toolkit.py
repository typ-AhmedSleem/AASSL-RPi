import cv2 as cv
import numpy as np
from time import sleep
from logger import Logger
from threading import Event, Thread


class CameraError(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class RGBArray:

    def __init__(self, camera: 'PCCamera', resolution) -> None:
        self.array = None
        self.closed = False

    def truncate(self, size=0):
        pass

    def close(self):
        self.closed = True


class PCCamera:

    def __init__(self) -> None:
        self.cap = None
        self.running_signal = Event()
        self.logger = Logger("PCCamera")

    @property
    def running(self):
        return (self.cap is not None) and self.running_signal.is_set()

    def open(self, cam_index=0):
        if not self.running:
            # Start camera
            self.logger.info("Opening Camera instance...")
            self.cap = cv.VideoCapture(cam_index)
            self.running_signal.set()
            self.logger.success("Opened Camera instance.")

    def capture_continuous(self, output: RGBArray, format='BGR', use_video_port=False):
        """ This method emulates one found in PiCamera to make it possible to test picamera function using pc camera"""
        if not self.running:
            self.open()

        while self.running:
            ret, frame = self.cap.read()
            if ret:
                output.array = frame
                yield "FRAME"
            else:
                break

    def close(self):
        if self.running:
            self.running_signal.clear()
            sleep(0.1)
            self.cap.release()
            self.logger.info("Closed Camera instance.")


class GPS:

    def __init__(self) -> None:
        self.DEFAULT_LOC = (30.0346762, 31.4295489)
        self.switcher = Event()
        self.logger = Logger("GPS")
        self.last_known_location = self.DEFAULT_LOC

    def setup(self):
        self.logger.success("GPS is ready.")

    def start(self):
        if not self.switcher.is_set():
            self.switcher.set()
            self.logger.info("GPS service started.")

    def stop(self):
        if self.switcher.is_set():
            self.switcher.clear()
            self.logger.info("GPS service stopped.")


class gpio:
    
    BCM = 'bcm'
    BOARD = 'board'
    
    IN = 'in'
    OUT = 'out'
    
    HIGH = 'high'
    LOW = 'low'
    
    PUD_DOWN = 'pud_down'
    
    @staticmethod
    def input(pin):
        return gpio.LOW
    
    @staticmethod
    def setmode(mode):
        pass
    
    @staticmethod
    def setwarnings(enable):
        pass
    
    @staticmethod
    def setup(pin, mode, pull=PUD_DOWN):
        pass
    
    @staticmethod
    def cleanup(assert_exists=True):
        pass