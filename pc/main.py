from communication import Communicator
from volume import VolumeProvider
import argparse
import yaml
import shutil
from os import path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Volume mixer')
    parser.add_argument('--config', '-c', type=str, help='Configuration file. Default: ./config.yaml')
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('list-applications', help='List all found programs and their volumes.')

    start_parser = subparsers.add_parser('start', help='Start communication with the device.')
    start_parser.add_argument('--baudrate', type=int, default=115200, help='Baud rate to use. Default: 115200')
    start_parser.add_argument('--debug', action='store_true', help='Use stdin/stdout instead of serial.')

    args = parser.parse_args()
    local_config = path.join(path.dirname(__file__), 'config.yaml')
    if args.config is None and not path.exists(local_config):
        shutil.copyfile(path.join(path.dirname(__file__), 'config.example.yaml'), local_config)
    with open(args.config if args.config else local_config, 'r') as f:
        config = dict(yaml.safe_load(f))
    if not config:
        raise Exception('Invalid configuration file.')

    if args.command == 'list-applications':
        print("=== Found applications ===")
        provider = VolumeProvider(config)
        for volume in provider.get_all():
            print(f"Name: {volume.get_name()}")
            print(f"Display name: {volume.get_display_name()}")
            print(f"Binary: {volume.get_binary()}")
            print(f"Volume: {volume.get_volume()}")
            print(f"Type: {volume.get_type()}\n")

    elif args.command == 'start':
        config['baudrate'] = args.baudrate
        config['debug'] = args.debug

        comm = Communicator(config)
        comm.start_communication()

    else:
        parser.print_help()
