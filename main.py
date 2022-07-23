from communication import Communicator
from volume import VolumeProvider
import argparse
import yaml

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Volume mixer')
    parser.add_argument('--config', '-c', type=argparse.FileType('r', encoding='utf-8'), default='./config.yaml',
                        help='configuration file')
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('list-applications', help='List all found programs and their volumes.')

    subparsers.add_parser('list-devices', help='List all found devices.')

    start_parser = subparsers.add_parser('start', help='Start communication with the device.')
    start_parser.add_argument('--port', type=str, help='Serial port to use.')
    start_parser.add_argument('--baudrate', type=int, default=115200, help='Baud rate to use. Default: 115200')
    start_parser.add_argument('--debug', action='store_true', help='Use stdin/stdout instead of serial.')

    args = parser.parse_args()

    config = dict(yaml.safe_load(args.config))
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

    elif args.command == 'list-devices':
        print("=== Found ports ===")
        for port in Communicator.get_ports():
            print(port)

    elif args.command == 'start':
        config['port'] = args.port
        config['baudrate'] = args.baudrate
        config['debug'] = args.debug

        comm = Communicator(config)
        comm.start_communication()
