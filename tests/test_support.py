import math
import random
import unittest
from magic_mouse_support import Contact, Frame, Recognizer, Thresholds, decode, device_id
from magic_mouse_support.protocol import MODELS, delta


def packet(product=0x030D, contacts=(), click=False):
    report, header, button = MODELS[product]
    data = bytearray(header);data[0] = report;data[button] = int(click)
    for ident, x, y, down in contacts:
        x, y = x & 4095, -y & 4095
        data.extend((x & 255, (x >> 8) | ((y & 15) << 4), y >> 4, 100, 90,
                     ((ident & 3) << 6) | 32, ident >> 2, 0x40 if down else 0))
    return bytes(data)


def frame(x=0, y=0):
    return Frame((Contact(1, x-300, y), Contact(2, x+300, y)))


def tap(r, start):
    r.feed(frame(), start)
    return r.feed(Frame(()), start+.12)


class ProtocolTests(unittest.TestCase):
    def test_all_models_and_vendors_ignore_alias(self):
        for vendor in (0x004C, 0x05AC):
            for product in MODELS:
                self.assertEqual(device_id(f'HID_ID=0005:{vendor:08X}:{product:08X}\nHID_NAME=Renamed 🐭'), (vendor, product))
                f = decode(packet(product, [(3, -1800, 900, True), (7, 1500, -1300, False)], True), product)[0]
                self.assertEqual(f, Frame((Contact(3, -1800, 900),), True))
        self.assertIsNone(device_id('HID_ID=0003:000005AC:00000262')) # internal keyboard
        self.assertIsNone(device_id('HID_ID=0005:0000046D:0000030D')) # not Apple

    def test_both_compound_frames_and_no_recursion(self):
        a,b = packet(contacts=[(1,0,0,True)]),packet()
        self.assertEqual(len(decode(bytes([0xF7,len(a)])+a+b,0x030D)),2)
        for data in (b'', b'\xf7', b'\xf7\xff'+a, b'\xf7\x02\xf7\x00'+b, a+b'\0', b'\x29',packet(contacts=[(1,0,0,True),(1,1,1,True)])):
            with self.assertRaises(ValueError):decode(data,0x030D)

    def test_short_pointer_frame_does_not_end_touch(self):
        self.assertEqual(decode(b'\x12\x01'+bytes(6),0x0269),[Frame(None,True)])

    def test_fuzz_and_wrap(self):
        rng=random.Random(7)
        for _ in range(2000):
            data=rng.randbytes(rng.randrange(256))
            try:decode(data,0x030D)
            except ValueError:pass
        self.assertEqual(delta(-2040,2040),16)


class GestureTests(unittest.TestCase):
    def test_double_tap_once(self):
        r=Recognizer()
        self.assertEqual(tap(r,0),[])
        events=tap(r,.25)
        self.assertEqual([(e.kind,e.fingers) for e in events],[('double-tap',2)])
        self.assertEqual(tap(r,.5),[])

    def test_staggered_lifts_do_not_move_centroid(self):
        r=Recognizer()
        for start in (0,.3):
            r.feed(frame(),start)
            r.feed(Frame((Contact(2,300,0),)),start+.1)
            events=r.feed(Frame(()),start+.14)
        self.assertEqual(events[0].kind,'double-tap')

    def test_click_not_tap_including_short_report(self):
        r=Recognizer();tap(r,0)
        r.feed(frame(),.25);r.feed(Frame(None,True),.28)
        self.assertEqual(r.feed(Frame(()),.35),[])
        self.assertEqual(tap(r,.4),[])

    def test_scroll_hold_replaced_finger_and_three_fingers_rejected(self):
        for bad in (frame(250), Frame((Contact(8,-300,0),Contact(9,300,0))),
                    Frame((Contact(1,-300,0),Contact(2,300,0),Contact(3,0,0)))):
            r=Recognizer();tap(r,0);r.feed(frame(),.25);r.feed(bad,.3)
            self.assertEqual(r.feed(Frame(()),.4),[])
        r=Recognizer();tap(r,0);r.feed(frame(),.2)
        self.assertEqual(r.feed(Frame(()),.7),[])

    def test_gap_reconnect_clock_reset(self):
        r=Recognizer();tap(r,0)
        self.assertEqual(tap(r,2),[])
        r.reset();self.assertEqual(tap(r,2.3),[])
        self.assertEqual(tap(r,1),[])
        self.assertEqual(r.feed(frame(),math.nan),[])

    def test_independent_devices(self):
        a,b=Recognizer(),Recognizer()
        self.assertEqual(tap(a,0),[]);self.assertEqual(tap(b,.2),[])

    def test_pinch_swipe_arbitration(self):
        r=Recognizer();r.feed(frame(),0)
        e=r.feed(Frame((Contact(1,-600,0),Contact(2,600,0))),.1)
        self.assertEqual(e[0].kind,'pinch')
        self.assertEqual(r.feed(frame(900),.2)[0].kind,'pinch')
        self.assertEqual(r.feed(Frame(()),.3)[0].phase,'end')
        self.assertEqual(tap(r,.4),[])
        r=Recognizer();r.feed(frame(),0)
        self.assertEqual(r.feed(frame(400),.1)[0].kind,'swipe')
        self.assertEqual(r.feed(Frame((Contact(1,-700,0),Contact(2,700,0))),.2)[0].kind,'swipe')

    def test_settings_validation(self):
        for value in (0,-1,math.nan,math.inf):
            with self.assertRaises(ValueError):Thresholds(tap_seconds=value)


if __name__ == '__main__':unittest.main()
