"""Magic Mouse HID decoding. MIT; upstream provenance in THIRD_PARTY_NOTICES.md."""
from dataclasses import dataclass
import re

MODELS = {0x030D: (0x29, 6, 3), 0x0269: (0x12, 14, 1), 0x0323: (0x12, 14, 1)}
VENDORS = (0x05AC, 0x004C)


def device_id(uevent):
    match = re.search(r'^HID_ID=([\da-fA-F]+):([\da-fA-F]+):([\da-fA-F]+)$', uevent, re.M)
    if not match:
        return None
    bus, vendor, product = (int(x, 16) for x in match.groups())
    return (vendor, product) if bus in (3, 5) and vendor in VENDORS and product in MODELS else None


def signed12(value):
    return value - 4096 if value & 2048 else value


def delta(new, old):
    return (new - old + 2048) % 4096 - 2048


@dataclass(frozen=True)
class Contact:
    id: int
    x: int
    y: int


@dataclass(frozen=True)
class Frame:
    # None means a short pointer-only report, not fingers lifting.
    contacts: tuple | None
    clicked: bool = False


def decode(data, product):
    """Return all ordered frames; reject malformed packets atomically.

    Unknown/non-touch reports raise ValueError: callers cancel recognition,
    never reinterpret a corrupt report as a finger lift. No feature reports
    or kernel settings are written by this package.
    """
    if product not in MODELS or not data:
        raise ValueError('Unsupported model or empty report')
    packets = [data]
    if data[0] == 0xF7:
        if len(data) < 2 or not 0 < data[1] < len(data) - 2:
            raise ValueError('Truncated double report')
        packets = [data[2:2 + data[1]], data[2 + data[1]:]]
    result = []
    report, header, button = MODELS[product]
    for packet in packets:
        if not packet or packet[0] != report:
            raise ValueError('Unexpected or nested report')
        if report == 0x12 and len(packet) == 8:
            result.append(Frame(None, bool(packet[button] & 3)))
            continue
        if len(packet) < header or (len(packet) - header) % 8 or len(packet) > header + 15 * 8:
            raise ValueError('Invalid touch report length')
        contacts, ids = [], set()
        for offset in range(header, len(packet), 8):
            t = packet[offset:offset + 8]
            ident = ((t[6] << 2) | (t[5] >> 6)) & 15
            if ident in ids:
                raise ValueError('Duplicate contact ID')
            ids.add(ident)
            if t[7] & 0xF0:
                contacts.append(Contact(ident, signed12(t[0] | ((t[1] & 15) << 8)),
                                        -signed12((t[2] << 4) | (t[1] >> 4))))
        result.append(Frame(tuple(contacts), bool(packet[button] & 3)))
    return result
