# Compatibility and limits

Python 3.10+; core has no third-party runtime dependencies.

| Hardware | Product | Parser | Real gesture validation |
| --- | --- | --- | --- |
| Magic Mouse (original) | 030d | Tested synthetically | Pending; device discovered on development host |
| Magic Mouse 2 (Lightning) | 0269 | Tested synthetically | Not tested |
| Magic Mouse (USB-C) | 0323 | Tested synthetically | Not tested |

Apple vendor IDs 05ac / 004c, USB or Bluetooth HID identities. The Linux kernel
must already supply working Magic Mouse touch reports. This library neither
installs DKMS nor enables the device by sending HID feature reports. A device
may be readable while not reporting touches: use `monitor` to distinguish that
from successful recognition. Connecting by a charging cable is not a promise
that gestures work over that transport.

The current recognizer emits two-finger double taps, swipe begin/update/end and
pinch begin/update/end. Pinch/swipe are **events only**. FamiliarMac 0.1 integration
maps only two-finger double-tap to Mission Control, default off until enabled in
its preferences. Pointer/scroll/click events continue through the kernel.
Passive reading means we cannot suppress native scrolling during a swipe; do not
map swipe effects until an adapter has explicitly resolved that interaction.

Each Reader owns its own recognizer. Disconnect/close, malformed packets,
backwards time and long report gaps reset recognition. Short 8-byte pointer
reports preserve contact state but cancel tapping when a button is pressed.
Thresholds are raw sensor units, configurable via the Thresholds dataclass;
no claim of macOS-identical gesture thresholds is made without physical tests.

FamiliarMac runs the reader inside its existing active-seat guarded root service,
not a root GUI. No world-readable input-node permission rule is required. The
library's standalone CLI uses the invoking user's existing hidraw permissions.
