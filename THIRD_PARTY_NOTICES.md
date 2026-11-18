# Upstream attribution

This is a new, smaller integration library built **using these three MIT projects
as its starting points**, not an entirely original invention or an official Apple driver.
All upstream license notices are shipped in `licenses/`.

| Project / pinned review revision | What informed this implementation |
| --- | --- |
| [Breno Perucchi — magic-mouse-gestures](https://github.com/brenoperucchi/magic-mouse-gestures/tree/c2b33ae5f82747cc473faf972c14b509704dd220) | Python HID discovery, Apple vendor/product table, contact bit layout and wrap-aware displacement. `protocol.py` adapts these ideas and parsing expressions. Credits also to sodonnel and JaapStruyk for upstream model/backend work. |
| [František Salač — magic-mouse-wayland-gestures](https://github.com/Salacfrantisek/magic-mouse-wayland-gestures/tree/23a4b366abb41510f32bd1e29268b68054e2751d) | Exclusive pinch/swipe arbitration: a contact sequence cannot change modes after recognition. Our recognizer implements a smaller backend-independent form. This project itself derives from Perucchi's work. |
| [Enrique Magallon — MouseTouch](https://github.com/Devace-93/mousetouch/tree/df948e43c493c7d9fc2ada3685a6d7a8e0521aef) | Direct HID rather than unreliable evdev slot fallback, physical-click guard, separate tap sequences, handling staggered finger lifts, and separation of recognition from desktop actions. `protocol.py` also adapts signed coordinate decoding from `src/hidraw.rs`. |

Our additional work: strict model-scoped packet validation, decoding **both**
compound reports, bounded nesting, no input grabbing or scroll replacement,
passive diagnostic CLI, deterministic portable tests and FamiliarMac's
credential-checked, active-seat/heartbeat-controlled integration.

Linux `drivers/hid/hid-magicmouse.c` was consulted as the protocol reference
(report lengths, click-byte offsets and short mouse-only reports). No kernel
source is included or copied into this MIT library.

Apple and Magic Mouse are trademarks of Apple Inc. No affiliation or endorsement.
