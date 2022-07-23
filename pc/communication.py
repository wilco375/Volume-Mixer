from volume import VolumeProvider
import serial
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

        if self.mode == 'serial':
            port = config['port'] if config['port'] else self.get_ports()[0]
            self.serial = serial.Serial(port, baudrate=115200, timeout=5)

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
        self._send_applications()
        while self.enabled:
            if self._receive_volume():
                self._send_applications()

    def stop_communication(self):
        """
        Stop serial communication with device
        """
        self.enabled = False

    def _get_volumes(self):
        """
        Get all volumes to send
        :return: volumes
        :rtype: [Volume]
        """
        return self.provider.get_display()

    def _send_applications(self):
        """
        Send active sound applications and their volumes in format "<program name>,<program volume (0-100)>,<program name>,<program volume (0-100)>,..."
        """
        data = [f"{volume.get_display_name()},{volume.get_volume()}"
                for volume in self._get_volumes()]
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
        except (UnicodeDecodeError, IndexError, ValueError, OSError):
            pass
        return False
