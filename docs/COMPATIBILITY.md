# Compatibility and limits

Python 3.10+; core has no third-party runtime dependencies.

| Hardware | Product | Parser | Real gesture validation |
| --- | --- | --- | --- |
| Magic Mouse (original) | 030d | Tested synthetically | Two-finger double-tap detected on hardware; GNOME action delivery confirmed |
| Magic Mouse 2 (Lightning) | 0269 | Tested synthetically | Not tested |
| Magic Mouse (USB-C) | 0323 | Tested synthetically | Not tested |

Apple vendor IDs 05ac / 004c, USB or Bluetooth HID identities. The Linux kernel
must already supply working Magic Mouse touch reports. This library neither
installs DKMS nor enables the device by sending HID feature reports. A device
may be readable while not reporting touches: use `monitor` to distinguish that
from successful recognition. Connecting by a charging cable is not a promise
that gestures work over that transport.

The current recognizer emits one- and two-finger double taps, horizontal one-finger swipes, two-finger swipe begin/update/end and
pinch begin/update/end. Pinch/swipe are **events only**. The library itself never injects desktop actions or grabs pointer devices.
FamiliarMac 1.2.0's adapter maps optional one-finger page swipes,
two-finger workspace swipes and one-finger double-tap document zoom, alongside
Mission Control. The adapter forwards only the exact Magic Mouse relative-pointer
endpoint to arbitrate native wheel scrolling; the library remains passive.

Each Reader owns its own recognizer. Disconnect/close, malformed packets,
backwards time and long report gaps reset recognition. Original-model 6-byte 0x10 and second-generation 8-byte pointer
reports preserve contact state but cancel tapping when a button is pressed.
Thresholds are raw sensor units, configurable via the Thresholds dataclass;
no claim of macOS-identical gesture thresholds is made without physical tests.

FamiliarMac runs the reader inside its existing active-seat guarded root service,
not a root GUI. No world-readable input-node permission rule is required. The
library's standalone CLI uses the invoking user's existing hidraw permissions.

## Development hardware check (2026-11-18)

The original Magic Mouse produced five double-tap recognitions in a passive test (1,259 decoded reports; 203 rejected reports). The rejected-report reasons still require investigation. A subsequent FamiliarMac session received the gesture and opened the overview. That session exposed a separate FamiliarMac overview-layout failure and a Nouveau GPU timeout; this is not an end-to-end stability certification. Later navigation and zoom checks are recorded below; pinch still requires hardware validation.


The original mouse also sends standard 0x10 pointer reports between touch
reports. A 2026-11-18 local capture observed 1,011 such reports, alongside valid
0x29 touch reports. Its device HID descriptor declares two button bits and two
16-bit relative axes (six bytes including report ID). These are now decoded as
pointer-only frames, preserving touch state while cancelling taps on clicks.
A subsequent live sample decoded 3,425 frames with zero rejects; the user
confirmed page swipes and one-finger double-tap zoom. This does not validate
unseen Lightning/USB-C firmware or claim macOS content-aware zoom parity.

Physical two-finger workspace switching and finger-following progress were also confirmed on the original model. FamiliarMac handles smoothing, cancellation and Mission Control presentation; these are adapter behavior, not synthetic input emitted by this library.
