from abc import ABC, abstractmethod
import sys
import yaml

if sys.platform == 'win32':
    from _ctypes import COMError
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume


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
            formatted = self.config['display_names'][self.get_binary()]
        else:
            formatted = self.get_name().replace(',', '')
            if self.config['capitalize_names']:
                formatted = formatted.capitalize()
        return formatted

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
        self.config = config
        self.master = None
        self.applications = None

    def get_applications(self, cache=True, add_blacklisted=False):
        """
        Get all active applications outputting volume
        :param cache: use cached list of applications if available
        :type cache: bool
        :return: application volumes
        :rtype: [Volume]
        """
        if cache and self.applications is not None:
            return self.applications

        # Get all applications while combining multiple instances of the same application
        applications = {}
        if self.is_windows:
            retry = 0
            while retry < 3:
                try:
                    for session in AudioUtilities.GetAllSessions():
                        if session.Process:
                            volume = WindowsApplicationVolume(self.config, session)
                            if volume.get_binary() not in applications:
                                applications[volume.get_binary()] = volume
                            else:
                                applications[volume.get_binary()].add_application(session)
                    break
                except (COMError, OSError):
                    # Sometimes, getting the sessions fails
                    retry += 1
        else:
            raise NotImplementedError
        applications = list(applications.values())

        # Order applications to priority and apply blacklist
        applications_binaries = [application.get_binary() for application in applications]
        ordered_applications = []
        for app in self.config['priority']:
            if app in applications_binaries and (add_blacklisted or app not in self.config['blacklist']):
                ordered_applications.append(applications[applications_binaries.index(app)])
        for application in applications:
            if application not in ordered_applications and (add_blacklisted or application.get_binary() not in self.config['blacklist']):
                ordered_applications.append(application)

        self.applications = ordered_applications

        return ordered_applications

    @abstractmethod
    def get_master(self):
        """
        Get the master volume
        :return: master volume
        :rtype: Volume
        """
        if self.master is not None:
            return self.master

        if self.is_windows:
            self.master = WindowsMasterVolume(self.config)
        else:
            raise NotImplementedError
        return self.master

    def get_all(self, cache=True):
        """
        Get all active volumes
        :param cache: use cached list of applications if available
        :type cache: bool
        :return: all active volumes
        :rtype: [Volume]
        """
        volumes = []
        if self.config['master']:
            volumes.append(self.get_master())
        if self.config['applications']:
            volumes.extend(self.get_applications(cache))
        return volumes

    def get_display(self, cache=True):
        """
        Get all active volumes to display
        :param cache: use cached list of applications if available
        :type cache: bool
        :return: all active volumes
        :rtype: [Volume]
        """
        if not cache:
            with open(self.config['path'], 'r') as f:
                c = dict(yaml.safe_load(f))
            for (k,v) in c.items():
                self.config[k] = v 
        return self.get_all(cache)
    
    def update_config(self):
        # Clear cache
        self.applications = None

        # Write config
        with open(self.config["path"], 'w') as f:
            config_to_write = {
                k: v for k, v in self.config.items() if k not in ["path", "baudrate", "debug"] 
            }
            yaml.dump(config_to_write, f)

class WindowsMasterVolume(Volume):
    def __init__(self, config):
        super().__init__(config)
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.interface = cast(interface, POINTER(IAudioEndpointVolume))
        self.volume = 0

    def get_name(self):
        return "Main"

    def get_binary(self):
        return None

    def get_volume(self):
        try:
            if self.interface.GetMute() == 1:
                self.volume = 0
            else:
                self.volume = round(self.interface.GetMasterVolumeLevelScalar() * 100)
        except (COMError, OSError):
            pass
        return self.volume

    def set_volume(self, volume):
        try:
            self.interface.SetMute(0, None)
            self.interface.SetMasterVolumeLevelScalar(min(1.0, max(0.0, volume / 100)), None)
        except (COMError, OSError):
            return False

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
        self.sessions = [session]
        self.interfaces = [session._ctl.QueryInterface(ISimpleAudioVolume)]
        self.volume = 0
        self.name = None
        self.binary = None

    def get_name(self):
        if self.name is not None:
            return self.name

        try:
            if self.sessions[0].DisplayName and self.sessions[0].DisplayName[0] != '@':
                self.name = self.sessions[0].DisplayName
            else:
                self.name = self.get_binary().split('.')[0]
        except (COMError, OSError):
            pass
        return self.name

    def get_binary(self):
        if self.binary is not None:
            return self.binary

        try:
            self.binary = self.sessions[0].Process.name()
        except (COMError, OSError):
            pass
        return self.binary

    def get_volume(self):
        try:
            if self.interfaces[0].GetMute() == 1:
                self.volume = 0
            else:
                self.volume = round(self.interfaces[0].GetMasterVolume() * 100)
        except (COMError, OSError):
            pass
        return self.volume

    def set_volume(self, volume):
        for interface in self.interfaces:
            try:
                interface.SetMute(0, None)
                interface.SetMasterVolume(min(1.0, max(0.0, volume / 100)), None)
            except (COMError, OSError):
                return False

    def get_type(self):
        return "application"

    def add_application(self, session):
        self.sessions.append(session)
        self.interfaces.append(session._ctl.QueryInterface(ISimpleAudioVolume))
