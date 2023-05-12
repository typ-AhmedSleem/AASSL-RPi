from data import CarKeys
from logger import Logger
from json import dumps as to_json


class CarInfo:
    def __init__(self, id: str = '', model: str = '', owner: str = '', emergency: str = '') -> None:
        self.mapped = {
            CarKeys.CAR_ID: id,
            CarKeys.CAR_MODEL: model,
            CarKeys.CAR_OWNER: owner,
            CarKeys.EMERGENCY: emergency
        }

    def __repr__(self) -> str:
        return str(to_json(self.mapped, indent=2))


class Car:

    def __init__(self, info: CarInfo = CarInfo()) -> None:
        self.info = info
        self.logger = Logger("Car")

    def setup(self):
        self.logger.info("Intializing car...")

        if len(self.chassis_id) == 0:
            self.logger.warning("No chassis id was set. Asking user to add it...")
            self.info.mapped[CarKeys.CAR_ID] = input('Enter chassis id: ')

        if len(self.model) == 0:
            self.logger.warning("No model was set. Asking user to add it...")
            self.info.mapped[CarKeys.CAR_MODEL] = input('Enter car model: ')

        if len(self.owner) == 0:
            self.logger.warning("No owner for this car. Asking user to add it...")
            self.info.mapped[CarKeys.CAR_OWNER] = input('Enter car owner: ')

        if len(self.emergency_contacts) == 0:
            self.logger.warning("No chassis id was set. Asking user to add it...")
            pri_emerg = input('Enter primary emergency contact: ')
            sec_emerg = input('Enter secondary emergency contact: ')
            self.info.mapped[CarKeys.EMERGENCY] = f"{pri_emerg},{sec_emerg}"

        self.logger.info(f"CarInfo was set: {self.info}")
        self.logger.success("Car is ready.")

    @property
    def missing_info(self):
        return len(self.chassis_id) == 0 or len(self.model) == 0 or len(self.owner) == 0 or len(self.emergency_contacts) == 0

    @property
    def chassis_id(self):
        return self.info.mapped.get(CarKeys.CAR_ID, '')

    @property
    def model(self):
        return self.info.mapped.get(CarKeys.CAR_MODEL, '')

    @property
    def owner(self):
        return self.info.mapped.get(CarKeys.CAR_OWNER, '')

    @property
    def emergency_contacts(self):
        return self.info.mapped.get(CarKeys.EMERGENCY, '')
