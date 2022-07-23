from abc import ABC, abstractmethod
import sys

if sys.platform == 'win32':
    from _ctypes import COMError
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume
elif sys.platform == 'linux':
    import os


class Volume(ABC):
    def __init__(self, config):
        """
        :param config: configuration
        :type config: dict
        """
        self.config = config

    @abstractmethod
    def get_name(self):
        """
        Get the name of the program
        :return: human-readable name of the volume device / application
        :rtype: str
        """
        return NotImplementedError

    def get_display_name(self):
        """
        Get the display name of the program
        """
        if self.get_binary() in self.config['display_names']:
            name = self.config['display_names'][self.get_binary()]
        else:
            name = self.get_name()
        shorted = name[0:4]
        if self.config['capitalize_names']:
            shorted = shorted.capitalize()
        return shorted.replace(',', '')

    @abstractmethod
    def get_binary(self):
        """
        Get the binary name of the program
        :return: binary name of the volume device / application
        :rtype: str|None
        """
        return NotImplementedError

    @abstractmethod
    def get_volume(self):
        """
        Get the volume of the program
        :return: volume of the program (0-100)
        :rtype: int
        """
        return NotImplementedError

    @abstractmethod
    def set_volume(self, volume):
        """
        Set the volume of the program
        :param volume: volume of the program (0-100)
        :type volume: int
        """
        return NotImplementedError

    @abstractmethod
    def get_type(self):
        """
        Get the type of the volume (master or application)
        :return: type of the program
        :rtype: str
        """
        return NotImplementedError

    def __str__(self):
        return f"{self.get_name()} - {self.get_volume()}%"

    def __repr__(self):
        return str(self)


class VolumeProvider:
    def __init__(self, config):
        """
        :param config: configuration
        :type config: dict
        """
        self.is_windows = sys.platform == 'win32'
        self.is_linux = sys.platform == 'linux'
        self.config = config

    def get_applications(self):
        """
        Get all active applications outputting volume
        :return: application volumes
        :rtype: [Volume]
        """
        if self.is_windows:
            applications = [WindowsApplicationVolume(self.config, session)
                            for session in AudioUtilities.GetAllSessions() if session.Process]
        elif self.is_linux:
            sink_inputs = [line for line in os.popen('pactl list sink-inputs').read().split('\n') if "Sink Input" in line]
            applications = [PulseAudioApplicationVolume(self.config, int(input.split('#')[1]))
                            for input in sink_inputs]
        else:
            return NotImplementedError

        applications_binaries = [application.get_binary() for application in applications]
        ordered_applications = []
        for app in self.config['priority']:
            if app in self.config['priority']:
                ordered_applications.append(applications[applications_binaries.index(app)])
        for application in applications:
            if application not in ordered_applications and application.get_binary() not in self.config['blacklist']:
                ordered_applications.append(application)
        return ordered_applications

    @abstractmethod
    def get_master(self):
        """
        Get the master volume
        :return: master volume
        :rtype: Volume
        """
        if self.is_windows:
            return WindowsMasterVolume(self.config)
        elif self.is_linux:
            return PulseAudioMasterVolume(self.config)

    def get_all(self):
        """
        Get all active volumes
        :return: all active volumes
        :rtype: [Volume]
        """
        volumes = []
        if self.config['master']:
            volumes.append(self.get_master())
        if self.config['applications']:
            volumes.extend(self.get_applications())
        return volumes

    def get_display(self):
        """
        Get all active volumes to display
        :return: all active volumes
        :rtype: [Volume]
        """
        return self.get_all()[0:self.config['display_limit']]


class WindowsMasterVolume(Volume):
    def __init__(self, config):
        super().__init__(config)
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.interface = cast(interface, POINTER(IAudioEndpointVolume))

    def get_name(self):
        return "Main"

    def get_binary(self):
        return None

    def get_volume(self):
        if self.interface.GetMute() == 1:
            return 0
        return round(self.interface.GetMasterVolumeLevelScalar() * 100)

    def set_volume(self, volume):
        try:
            self.interface.SetMute(0, None)
            self.interface.SetMasterVolumeLevelScalar(min(1.0, max(0.0, volume / 100)), None)
        except COMError:
            pass

    def get_type(self):
        return "master"


class PulseAudioMasterVolume(Volume):
    def get_name(self):
        return "Main"

    def get_binary(self):
        return None

    def get_volume(self):
        sinks = os.popen("pactl list sinks").read()
        for line in sinks.split("\n"):
            if "Volume:" in line:
                return int(line.split("%")[0].split(" ")[-1])

    def set_volume(self, volume):
        os.system(f"pactl set-sink-volume @DEFAULT_SINK@ {min(100, max(0, volume))}%")

    def get_type(self):
        return "master"


class WindowsApplicationVolume(Volume):
    def __init__(self, config, session):
        """
        :param config: configuration
        :type config: dict
        :param session: program session
        :type session: pycaw.utils.AudioSession
        """
        super().__init__(config)
        self.session = session
        self.interface = session._ctl.QueryInterface(ISimpleAudioVolume)

    def get_name(self):
        if self.session.DisplayName and self.session.DisplayName[0] != '@':
            return self.session.DisplayName
        else:
            return self.get_binary().split('.')[0]

    def get_binary(self):
        return self.session.Process.name()

    def get_volume(self):
        if self.interface.GetMute() == 1:
            return 0
        return round(self.interface.GetMasterVolume() * 100)

    def set_volume(self, volume):
        try:
            self.interface.SetMute(0, None)
            self.interface.SetMasterVolume(min(1.0, max(0.0, volume / 100)), None)
        except COMError:
            pass

    def get_type(self):
        return "application"


class PulseAudioApplicationVolume(Volume):
    def __init__(self, config, input):
        """
        :param config: configuration
        :type config: dict
        :param input: sink input
        :type input: int
        """
        super().__init__(config)
        self.input = input
        self.name = None
        self.binary = None

    def get_name(self):
        if self.name is not None:
            return self.name
        else:
            sinks = os.popen("pactl list sink-inputs").read()
            is_application = False
            for line in sinks.split("\n"):
                if f"Sink Input #{self.input}" in line:
                    is_application = True

                if "application.name = " in line and is_application:
                    self.name = line.split('"')[-2]
                    return self.name
        return None

    def get_binary(self):
        if self.binary is not None:
            return self.binary
        else:
            sinks = os.popen("pactl list sink-inputs").read()
            is_application = False
            for line in sinks.split("\n"):
                if f"Sink Input #{self.input}" in line:
                    is_application = True

                if "application.process.binary = " in line and is_application:
                    self.binary = line.split('"')[-2]
                    return self.binary

    def get_volume(self):
        sinks = os.popen("pactl list sink-inputs").read()
        is_application = False
        for line in sinks.split("\n"):
            if f"Sink Input #{self.input}" in line:
                is_application = True

            if "Volume:" in line and is_application:
                return int(line.split("%")[0].split(" ")[-1])

    def set_volume(self, volume):
        os.system(f"pactl set-sink-input-volume {self.input} {min(100, max(0, volume))}%")

    def get_type(self):
        return "application"
