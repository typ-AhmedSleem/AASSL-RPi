import math
import cv2 as cv
from time import sleep, time as current_time
from logger import Logger
from threading import Event, Thread
from numpy import zeros, int8 as INT8
# Picamera
from picamera import PiCamera
from picamera.array import PiRGBArray


class VideoBuffer:
    
    def __init__(self, max_frame_count=0, **buffers) -> None:
        self.max_frame_count = max_frame_count
        self.__data = []
        if 'buf_before' in buffers:
            self.__data + buffers['buf_before'].__data
        if 'buf_after' in buffers:
            self.__data + buffers['buf_after'].__data
            
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
        print("Buffer cleared.")

    def __repr__(self) -> str:
        return f'VideoBuffer[frames_count= {self.occupied_size}]'

class Camera:

    def __init__(self, resolution=(640, 480), framerate=30, vflip=False, duration=5) -> None:
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
        self.picamera = PiCamera()
        self.picamera.vflip = self.vflip
        self.picamera.framerate = self.framerate
        self.picamera.resolution = self.resolution
        self.initialized_signal.set()
        self.logger.success("Setup complete. Camera is ready.")

    def start(self):
        self.recording_signal.set()
        # Start a background thread for camera
        self.camera_thread = Thread(name='Camera', target=self.__camera_worker)
        self.camera_thread.start()
        self.logger.info("Started recording.")

    def stop(self):
        if self.recording:
            self.recording_signal.clear()
            self.picamera.close()

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
            self.logger.info("Camera suspended.")

    def resume(self):
        if self.suspended:
            self.suspending_switcher.clear()
            self.logger.info("Camera resumed.")

    def __camera_worker(self):
        self.logger.info("Starting Camera...")
        # Allow the camera to wrap up
        sleep(0.1)
        # Create frame buffer to hold every frame captured
        try:
            frame_buffer = PiRGBArray(self.picamera, self.resolution)
            # Start capturing frames from camera
            for _ in self.picamera.capture_continuous(frame_buffer, format='bgr', use_video_port=True):
                # Skip frame if camera is saving video or camera is suspended
                if self.saving or self.suspended:
                    continue
                # Grab the frame then process it
                image = frame_buffer.array

                # Push frame to video buffer
                self.video_buffer.push(image)

                # Clear frame buffer to write next frame
                frame_buffer.truncate(0)
                # self.logger.info("Pushed frame to buffer.")
                # Check whether camera switcher is switched off
                if not self.recording:
                    break
            # Switcher is off now
            frame_buffer.close()
            self.picamera.close()
            self.logger.info("Stopped recording.")
        except:
            pass


if __name__ == '__main__':
    import utils
    import random
    if not utils.captures_dir_exists():
        utils.create_captures_dir()
    
    dur = random.uniform(1,11)
    camera = Camera(duration=dur)
    camera.setup()
    camera.start()
    sleep(dur)
    camera.save_captured_video(camera.video_buffer,random.uniform(1,1000000))
    camera.stop()
