import cv2 as cv
from time import sleep
from logger import Logger
from threading import Event, Thread
from numpy import zeros, int8 as INT8

IS_RPI = False
if IS_RPI:
    from picamerax import PiCamera
    from picamerax.array import PiRGBArray


class VideoBuffer:
    def __init__(self, shape=(480, 640, 3), max_frame_count=0, fill=False) -> None:
        self.max_frame_count = max_frame_count
        self.__data = [zeros(shape=shape, dtype=INT8) * max_frame_count] if fill else []

    @property
    def occupied_size(self):
        return len(self.__data)

    def pop(self):
        pass

    def push(self, frame):
        # Ensure a slot of frame in video buffer
        if self.occupied_size >= self.max_frame_count:
            del self.__data[0]  # Remove the 1st frame from video buffer
        # Append frame to the end of data
        self.__data.append(frame)


class Camera:

    def __init__(self, resolution=(640, 480), framerate=15, vflip=True) -> None:
        # Camera params
        self.vflip = vflip
        self.framerate = framerate
        self.resolution = resolution
        # Camera runtime
        self.VIDEO_DURATION = 5
        # Global runtime
        self.switcher = Event()
        self.logger = Logger("Camera")
        self.DURATION_FRAMES_COUNT = self.framerate * self.VIDEO_DURATION
        self.video_buffer = VideoBuffer(self.DURATION_FRAMES_COUNT)
        # Log
        self.logger.success("Setup complete. Camera Ready...")

    def setup(self):
        self.picamera = PiCamera()
        self.picamera.vflip = self.vflip
        self.picamera.framerate = self.framerate
        self.picamera.resolution = self.resolution

    def start(self):
        self.switcher.set()
        # Start a background thread for camera
        self.camera_thread = Thread(name='Camera', target=self.__camera_worker)
        self.camera_thread.start()
        self.logger.info("Started recording.")

    def stop(self):
        if self.switcher.is_set():
            self.switcher.clear()
            self.picamera.close()

    @property
    def recording(self):
        return self.switcher.is_set()

    def save_captured_video(self, timestamp: int):
        """ Saves the captured video recorded in video buffer to local storage
            then returns the path of it
        Returns:
            str: Path of saved video
        """

        fourcc = cv.VideoWriter_fourcc(*'mp4v')
        with cv.VideoWriter("crash.mp4", fourcc, self.framerate, self.resolution) as writer:
            for frame in range(self.DURATION_FRAMES_COUNT):
                writer.write(frame)  # Write frame to video file.
        # Return the video filename
        return f"{timestamp}.mp4"

    def __camera_worker(self):
        # Allow the camera to wrap up
        sleep(0.1)
        # Start capturing frames from camera
        frame_buffer = PiRGBArray(self.picamera, self.resolution)
        for _ in self.picamera.capture_continuous(frame_buffer, format='bgr', use_video_port=True):
            # Grab the frame then process it
            image = frame_buffer.array
            rgb_image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

            # Push frame to video buffer
            self.video_buffer.push(rgb_image)

            # Clear frame buffer to write next frame
            frame_buffer.truncate(0)
            # Check whether camera switcher is switched off
            if not self.switcher.is_set():
                break

        # Switcher is off now
        frame_buffer.close()
        self.picamera.close()
        self.logger.info("Stopped recording.")
        self.camera_thread.join()
