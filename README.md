# FamiliarMac Magic Mouse

A small **MIT-licensed Linux Magic Mouse library**, derived from and inspired by
[MouseTouch](https://github.com/Devace-93/mousetouch),
[magic-mouse-wayland-gestures](https://github.com/Salacfrantisek/magic-mouse-wayland-gestures)
and [magic-mouse-gestures](https://github.com/brenoperucchi/magic-mouse-gestures).
See [upstream attribution](THIRD_PARTY_NOTICES.md) and the shipped original licenses.

It decodes Magic Mouse 1, Lightning and USB-C HID reports into contacts, then
recognizes two-finger double taps, swipes and pinches. It **reads only**: no evdev
grab, synthetic middle click, scroll replacement, driver reload or keyboard remap.
Desktop adapters decide what a recognized gesture should do.

**Status: experimental 0.1.0.** Parser and recognizer regression tests pass;
model-by-model hardware validation remains explicit in
[compatibility](docs/COMPATIBILITY.md). This is not a drop-in full macOS gesture stack.

## Use

```sh
python3 -m pip install .
magic-mouse-support probe
magic-mouse-support monitor
python3 -m unittest discover -s tests -v
```

The monitor prints device discovery and recognized events, never keyboard input.
It requires existing read permission for the Magic Mouse hidraw node. A permission
error is reported rather than silently saying there is no mouse. Do not run a GUI
as root or grant access to every input device to work around it.

```python
from magic_mouse_support import decode, Recognizer

recognizer = Recognizer()  # one per physical device
for frame in decode(hid_report_bytes, product=0x030D):
    for event in recognizer.feed(frame, monotonic_seconds):
        if event.kind == 'double-tap':
            show_overview()
```

Reset the recognizer after dropped/malformed input. `devices.Reader` does this
and supports passive nonblocking reads; `python3 -m magic_mouse_support` exposes
the same CLI without installation.

## FamiliarMac integration

[FamiliarMac](https://github.com/kilinccagatay/familiarmac) vendors a pinned,
licensed snapshot so clean installations and release upgrades work offline.
Its existing mouse service reads only supported Magic Mouse hidraw nodes, only
while the active unlocked session opts in and maintains a heartbeat. The
**Mission Control → Magic Mouse → Double-tap with two fingers** switch controls
this independently from the Logitech middle-button shortcut.

No `wtype`/`ydotool` fallback, no per-user shell commands executed as root, no
new keyboard interception. Swipe/pinch recognition is available to future
adapters; this FamiliarMac integration currently enables double-tap only.

## Why another project?

The [issue review](docs/UPSTREAM-REVIEW.md) explains concrete upstream reports and
our response, distinguishing existing upstream fixes from our changes and
unverified hardware behavior. The goal is a reusable, testable recognition core
with a narrow integration boundary, not to hide its origins or claim all upstream
bugs have disappeared.
