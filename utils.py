import random
from time import sleep
from os import path, mkdir

CAPTURES_DIR_NAME = 'captures/'
CONFIG_FILENAME = 'config.csv'


def captures_dir_path():
    return path.join('./', CAPTURES_DIR_NAME)


def data_dir_path():
    return path.join('./', 'data')


def config_file_path():
    return path.join('./data/', CONFIG_FILENAME)


def captures_dir_exists():
    return path.exists(captures_dir_path())


def data_dir_exists():
    return path.exists(captures_dir_path())

def config_file_exists() -> bool:
    return path.exists(config_file_path())


def create_captures_dir():
    if not captures_dir_exists():
        try:
            mkdir(captures_dir_path())
        except:
            pass
        finally:
            return True
    return False


def get_capture_file_path(filename: str):
    return path.join(captures_dir_path(), filename)


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


if __name__ == '__main__':

    filename = '123.mp4'
    print()
    print()
    print(captures_dir_path())
    print(get_capture_file_path(filename))
    print()
    print(captures_dir_exists())
    print(capture_file_exists(filename))
    print()
    create_captures_dir()
    print(captures_dir_exists())
    print(capture_file_exists(filename))
