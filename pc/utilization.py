import os
import psutil
import sys
from abc import ABC, abstractmethod


class Utilization(ABC):
    _ram_total = None

    def __init__(self, config):
        """
        :param config: configuration
        :type config: dict
        """
        self.config = config

    @abstractmethod
    def get_cpu_usage(self):
        """
        Get the current CPU utilization
        :return: utilization (0-100)
        :rtype: int
        """
        return psutil.cpu_percent()

    @abstractmethod
    def get_gpu_usage(self):
        """
        Get the current GPU utilization
        :return: utilization (0-100)
        :rtype: int
        """
        return NotImplementedError

    @abstractmethod
    def get_ram_usage(self):
        """
        Get the amount of RAM currently in use
        :return: amount of RAM in use in GB
        :rtype: float
        """
        return round(psutil.virtual_memory().used / 1073741824, 1)

    @abstractmethod
    def get_ram_total(self):
        """
        Get the total amount of RAM available
        :return: amount of RAM in the system in GB
        :rtype: float
        """
        if self._ram_total is None:
            # Cache total amount of memory since it will not change
            self._ram_total = round(psutil.virtual_memory().total / 1073741824, 1)
        return self._ram_total


class UtilizationProvider:
    def __init__(self, config):
        """
        :param config: configuration
        :type config: dict
        """
        self.is_windows = sys.platform == 'win32'
        self.config = config
        self.utilization = None

    def get_utilization(self):
        """
        Get the utilization
        :return: utilization
        :rtype: Utilization
        """
        if self.utilization is not None:
            return self.utilization

        if self.is_windows:
            self.utilization = WindowsUtilization(self.config)
        else:
            raise NotImplementedError
        return self.utilization


class WindowsUtilization(Utilization):
    def get_gpu_usage(self):
        return int(os.popen('powershell -c "(Get-WmiObject -Namespace root\cimv2 -Class Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine | Measure-Object -Sum UtilizationPercentage).Sum"').read().strip())
