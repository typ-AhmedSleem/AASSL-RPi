import math
from time import time as current_time, sleep

from logger import Logger
from old_camera import Camera, VideoBuffer
from gps import GPS
from car import Car, CarInfo, CrashDetectorCallback
from accident_reporter import AccidentReporter, Accident
import threading


class AASSL(CrashDetectorCallback):

    def __init__(self) -> None:
        self.logger = Logger('AASSL')
        self.logger.info("Starting AASSL...")

        # Car
        self.car = Car(CarInfo.get_default(), self)

        # AccidentReporter
        self.crash_reporter = AccidentReporter()

        # Camera
        self.camera = Camera(duration=5)
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
        self.logger.info("Stopping system...")
        # Stop system components
        self.car.stop()
        self.gps.stop()
        self.camera.stop()
        self.logger.info("System stopped.")
        # Exit
        exit(0)

    def on_accident_happened(self):
        self.logger.info("Received crash signal from CrashDetector. Handling it on thread: {}".format(threading.currentThread().name))
        # Wait until camera is initialized if it not
        if not self.camera.initialized:
            self.logger.info("Waiting for camera to initialize.")
            self.camera.initialized_signal.wait()
            self.logger.info("Camera is initialized.")
        # Build accident model
        timestamp = math.floor(current_time() * 1000)  # Timestamp in millis
        # Get before accident video buffer from camera
        while self.camera.video_buffer.occupied_size < self.camera.video_buffer.max_frame_count:
            self.logger.info("Filling before accident camera buffer. InBufferNow= {}".format(self.camera.video_buffer.occupied_size))
            sleep(0.1)
        
        self.camera.suspend()
        buffer_before_accident = self.camera.video_buffer
        self.logger.info("Grabbed before accident video buffer: {}".format(buffer_before_accident))
        
        # Resume the camera
        self.camera.video_buffer.clear()
        self.logger.info("Capturing 5 secs after accident...")
        # Wait for camera to capture the next 5 secs video
        self.camera.resume()
        while self.camera.video_buffer.occupied_size < self.camera.video_buffer.max_frame_count:
            self.logger.info("Filling after accident camera buffer. InBufferNow= {}".format(self.camera.video_buffer.occupied_size))
            sleep(0.1)
        
        # Get after accident buffer from camera
        buffer_after_accident = self.camera.video_buffer
        self.logger.info("Grabbed after accident video buffer: {}".format(buffer_after_accident))

        buffer_accident_video = VideoBuffer(
            buf_before=buffer_before_accident
        )
        self.logger.info("Total accident video buffer: {}".format(buffer_accident_video))
        # Save the video
        filename = self.camera.save_captured_video(buffer_accident_video, timestamp)
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
        # Resume car crash detector
        self.car.crash_detector.resume()


if __name__ == '__main__':
    aassl = AASSL()
    aassl.setup_system()
    aassl.start_system()
    # aassl.stop_system()
