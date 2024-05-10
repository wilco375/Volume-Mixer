from communication import Communicator
from volume import VolumeProvider
import argparse
import yaml
import shutil
from os import path
from infi.systray import SysTrayIcon
from os.path import join, dirname
import tkinter as tk
from tkinter.font import Font
import os
from settings import Settings
from multiprocessing import Process

def quit_systray(_):
    settings.quit()
    os._exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Volume mixer')
    parser.add_argument('--config', '-c', type=str, help='Configuration file. Default: ./config.yaml')
    parser.add_argument('--baudrate', type=int, default=115200, help='Baud rate to use. Default: 115200')
    parser.add_argument('--debug', action='store_true', help='Use stdin/stdout instead of serial.')

    args = parser.parse_args()
    local_config = path.join(path.dirname(__file__), 'config.yaml')
    if args.config is None and not path.exists(local_config):
        shutil.copyfile(path.join(path.dirname(__file__), 'config.example.yaml'), local_config)
    config_path = args.config if args.config else local_config
    with open(config_path, 'r') as f:
        config = dict(yaml.safe_load(f))
    if not config:
        raise Exception('Invalid configuration file.')

    config['path'] = config_path
    config['baudrate'] = args.baudrate
    config['debug'] = args.debug

    comm = Communicator(config)
    Process(target=comm.start_communication).start()

    settings = Settings(comm)

    menu_options = (("Open settings", None, settings.show),)
    systray = SysTrayIcon("icon.ico", "Volume Mixer", menu_options, on_quit=quit_systray)
    systray.start()