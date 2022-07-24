from volume import VolumeProvider
import serial
import time
from serial.tools.list_ports import comports


class Communicator:
    """
    Communicator class
    """

    def __init__(self, config):
        """
        :param config: configuration
        :type config: dict
        """
        self.enabled = False
        self.mode = 'stdin' if config['debug'] else 'serial'
        self.provider = VolumeProvider(config)
        self.serial = None
        self.port = config['port']

    @staticmethod
    def get_ports():
        """
        Get all available serial ports
        """
        return [port.device for port in comports()]

    def start_communication(self):
        """
        Start serial communication with device
        """
        self.enabled = True
        while self.enabled:
            try:
                if self.mode == 'serial' and self.serial is None:
                    port = self.port
                    if port is None:
                        ports = self.get_ports()
                        if len(ports) > 0:
                            port = ports[0]

                        self.port = port
                    self.serial = serial.Serial(self.port, baudrate=115200, timeout=5)

                    self._send_applications()
                    while self.enabled:
                        if self._receive_volume():
                            self._send_applications()
            except serial.SerialException:
                print("Error: No device found. Trying again after 10s...")
                self.serial = None
                time.sleep(10)

    def stop_communication(self):
        """
        Stop serial communication with device
        """
        self.enabled = False

    def _get_volumes(self, cache=True):
        """
        Get all volumes to send
        :param cache: use cached list of applications if available
        :type cache: bool
        :return: volumes
        :rtype: [Volume]
        """
        return self.provider.get_display(cache)

    def _send_applications(self):
        """
        Send active sound applications and their volumes in format "<program name>,<program volume (0-100)>,<program name>,<program volume (0-100)>,..."
        """
        data = [f"{volume.get_display_name()},{volume.get_volume()}"
                for volume in self._get_volumes(False)]
        data = ','.join(data) + '\n'
        if self.mode == 'serial':
            self.serial.write(data.encode())
        else:
            print(data, end='')

    def _receive_volume(self):
        """
        Receive volume change in the format "<program index (0+)>,<program volume (0-100)>"
        :return: True if timeout was reached, False otherwise
        :rtype: bool
        """
        try:
            if self.mode == 'serial':
                volume = self.serial.readline().decode()
            else:
                volume = input()
            if volume == '':
                # Probably timed out
                return True
            program = int(volume.split(',')[0])
            program_volume = int(volume.split(',')[1])
            self._get_volumes()[program].set_volume(program_volume)
        except (UnicodeDecodeError, IndexError, ValueError):
            pass
        return False
