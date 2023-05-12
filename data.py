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
            # AccidentKeys.LATITUDE: f"{self.lat}",
            # AccidentKeys.LONGITUDE: f"{self.lng}",
            # AccidentKeys.TIMESTAMP: f"{self.timestamp}",
            # AccidentKeys.TIMESTAMP: self.video_filename,
            CarKeys.CAR_ID: car.chassis_id,
            CarKeys.CAR_MODEL: car.model,
            CarKeys.CAR_OWNER: car.owner,
            CarKeys.EMERGENCY: car.emergency_contacts
        }

    def as_json(self, car):
        return to_json(self.as_dict(car))
