import cv2 as cv
import numpy as np
from time import sleep


class PiRGBArray:

    def __init__(self, picamera: 'PiCamera', res) -> None:
        self.array = None

    def close(self):
        pass

    def truncate(self, size=0):
        pass


class PiCamera:

    def __init__(self, resolution=(640, 480), framerate=15, vflip=True) -> None:
        self.vflip = vflip
        self.framerate = framerate
        self.resolution = resolution
        self.running = False

    def start(self):
        self.running = True
        self.cap = cv.VideoCapture(0)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

    def close(self):
        self.cap.release()
        self.running = False

    def capture_continuous(self, frame_buffer: PiRGBArray, format='bgr', use_video_port=False):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                image = np.array(frame)
                frame_buffer.array = image
                yield image
            else:
                self.running = False
                break
