from volume import VolumeProvider
import serial


class Communicator:
    """
    Communicator class
    """
    def __init__(self, config):
        """
        :param config: configuration
        :type config: dict
        """
        self.send = config['display']
        self.mode = 'stdin' if config['debug'] else 'serial'
        self.provider = VolumeProvider()

        if self.mode == 'serial':
            self.serial = serial.Serial(config['serial_port'], timeout=10)

    def start_communication(self):
        """
        Start serial communication with device
        """
        self.enabled = True
        while self.enabled:
            self._send_applications()
            self._receive_volume()

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
        if self.send == 'apps':
            return self.provider.get_applications()
        elif self.send == 'master':
            return [self.provider.get_master()]
        else:
            return self.provider.get_all()

    def _send_applications(self):
        """
        Send active sound applications and their volumes in format "<program name>,<program volume (0-100)>,<program name>,<program volume (0-100)>,..."
        """
        data = [f"{self._format_application_name(volume.get_short_name())},{volume.get_volume()}" for volume in self._get_volumes()]
        data = ','.join(data) + '\n'
        if self.mode == 'serial':
            self.serial.write(data.encode())
        else:
            print(data, end='')

    def _receive_volume(self):
        """
        Receive volume change in the format "<program index (0+)>,<program volume (0-100)>"
        """
        try:
            if self.mode == 'serial':
                volume = self.serial.readline().decode()
            else:
                volume = input()
            program = int(volume.split(',')[0])
            program_volume = int(volume.split(',')[1])
            self._get_volumes()[program].set_volume(program_volume)
        except (UnicodeDecodeError, IndexError):
            print("Something went wrong when receiving volume")

    def _format_application_name(self, name):
        """
        Format application name to show on the display of the device
        """
        return name.replace(',', ' ')
