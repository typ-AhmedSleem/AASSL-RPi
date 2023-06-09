# Testing params
IS_TESTING = False

# GPS module UART config
GPS_UART_PORT = '/dev/ttyAMA0'
GPS_UART_BAUDRATE = 9600

# GSM module UART config
GSM_UART_PORT = '/dev/ttyAMA1'
GSM_UART_BAUDRATE = 115200

def set_test_mode(enable: bool = False):
    IS_TESTING = enable

class IOPins:
    PIN_CRASHING_BUTTON = 17 # BCM numbering mode

class FirebaseConstants:

    # FCM
    TOKEN_REFERENCE = "tokens"

    # Storage
    STORAGE_BUCKET_URL = "aas-for-sl.appspot.com"

    # Firebase app
    DATABASE_URL = "https://aas-for-sl-default-rtdb.firebaseio.com/"
    CREDENTIALS_FILE_PATH = "data/aas-for-sl-firebase-adminsdk-dznrq-b0280663c2.json"
