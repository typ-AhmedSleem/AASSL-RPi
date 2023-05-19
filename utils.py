import random
from time import sleep
from os import path, mkdir

CAPTURES_DIR_NAME = 'captures/'


def get_captures_dir_path():
    return path.join('./', CAPTURES_DIR_NAME)


def captures_dir_exists():
    return path.exists(get_captures_dir_path())


def create_captures_dir():
    if not captures_dir_exists():
        try:
            mkdir(get_captures_dir_path())
        except:
            pass
        finally:
            return True


def get_capture_file_path(filename: str):
    return path.join(get_captures_dir_path(), filename)


def capture_file_exists(filename: str) -> bool:
    return path.exists(get_capture_file_path(filename))


def isempty(s: str):
    if s is None or len(s) == 0:
        return True
    if isinstance(s, str):
        return s.strip() == ''


def enable_debug_log(enable=False):
    import logging
    logging.basicConfig(level=logging.DEBUG if enable else logging.INFO)


class gpio:

    IN, OUT = 'in', 'out'
    BOARD, BCM = 'board', 'bcm'
    LOW, HIGH = 0, 1

    @staticmethod
    def setmode(mode):
        pass

    @staticmethod
    def setup(pin, mode, pullup):
        pass

    @staticmethod
    def cleanup(pin=None, assert_exists=True):
        pass

    @staticmethod
    def input(pin) -> int:
        sleep(1)
        return random.choice([0, 1])


if __name__ == '__main__':

    filename = '123.mp4'

    print()
    print()
    print(get_captures_dir_path())
    print(get_capture_file_path(filename))
    print()
    print(captures_dir_exists())
    print(capture_file_exists(filename))
    print()
    create_captures_dir()
    print(captures_dir_exists())
    print(capture_file_exists(filename))
