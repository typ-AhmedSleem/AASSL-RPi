# import cv2 as cv
# import numpy as np
# from time import sleep

# cap = cv.VideoCapture(0)

# while True:

#     ret, image = cap.read()
#     if ret:

#     else:
# break
# cap.release()

if __name__ == '__main__':

    # Test System
    import utils
    import random
    from time import time as current_time, sleep
    from car import Car, CrashDetectorCallback
    from accident_reporter import AccidentReporter, Accident

    class Callback(CrashDetectorCallback):

        def on_accident_happened(self):
            sleep(0.5)
            reporter.logger.info("Creating accident record...")
            # Build accident
            timestamp = current_time() * 1000  # Timestamp in millis
            filename = f"{timestamp}.mp4"
            accident = Accident(
                lat=random.random() * 30,
                lng=-random.random() * 30,
                timestamp=timestamp,
                video_filename=filename
            )

            # Create dummy video file with no contents
            with open("data/test.mp4", 'rb') as input:
                utils.create_captures_dir()
                with open(utils.get_capture_file_path(filename), 'wb') as output:
                    output.write(input.read())

            # Broadcast accident
            reporter.logger.info("Build accident record:\n{}".format(accident.as_json(car)))
            reported = reporter.report_accident(accident.as_dict(car))
            if reported:
                car.crash_detector.stop()
            else:
                sleep(1)
                car.crash_detector.resume()

    # AccidentReporter instance
    reporter = AccidentReporter()
    reporter.setup()

    # Car instance
    car = Car(Car.build_car_info(
        id='5562',
        model="Toyota Supra",
        owner="Ahmed Sleem",
        emergency="01029787124,01553106473"), Callback())

    car.setup()
    car.start()
