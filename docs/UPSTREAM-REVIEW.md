# Upstream issue review — 2026-11-18

Reviewed the three pinned revisions in THIRD_PARTY_NOTICES.md, their open issues,
relevant closed fixes and issue comments. “Addressed” below means covered by our
architecture/tests; it does not claim we fixed the upstream repositories or
completed hardware validation on every model.

| Upstream evidence | Treatment here | Validation / remaining limitation |
| --- | --- | --- |
| [MouseTouch #20](https://github.com/Devace-93/mousetouch/issues/20): renamed mouse, permissions/config confusion on Zorin | Exact HID vendor/product match, no name substring or root HOME config. CLI reports permission errors. | Renamed device test; host discovery found original Magic Mouse. Upstream maintainer already reports fixes since 0.1.5; do not claim this is our discovery. |
| [MouseTouch #21](https://github.com/Devace-93/mousetouch/issues/21), [#35](https://github.com/Devace-93/mousetouch/issues/35): scroll momentum/feel | Passive hidraw reader; never grabs or replaces native scrolling. | No new momentum implementation. Preserves whatever scrolling the native driver provides, including its limitations. |
| [MouseTouch #73](https://github.com/Devace-93/mousetouch/issues/73): accidental middle-click paste | No synthesized middle click; physical click invalidates pending taps. | Click-guard tests. Existing kernel middle-click emulation is **not changed** and may still produce native middle clicks. |
| [Wayland Gestures #3](https://github.com/Salacfrantisek/magic-mouse-wayland-gestures/issues/3): USB-C install requires BTN_MIDDLE | Explicit USB-C ID; touch recognition has no BTN_MIDDLE prerequisite or driver reprobe. | Synthetic USB-C report tests only, no USB-C hardware claim. Comments show experimental branch still fails middle-button preflight. |
| [Wayland Gestures #2](https://github.com/Salacfrantisek/magic-mouse-wayland-gestures/issues/2): missing ydotool socket | Library emits typed events, not subprocess commands. FamiliarMac consumes them through its existing private accelerator. | No ydotool daemon/socket/version dependency. KDE integration is not supplied. |
| [Perucchi #1](https://github.com/brenoperucchi/magic-mouse-gestures/issues/1), [PR #3](https://github.com/brenoperucchi/magic-mouse-gestures/pull/3), [#6](https://github.com/brenoperucchi/magic-mouse-gestures/pull/6), [#7](https://github.com/brenoperucchi/magic-mouse-gestures/pull/7), [#12](https://github.com/brenoperucchi/magic-mouse-gestures/pull/12): GNOME virtual-keyboard and ydotool syntax/socket failures | Same typed-event boundary. | Does not type fallback shortcut strings into applications. |
| [Perucchi PR #11](https://github.com/brenoperucchi/magic-mouse-gestures/pull/11): first-generation/USB-C IDs | Keep all three model IDs and both Apple vendor IDs with attribution. | All parser variants tested. |
| MouseTouch `src/hidraw.rs` handles only first 0xf7 report | Decode both in order, validate whole compound packet before returning events, disallow nested wrappers. | Compound/lift and malformed input regression tests. |

Gesture recognition is independent of the compositor. Continuous native pinch
and workspace swipe injection require a separate adapter; this release does not
pretend that merely recognizing those gestures implements their desktop effects.
