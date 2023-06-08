import math
import cv2 as cv
from time import sleep, time as current_time
from logger import Logger
from threading import Event, Thread
import picamera2
from io import BytesIO


class VideoBuffer:
    def __init__(self, max_frame_count=0, **buffers) -> None:
        self.max_frame_count = max_frame_count
        self.__data = []
        if 'buf_before' in buffers:
            self.__data.extend(buffers['buf_before'])
        if 'buf_after' in buffers:
            self.__data.extend(buffers['buf_after'])

    def __iter__(self):
        for frame in self.__data:
            yield frame

    @property
    def occupied_size(self):
        return len(self.__data)

    def push(self, frame):
        # Ensure a slot of frame in video buffer
        if self.occupied_size >= self.max_frame_count:
            del self.__data[0]  # Remove the 1st frame from video buffer
        # Append frame to the end of data
        self.__data.append(frame)

    def clear(self):
        self.__data.clear()

    def __repr__(self) -> str:
        return f'VideoBuffer[frames_count= {self.occupied_size}]'


class Camera:

    def __init__(self, resolution=(640, 480), framerate=30, vflip=True, duration=5) -> None:
        # Camera params
        self.vflip = vflip
        self.framerate = framerate
        self.resolution = resolution
        # Camera runtime
        self.VIDEO_DURATION = duration
        # Events
        self.recording_signal = Event()
        self.saving_switcher = Event()
        self.suspending_switcher = Event()
        self.initialized_signal = Event()
        self.capture_after_accident_signal = Event()
        # Global runtime
        self.logger = Logger("Camera")
        self.DURATION_FRAMES_COUNT = self.framerate * self.VIDEO_DURATION
        self.video_buffer = VideoBuffer(max_frame_count=self.DURATION_FRAMES_COUNT)
        self.logger.info(f"Created VideoBuffer instance that can hold {self.DURATION_FRAMES_COUNT} frame.")
        # Log
        self.logger.success("Created Camera instance. Waiting for setup...")

    def setup(self):
        # Create camera instance and configure it
        self.picamera = picamera2.Picamera2()
        self.picamera.configure(self.picamera.create_video_configuration())
        self.logger.success("Setup complete. Camera is ready.")

    def start(self):
        self.recording_signal.set()
        # Start a background thread for camera
        self.camera_thread = Thread(name='Camera', target=self.__camera_worker)
        self.camera_thread.start()
        self.logger.info("Started recording.")

    def stop(self):
        if self.recording:
            try:
                self.picamera.close()
                self.recording_signal.clear()
            except RuntimeError:
                self.logger.error("Can't close camera.")

    @property
    def recording(self):
        return self.recording_signal.is_set()

    @property
    def suspended(self):
        return self.suspending_switcher.is_set()

    @property
    def saving(self):
        return self.saving_switcher.is_set()

    @property
    def initialized(self):
        return self.initialized_signal.is_set()

    def suspend(self):
        if not self.suspended:
            self.suspending_switcher.set()

    def resume(self):
        if self.suspended:
            self.suspending_switcher.clear()

    def save_captured_video(self, video_buffer: VideoBuffer, timestamp: int):
        """ Saves the captured video recorded in video buffer to local storage
            then returns the path of it
        Returns:
            str: Path of saved video
        """

        # Set saving switcher flag to true
        self.saving_switcher.set()
        filename = f"{timestamp}.mp4"
        filepath = f"./captures/{filename}"
        try:
            # Save buffer video to file
            fourcc = cv.VideoWriter_fourcc(*'mp4v')
            writer = cv.VideoWriter(filepath, fourcc, self.framerate, self.resolution)
            self.logger.info(f"Saving video in buffer.. Dur[{self.VIDEO_DURATION}] Res[{self.resolution}] FR[{self.framerate}] Frames[{video_buffer.occupied_size}]")
            for frame in video_buffer:
                writer.write(frame)  # Write frame to video file.
            video_buffer.clear()
            self.logger.success("Video was saved successfully to {}".format(filepath))
        except Exception as e:
            self.logger.error(e)
        finally:
            writer.release()
            # Reset flag to continue capturing
            self.saving_switcher.clear()
        # Return the video filename
        return filename

    def __camera_worker(self):
        self.logger.info("Starting Camera...")
        # Start the picamera
        self.picamera.start()
        self.initialized_signal.set()
        # Allow the camera to wrap up
        sleep(0.1)
        # Start capturing frames from camera
        while self.recording:
            # Skip frame if camera is saving video
            if self.saving or self.suspended:
                continue
            self.logger.info("Processing captured frame...")
            # Grab the frame then process it
            frame = self.picamera.capture_array(wait=True)
            # Push frame to video buffer
            self.video_buffer.push(frame)

        # Poweroff camera and join thread
        self.picamera.close()
        self.saving_switcher.clear()
        self.initialized_signal.clear()
        self.suspending_switcher.clear()
        self.capture_after_accident_signal.clear()
        self.logger.info("Stopped recording.")


if __name__ == '__main__':
    camera = Camera(duration=5)
    camera.setup()
    camera.start()
    sleep(5)
    camera.stop()
