"""Deterministic, per-device recognizer; no OS commands or input injection.

Design informed by MouseTouch tap/click guards and Salač's gesture arbiter.
Thresholds are conservative raw sensor units; see docs/COMPATIBILITY.md.
"""
from dataclasses import dataclass
import math
from .protocol import delta


@dataclass(frozen=True)
class Gesture:
    kind: str
    fingers: int
    phase: str = 'end'
    dx: float = 0
    dy: float = 0
    scale: float = 1


@dataclass(frozen=True)
class Thresholds:
    tap_seconds: float = .40
    double_seconds: float = .50
    chord_seconds: float = .10
    tap_travel: float = 220
    gesture_travel: float = 300
    horizontal_pair_travel: float = 140
    gap_seconds: float = .75

    def __post_init__(self):
        for value in vars(self).values():
            if not math.isfinite(value) or value <= 0:
                raise ValueError('Thresholds must be finite and positive')


class Recognizer:
    def __init__(self, thresholds=None):
        self.t = thresholds or Thresholds()
        self.reset()

    def reset(self):
        self.session = None
        self.last_tap = None
        self.last_time = None

    def feed(self, frame, now):
        if not math.isfinite(now):
            self.reset()
            return []
        if self.last_time is not None and (now < self.last_time or now - self.last_time > self.t.gap_seconds):
            self.reset()
        self.last_time = now
        if frame.clicked:
            self.last_tap = None
            if self.session:
                self.session['blocked'] = True
        if frame.contacts is None:
            return []
        points = {p.id: (p.x, p.y) for p in frame.contacts}
        if not points:
            s, self.session = self.session, None
            if s is None:
                return []
            if s['mode']:
                return [Gesture(s['mode'], s['count'], 'cancel' if s['blocked'] else 'end', s.get('dx', 0), s.get('dy', 0), s.get('scale', 1))]
            valid = (not s['blocked'] and s['count'] in (1, 2) and now - s['start'] <= self.t.tap_seconds
                     and s['travel'] <= self.t.tap_travel and (s['count'] == 1 or s['chord']))
            if not valid:
                self.last_tap = None
                return []
            # Pair distinct complete contact sequences. A triple tap fires once.
            if self.last_tap is not None and self.last_tap[1] == s['count'] and 0 <= now - self.last_tap[0] <= self.t.double_seconds:
                self.last_tap = None
                return [Gesture('double-tap', s['count'])]
            self.last_tap = (now, s['count'])
            return []
        if self.session is None:
            self.session = dict(start=now, origins={}, count=0, travel=0, blocked=frame.clicked,
                                chord=False, mode=None, distance=None, pair=None)
        s = self.session
        if s['mode'] and len(points) > s['count']:
            s['blocked'] = True
        s['count'] = max(s['count'], len(points))
        if len(points) == 2 and now - s['start'] <= self.t.chord_seconds:
            s['chord'] = True
        if len(points) > 2:
            s['blocked'] = True
        for ident, point in points.items():
            if ident not in s['origins']:
                if now - s['start'] > self.t.chord_seconds:
                    s['blocked'] = True
                s['origins'][ident] = point
            origin = s['origins'][ident]
            s['travel'] = max(s['travel'], math.hypot(delta(point[0], origin[0]), delta(point[1], origin[1])))
        if len(s['origins']) > 2:
            s['blocked'] = True
        if len(points) == 1 and s['count'] == 1 and not s['blocked']:
            ident, point = next(iter(points.items()))
            dx, dy = (delta(point[i], s['origins'][ident][i]) for i in (0, 1))
            s['dx'], s['dy'] = dx, dy
            # Preserve vertical scrolling: one-finger gestures are horizontal only.
            if abs(dx) >= self.t.gesture_travel and abs(dx) > abs(dy) * 1.5:
                old_mode = s['mode']
                s['dx'], s['dy'] = dx, dy
                s['mode'] = 'swipe'
                self.last_tap = None
                return [Gesture('swipe', 1, 'update' if old_mode else 'begin', dx, dy)]
            return []
        if len(points) != 2 or s['blocked']:
            return []
        ids = tuple(sorted(points))
        a, b = (points[i] for i in ids)
        distance = math.hypot(delta(a[0], b[0]), delta(a[1], b[1]))
        if s['pair'] is None:
            s['pair'], s['distance'] = ids, distance
        if s['pair'] != ids:
            s['blocked'] = True
            return []
        dx = sum(delta(p[0], s['origins'][i][0]) for i, p in points.items()) / 2
        dy = sum(delta(p[1], s['origins'][i][1]) for i, p in points.items()) / 2
        travel = math.hypot(dx, dy)
        spread = abs(distance - s['distance'])
        old_mode = s['mode']
        if not old_mode:
            if spread >= self.t.gesture_travel and spread > travel * 1.5:
                s['mode'] = 'pinch'
            elif (abs(dx) >= self.t.horizontal_pair_travel and abs(dx) > abs(dy) * 1.5
                  and travel > spread * 1.5):
                s['mode'] = 'swipe'
            elif travel >= self.t.gesture_travel and travel > spread * 1.5:
                s['mode'] = 'swipe'
        if s['mode']:
            s['dx'], s['dy'], s['scale'] = dx, dy, distance / s['distance'] if s['distance'] else 1
            self.last_tap = None
            return [Gesture(s['mode'], 2, 'update' if old_mode else 'begin', dx, dy,
                            distance / s['distance'] if s['distance'] else 1)]
        return []
