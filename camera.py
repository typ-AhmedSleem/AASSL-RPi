import os
import math
import cv2 as cv
from time import sleep
from logger import Logger
from threading import Event, Thread

import utils
from constants import IS_TESTING

if IS_TESTING:
    # Use PC camera (for testing only)
    from pc_toolkit import (
        PCCamera as PiCamera,
        RGBArray as PiRGBArray
    )
else:
    # Picamera on RPi
    from picamera import PiCamera
    from picamera.array import PiRGBArray


class VideoBuffer:

    def __init__(self, framerate=30, max_frame_count=0, **buffers) -> None:
        self.framerate = framerate
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

    @property
    def duration(self):
        return int(round(self.max_frame_count / self.framerate, 0))

    def push(self, frame):
        # Ensure a slot of frame in video buffer
        if self.occupied_size >= self.max_frame_count:
            del self.__data[0]  # Remove the 1st frame from video buffer
        # Append frame to the end of data
        self.__data.append(frame)

    def clear(self):
        self.__data.clear()

    def clone(self):
        return VideoBuffer(
            frame_rate=self.framerate,
            max_frame_count=self.max_frame_count,
            buf_before=self.__data.copy())

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
        self.video_buffer = VideoBuffer(
            frame_rate=self.framerate,
            max_frame_count=self.DURATION_FRAMES_COUNT,
        )
        self.logger.info(f"Created VideoBuffer instance that can hold {self.video_buffer.max_frame_count} frame.")
        self.logger.info("Created Camera instance. Waiting for setup...")

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
        self.camera_thread = Thread(name='CameraThread', target=self.__camera_worker)
        self.camera_thread.start()

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
        saved = False
        # Set saving switcher flag to true
        self.saving_switcher.set()
        filename = f"{timestamp}.mp4"
        filepath = f"./captures/{filename}"
        try:
            # Create captures folder if not exists
            if not utils.captures_dir_exists():
                self.logger.warning("Captures folder not exists. Creating it...")
                created = utils.create_captures_dir()
                if created:
                    self.logger.info("Created captures folder.")
                else:
                    raise Exception("Can't create captures folder.")
            # Save buffer video to file
            fourcc = cv.VideoWriter_fourcc(*'mp4v')
            writer = cv.VideoWriter(filepath, fourcc, self.framerate, self.resolution)
            self.logger.info(f"Saving video in buffer.. Dur[{video_buffer.duration}] Resl[{self.resolution}] FR[{video_buffer.framerate} FPS] Frames[{video_buffer.occupied_size}] to Path[{filepath}]")
            # Write video from buffer to file.
            for frame in video_buffer:
                writer.write(frame)
            # Check saved video filesize
            size = os.path.getsize(filepath)
            if size == 0:
                raise Exception("Something happened while saving video, it's empty.. If you changed resolution of camera, return it to (640,480).")
            # Video file was saved
            saved = True
            self.logger.success("Video was saved successfully to '{}' | Size= ({:.2f} KB)".format(filepath, size / 1024.0))
        except Exception as e:
            self.logger.error(e)
        finally:
            writer.release()
            # Reset flag to continue capturing
            self.saving_switcher.clear()
        # Return the video filename
        return filename if saved else None

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

    @property
    def filling_buffer(self):
        return self.video_buffer.occupied_size < self.video_buffer.max_frame_count

    def wait_until_buffer_filled(self):
        while self.filling_buffer:
            pass

    def suspend(self):
        if not self.suspended:
            self.suspending_switcher.set()
            self.logger.info("Camera suspended.")

    def resume(self):
        if self.suspended:
            self.suspending_switcher.clear()
            self.logger.info("Camera resumed.")

    def create_accident_buffer(self, buffer_before: VideoBuffer, buffer_after: VideoBuffer):
        return VideoBuffer(
            buf_after=buffer_after,
            buf_before=buffer_before,
            framerate=self.framerate,
            max_frame_count=self.DURATION_FRAMES_COUNT * 2
        )

    def __camera_worker(self):
        self.logger.info("Starting Camera...")
        # Wait until camera warms up
        sleep(0.1)
        # Create frame buffer to hold every frame captured
        try:
            self.logger.info("Started recording.")
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

                # Check whether camera switcher is switched off
                if not self.recording:
                    break
            # Switcher is off now
            frame_buffer.close()
            self.picamera.close()
            self.logger.info("Stopped recording.")
        except Exception as e:
            self.logger.error(e)


# if __name__ == '__main__':
#     import utils
#     import math
#     import random
#     # Create captures folder if not exists
#     if not utils.captures_dir_exists():
#         utils.create_captures_dir()
#     # Setup camera instance
#     camera = Camera(
#         resolution=(1920, 1920),
#         framerate=30,
#         duration=1
#     )
#     camera.setup()
#     camera.start()

#     # Get before accident video
#     camera.logger.info("Filling buffer before...")
#     camera.wait_until_buffer_filled()
#     camera.logger.info("Filled buffer before...")
#     camera.suspend()
#     buf_before = camera.video_buffer.clone()
#     camera.video_buffer.clear()

#     # Get after accident video
#     camera.resume()
#     camera.logger.info("Filling buffer after...")
#     camera.wait_until_buffer_filled()
#     camera.logger.info("Filled buffer after...")
#     camera.suspend()
#     buf_after = camera.video_buffer.clone()
#     camera.video_buffer.clear()

#     # Get full accident video
#     buf_total = camera.create_accident_buffer(buf_before, buf_after)

#     # Save total video then stop camera
#     camera.save_captured_video(buf_total, math.ceil(random.uniform(1, 100)))
#     camera.stop()
