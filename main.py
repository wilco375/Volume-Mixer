from communication import Communicator
from volume import VolumeProvider
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Volume mixer')
    subparsers = parser.add_subparsers(dest='command')

    list_volumes_parser = subparsers.add_parser('list-volumes', help='List all found programs and their volumes')
    list_volumes_parser.add_argument('--display', choices=['all', 'apps', 'master'], default='all',
                        help="Volumes to display on the device. Either both master and applications or just applications or just master. Default: 'all'")

    start_parser = subparsers.add_parser('start', help='Start communication with device')
    start_parser.add_argument('list-volumes', action='store_true', help='Use stdin/stdout instead of serial')
    start_parser.add_argument('start', action='store_true', help='Use stdin/stdout instead of serial')
    start_parser.add_argument('--port', type=str, help='Serial port to use')
    start_parser.add_argument('--display', choices=['all', 'apps', 'master'], default='all',
                        help="Volumes to display on the device. Either both master and applications or just applications or just master. Default: 'all'")
    start_parser.add_argument('--debug', action='store_true', help='Use stdin/stdout instead of serial')

    args = parser.parse_args()

    if args.command == 'list-volumes':
        provider = VolumeProvider()
        if args.display == 'apps':
            volumes = provider.get_applications()
        elif args.display == 'master':
            volumes = [provider.get_master()]
        else:
            volumes = provider.get_all()
        for volume in volumes:
            print(f"Name: {volume.get_name()}")
            print(f"Display name: {volume.get_short_name()}")
            print(f"Binary: {volume.get_binary()}")
            print(f"Volume: {volume.get_volume()}")
            print(f"Type: {volume.get_type()}\n")

    elif args.command == 'start':
        comm = Communicator({
            'serial_port': args.port,
            'debug': args.debug,
            'display': args.display
        })
        comm.start_communication()
