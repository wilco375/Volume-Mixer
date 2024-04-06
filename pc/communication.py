from volume import VolumeProvider
from utilization import UtilizationProvider
import serial
import time
import subprocess
import re
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
        self.volume_provider = VolumeProvider(config)
        self.utilization_provider = UtilizationProvider(config)
        self.serial = None
        self.port = self.get_com_port(config['device_name'])

    @staticmethod
    def get_com_port(device_name):
        """
        Get COM port of Bluetooth device in config
        """
        device_name = re.sub(r'[^a-zA-Z0-9\s]', '', device_name)
        device_ids = subprocess.check_output(['powershell.exe', f'Get-WmiObject -query "select HardwareID from Win32_PnPEntity where Caption = \'{device_name}\' and PNPClass = \'Bluetooth\'" | Select-Object -ExpandProperty HardwareID']).decode('utf-8').split('\r\n')
        device_ids = [device_id for device_id in device_ids if device_id != '']
        com_devices = comports()

        for device_id in device_ids:
            device_id = device_id.split('Dev_')[1]
            
            for com_device in com_devices:
                com_hwid = com_device.hwid.split('_')
                if (len(com_hwid) < 2):
                    continue
                if com_hwid[-2].endswith(device_id):
                    return com_device.device

    def start_communication(self):
        """
        Start serial communication with device
        """
        self.enabled = True
        while self.enabled:
            try:
                if self.mode == 'serial' and self.serial is None:
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
        return self.volume_provider.get_display(cache)
    
    def _get_utilization(self):
        """
        Get utilization to send
        :return: utilization
        :rtype: [Utilization]
        """
        return self.utilization_provider.get_utilization()

    def _send_applications(self):
        """
        Send active sound applications and their volumes in format "<program name>,<program volume (0-100)>,<program name>,<program volume (0-100)>,..."
        """
        data = [
            str(self._get_utilization().get_cpu_usage()) + '%',
            str(self._get_utilization().get_gpu_usage()) + '%',
            str(self._get_utilization().get_ram_usage()) + '/' + str(self._get_utilization().get_ram_total()),
        ]
        data = data.extend([f"{volume.get_display_name()},{volume.get_volume()}"
                for volume in self._get_volumes(False)])
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
