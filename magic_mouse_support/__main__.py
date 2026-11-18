"""Read-only diagnostic CLI. Never injects keys or modifies device settings."""
import argparse
import json
import select
import time
from dataclasses import asdict
from .devices import Reader, discover


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['probe', 'monitor'])
    args = parser.parse_args()
    readers = []
    try:
        for path, (vendor, product), _ in discover():
            status = dict(path=path, vendor=f'{vendor:04x}', product=f'{product:04x}')
            try:
                reader = Reader(path, product)
                readers.append(reader)
                status['readable'] = True
            except OSError as error:
                status.update(readable=False, error=str(error))
            print(json.dumps(status), flush=True)
        if not readers:
            print('No readable supported Magic Mouse. Check Bluetooth connection and hidraw permissions.', flush=True)
            return 1
        if args.command == 'monitor':
            while readers:
                ready, _, _ = select.select([r.fd for r in readers], [], [], 1)
                for reader in list(readers):
                    if reader.fd in ready:
                        try:
                            for event in reader.read(time.monotonic()):
                                print(json.dumps(dict(device=reader.path, **asdict(event))), flush=True)
                        except BlockingIOError:
                            pass
                        except OSError:
                            reader.close()
                            readers.remove(reader)
    except KeyboardInterrupt:
        pass
    finally:
        for reader in readers:
            reader.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
