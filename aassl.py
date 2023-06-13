import math
from time import time as current_time

from logger import Logger
from camera import Camera
from crash_reporter import AccidentReporter, Accident
from car import Car, CarInfo, CrashDetectorCallback, InterruptionService

from threading import Event

from constants import IS_TESTING, FirebaseConstants

if IS_TESTING:
    # Use emulated GPS
    from pc_toolkit import GPS
else:
    # Use actual GPS module
    from gps import GPS


class AASSL(CrashDetectorCallback, InterruptionService.Callback):

    def __init__(self) -> None:
        self.logger = Logger('AASSL')
        self.setup_signal = Event()
        self.running_signal = Event()
        self.logger.info("Creating AASSL instance...")

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

        # InterruptionService
        self.interruption_service = InterruptionService(self)

        self.logger.success("Created AASSL instance. Waiting for setup...")

    def system_ready(self):
        return self.setup_signal.is_set()
    
    def system_running(self):
        return self.running_signal.is_set()

    def setup_system(self):
        if self.system_ready():
            self.logger.warning("System setup already done.")
            return
        
        try:
            self.car.setup()
            self.gps.setup()
            self.camera.setup()
            self.crash_reporter.setup()
            
            self.setup_signal.set()
        except KeyboardInterrupt:
            self.logger.error("SETUP WAS INTERRUPTED")
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                self.running_signal.clear()
                self.logger.error(f"Couldn't find firebase config at path: '{FirebaseConstants.CREDENTIALS_FILE_PATH}'")
            self.logger.error("One or more system components failed to setup. {}".format(e))

    def start_system(self):
        if not self.system_ready():
            self.logger.warning("System isn't ready yet. Please setup the system first.")
            return
        
        if self.system_running():
            self.logger.warning("System is already running.")
            return
        
        try:
            self.running_signal.set()
            self.logger.info("Starting system...")
            # Start system components
            self.car.start()
            self.gps.start()
            self.camera.start()
            self.interruption_service.start()
        except Exception:
            self.running_signal.clear()
            self.logger.error("One or more system components failed to start.")

    def stop_system(self):
        if not self.system_running():
            self.logger.warning("System isn't running to stop it.")
            return
        try:
            self.running_signal.clear()
            self.logger.info("Stopping system...")
            # Stop system components
            self.car.stop()
            self.gps.stop()
            self.camera.stop()
            self.logger.info("System stopped.")
        except:
            self.logger.error("One or more system components failed to stop.")
        finally:
            # Exit
            exit(0)

    def on_interrupt(self):
        self.logger.info("SYSTEM WAS INTERRUPTED.")
        return self.stop_system()

    def on_accident_happened(self):
        self.logger.info("Received crash signal from CrashDetector. Handling it...")
        # Wait until camera is initialized if it not
        if not self.camera.initialized:
            self.logger.info("Waiting for camera to initialize.")
            self.camera.initialized_signal.wait()
            self.logger.info("Camera is initialized.")
        # Build accident model
        timestamp = math.floor(current_time() * 1000)  # Timestamp in millis
        # Get before accident video buffer from camera
        self.camera.wait_until_buffer_filled()

        self.camera.suspend()
        buffer_before_accident = self.camera.video_buffer.clone()
        self.logger.info("Grabbed before accident video buffer: {}".format(buffer_before_accident))

        # Resume the camera
        self.camera.video_buffer.clear()
        self.logger.info("Capturing 5 secs after accident...")
        # Wait for camera to capture the next 5 secs video
        self.camera.resume()
        self.camera.wait_until_buffer_filled()

        # Get after accident buffer from camera
        buffer_after_accident = self.camera.video_buffer.clone()
        self.logger.info("Grabbed after accident video buffer: {}".format(buffer_after_accident))

        buffer_accident_video = self.camera.create_accident_buffer(
            buffer_before=buffer_before_accident,
            buffer_after=buffer_after_accident
        )
        self.camera.video_buffer.clear()
        self.logger.info("Total accident video buffer: {}".format(buffer_accident_video))
        # Save the video
        filename = self.camera.save_captured_video(buffer_accident_video, timestamp)
        if filename is None:
            self.logger.error("Camera was unable to save accident video. Aborted reporting.")
            return
        
        # Get last known location from GPS
        location = self.gps.last_known_location
        
        # Build accident model
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
