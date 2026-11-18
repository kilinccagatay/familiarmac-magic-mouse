"""Passive hidraw source. Does not grab evdev or change the kernel driver."""
import os
from pathlib import Path
from .protocol import device_id, decode
from .gestures import Recognizer


def discover(root='/sys/class/hidraw'):
    for entry in sorted(Path(root).glob('hidraw*')):
        try:
            metadata = (entry / 'device/uevent').read_text()
            ident = device_id(metadata)
            if ident:
                yield '/dev/' + entry.name, ident, entry
        except OSError:
            continue


class Reader:
    def __init__(self, path, product):
        self.path, self.product = path, product
        self.recognizer = Recognizer()
        self.fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
        self.frames = self.invalid = 0

    def read(self, now):
        data = os.read(self.fd, 256)
        if not data:
            raise OSError('Magic Mouse disconnected')
        try:
            frames = decode(data, self.product)
        except ValueError:
            self.invalid += 1
            self.recognizer.reset()
            return []
        self.frames += len(frames)
        gestures = []
        for frame in frames:
            gestures.extend(self.recognizer.feed(frame, now))
        return gestures

    def close(self):
        os.close(self.fd)
        self.recognizer.reset()
