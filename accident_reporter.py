import utils
import firebase_admin
from logger import Logger
from firebase_admin import (
    db,
    storage,
    messaging,
    credentials,
)
from constants import FirebaseConstants

from json import dumps as to_json


class CarKeys:
    CAR_ID = 'id'
    CAR_MODEL = 'model'
    CAR_OWNER = 'owner'
    EMERGENCY = 'emergency'


class AccidentKeys:
    LATITUDE = 'lat'
    LONGITUDE = 'lng'
    VIDEO = 'video'
    TIMESTAMP = 'timestamp'


class Accident:

    def __init__(self, lat, lng, timestamp, video_filename) -> None:
        self.lat = lat
        self.lng = lng
        self.timestamp = timestamp
        self.video_filename = video_filename

    def as_dict(self, car):
        return {
            AccidentKeys.LATITUDE: f"{self.lat}",
            AccidentKeys.LONGITUDE: f"{self.lng}",
            AccidentKeys.TIMESTAMP: f"{self.timestamp}",
            AccidentKeys.VIDEO: self.video_filename,
            CarKeys.CAR_ID: car.chassis_id,
            CarKeys.CAR_MODEL: car.model,
            CarKeys.CAR_OWNER: car.owner,
            CarKeys.EMERGENCY: car.emergency_contacts
        }

    def as_json(self, car):
        return to_json(self.as_dict(car), indent=2)


class AccidentReporter:

    def __init__(self) -> None:
        self.setup_done = False
        self.logger = Logger("AccidentReporter")

    def setup(self):
        self.logger.info("Initializing AccidentReporter...")
        cred = credentials.Certificate(FirebaseConstants.CREDENTIALS_FILE_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FirebaseConstants.DATABASE_URL,
            'storageBucket': FirebaseConstants.STORAGE_BUCKET_URL
        })

        self.logger.info("Initializing Storage...")
        self.storage = FirebaseStorage()

        self.logger.info("Initializing FCM...")
        self.fcm = FirebaseCloudMessaging()

        self.logger.success("AccidentReporter is ready.")

    def report_accident(self, accident_payload: dict[str, str]):
        self.logger.info("Preparing to report an accident.")
        # Check payload first
        if accident_payload is None or len(accident_payload) == 0:
            self.logger.error("Accident is either None or Empty. Aborted reporting.")
            return False

        # Obtain video filename and path from payload
        filename = accident_payload.get(AccidentKeys.VIDEO, "")
        filepath = utils.get_capture_file_path(filename)

        # Check filename and path
        if utils.isempty(filename) or not utils.capture_file_exists(filename):
            self.logger.error("Can't find video file associated with this accident.")
            return False

        self.logger.info("Reporting accident...")
        # Upload video to storage
        self.logger.info(f"Preparing to upload file '{filepath}' ...")
        uploaded = self.storage.upload_file(filepath, filename)

        # Send push notification to client app
        sent = self.fcm.send_notification(accident_payload)

        reported = uploaded and sent
        if reported:
            self.logger.success("Accident reported successfully.")
        else:
            self.logger.error("Couldn't report accident.")

        return reported


class FirebaseStorage:

    def __init__(self) -> None:
        self.logger = Logger("Storage")
        self.bucket = storage.bucket()

    def upload_file(self, filepath: str, filename: str):
        """
        Uploads the video in filepath to firebase storage.

        [Note]: This method while executing is sure about given filepath and filename existence
        as it's only called (and should only be called) from 'firebase.report_accident' which does checks on path and filename.

        Args:
            filepath (str): Path to the video file (Relative path).\n
            filename (str): Name of the video file.
        """
        # Upload the file
        try:
            self.logger.info("Uploading video of the accident...")
            remote_path = filename
            blob_file = self.bucket.blob(remote_path)
            blob_file.upload_from_filename(filepath)
            self.logger.success("Video uploaded successfully.")
            return True
        except Exception as e:
            # self.logger.error(e.args[0])
            self.logger.error(f"Can't upload video to remote storage. Reason: {e}")
            return False


class FirebaseCloudMessaging:

    def __init__(self) -> None:
        self.logger = Logger("FCM")
        # FCM runtime
        self.tokens = {}
        self.last_eta = ""

    def refresh_tokens(self):
        try:
            self.logger.info("Refreshing token...")
            ref = db.reference(FirebaseConstants.TOKEN_REFERENCE)

            # Check if token was refreshed at least once
            rcvd_data = ref.get(True)
            tokens_map = dict(rcvd_data[0])
            new_eta = rcvd_data[1]
            # Update token if either eta or token changed
            if self.last_eta != new_eta or len(self.tokens) != len(tokens_map):
                self.tokens = tokens_map
                self.last_eta = new_eta
                self.logger.info(f"Tokens refreshed successfully. {self.tokens}")
            return True
        except Exception as e:
            # self.logger.error(e.args[0])
            self.logger.error(f"Can't refresh tokens.")
            return False

    def send_notification(self, payload):
        # Check if payload is empty
        if utils.isempty(payload):
            self.logger.error("Can't send notification to device. Payload is empty.")
            return False

        # Refresh token
        refreshed = self.refresh_tokens()

        # Check tokens after being refreshed
        if not refreshed or len(self.tokens) == 0:
            return False

        # Send msg to each token
        sent_msgs_count = 0
        for client_uid in self.tokens:
            target_token = self.tokens.get(client_uid, '')
            if utils.isempty(target_token):
                continue
            try:
                self.logger.info(f"Sending signal to client '{client_uid}'")
                # Create the message
                accident_msg = messaging.Message(
                    data=payload,
                    token=target_token
                )
                # Send it
                response: str = messaging.send(accident_msg)
                id_idx = response.find(':') + 1
                self.logger.success(f"Notified client '{client_uid}'.")
                sent_msgs_count += 1
            except Exception as e:
                self.logger.warning(f"Couldn't notify client '{client_uid}'. Reason: '{e.args[0]}'")

        return sent_msgs_count > 0
