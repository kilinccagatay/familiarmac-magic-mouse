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
                return [Gesture(s['mode'], s['count'], 'end')]
            valid = (not s['blocked'] and s['count'] == 2 and now - s['start'] <= self.t.tap_seconds
                     and s['travel'] <= self.t.tap_travel and s['chord'])
            if not valid:
                self.last_tap = None
                return []
            # Pair distinct complete contact sequences. A triple tap fires once.
            if self.last_tap is not None and 0 <= now - self.last_tap <= self.t.double_seconds:
                self.last_tap = None
                return [Gesture('double-tap', 2)]
            self.last_tap = now
            return []
        if self.session is None:
            self.session = dict(start=now, origins={}, count=0, travel=0, blocked=frame.clicked,
                                chord=False, mode=None, distance=None, pair=None)
        s = self.session
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
            elif travel >= self.t.gesture_travel and travel > spread * 1.5:
                s['mode'] = 'swipe'
        if s['mode']:
            self.last_tap = None
            return [Gesture(s['mode'], 2, 'update' if old_mode else 'begin', dx, dy,
                            distance / s['distance'] if s['distance'] else 1)]
        return []
