import serial
from time import sleep
from logger import Logger
from threading import Thread, Event
from constants import GPS_UART_PORT, GPS_UART_BAUDRATE


class GPS:

    def __init__(self) -> None:
        self.DEFAULT_LOC = (30.0346762, 31.4295489)
        self.switcher = Event()
        self.serial = None
        self.logger = Logger("GPS")
        self.last_known_location = self.DEFAULT_LOC

    def setup(self):
        self.open_serial_port()
        self.logger.success("GPS is ready.")

    def open_serial_port(self):
        try:
            self.serial = serial.Serial(port=GPS_UART_PORT, baudrate=GPS_UART_BAUDRATE, timeout=1)
            self.logger.success("Opened GPS serial port")
        except Exception as e:
            self.logger.error("Can't open GPS serial port. Reason: {}".format(e))

    def start(self):
        if not self.switcher.is_set():
            self.switcher.clear()
            Thread(name="GPS", target=self.__gps_worker_job).start()

    def stop(self):
        if self.switcher.is_set():
            self.switcher.clear()

    @property
    def serial_open(self):
        """ Checks whether the serial is open and active or not

        Returns:
            bool: True only if serial is created and open, False otherwise.
        """
        return (self.serial is not None) and not self.serial.closed

    def __gps_worker_job(self):
        self.logger.info("GPS service started.")
        while True:
            # Open serial port if not opened
            if not self.serial_open:
                self.open_serial_port()
                #sleep(1)
            # Get location updates
            try:
                line = self.serial.readline().decode().strip()
                if line.startswith('$GPGGA'):
                    # Split line into NMEA parts
                    nema = line.split(',')
                    # Obtain lat & lng from NMEA
                    lat = float(nema[2][:2]) + float(nema[2][2:]) / 60
                    lng = float(nema[4][:3]) + float(nema[4][3:]) / 60
                    # Update last known location
                    self.last_known_location[0] = lat
                    self.last_known_location[1] = lng
                    # Log
                    self.logger.info(f"New location update: Lat= {self.last_known_location[0]} | Lng= {self.last_known_location[1]}")
                    # Wait a sec to warmup
                    sleep(1)
            except Exception as e:
                #self.logger.warning(e)
                sleep(2)
        self.logger.info("GPS service stopped.")

if __name__ =='__main__':
    gps = GPS()
    gps.setup()
    gps.start()