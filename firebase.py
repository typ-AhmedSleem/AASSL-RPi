import os
import firebase_admin
from logger import Logger
from firebase_admin import (
    db,
    storage,
    messaging,
    credentials,
)


class Constants:

    STORAGE_BUCKET_NAME = "gs://aas-for-sl.appspot.com"
    DATABASE_URL = "https://aas-for-sl-default-rtdb.firebaseio.com/"
    CREDENTIALS_FILE_PATH = "aas-for-sl-firebase-adminsdk-dznrq-b0280663c2.json"
    TOKEN_REFERENCE = "fcm_token"


class Firebase:

    def __init__(self) -> None:
        self.logger = Logger("Firebase")

    def setup(self):
        self.logger.info("Initializing Firebase...")
        cred = credentials.Certificate(Constants.CREDENTIALS_FILE_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': Constants.DATABASE_URL
        })
        self.logger.info("Initializing Storage...")
        self.storage = FirebaseStorage()
        self.logger.info("Initializing FCM...")
        self.fcm = FirebaseCloudMessaging()
        self.logger.success("Firebase is ready.")


class FirebaseStorage:

    def __init__(self) -> None:
        self.logger = Logger("Firebase:Storage")
        self.bucket = storage.bucket(name=Constants.STORAGE_BUCKET_NAME)

    def upload_file(self, file_path: str, filename: str):
        # Do some checks first
        if len(file_path) == 0 or len(filename) == 0:
            self.logger.error("Given empty filepath or filename. Upload aborted.")
            return
        if not os.path.exists(file_path):
            self.logger.error("Video file provided with path doesn't exist. Upload aborted.")
            return

        # Upload the file
        self.logger.info(f"Preparing to upload file '{file_path}' ...")
        remote_path = filename
        blob_file = self.bucket.blob(remote_path)
        blob_file.upload_from_filename(file_path)


class FirebaseCloudMessaging:

    def __init__(self) -> None:
        self.logger = Logger("Firebase:FCM")
        self.token = ""

    def refresh_token(self):
        try:
            self.logger.info("Refreshing token...")
            ref = db.reference(Constants.TOKEN_REFERENCE)
            new_token = ref.get()
            self.token = new_token
            self.logger.info(f"Token refreshed. {self.token[:14]}")
        except Exception as e:
            self.logger.error(f"Can't refresh token. Reason= {e}")

    def send_notification(self, payload):
        # Check if payload is empty
        if len(payload) == 0:
            self.logger.error("Can't send notification to device. Payload is empty.")
            return

        # Refresh token
        self.refresh_token()

        # Create the message
        accident_msg = messaging.Message(
            data=payload,
            token=self.token
        )

        # Send it
        response: str = messaging.send(accident_msg)
        id_idx = response.find(':') + 1
        self.logger.success(f"Sent message. id= {response[id_idx:]}")


if __name__ == '__main__':
    # Test
    import time
    from data import Accident
    from car import Car, CarInfo

    car = Car(CarInfo(id='5562', model="Toyota Supra", owner="Ahmed Sleem", emergency="010,011"))
    car.setup()
    firebase = Firebase()
    firebase.setup()
    timestamp = time.time() * 1000
    firebase.fcm.send_notification(Accident(
        lat=23.264841,
        lng=-29.53912,
        timestamp=timestamp,
        video_filename=f"{timestamp}.mp4"
    ).as_dict(car))
