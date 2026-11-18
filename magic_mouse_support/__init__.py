"""Independent Magic Mouse protocol and gesture library (MIT)."""
from .protocol import Contact, Frame, decode, device_id
from .gestures import Gesture, Recognizer, Thresholds
__version__ = '0.2.0'
__all__ = ['Contact', 'Frame', 'decode', 'device_id', 'Gesture', 'Recognizer', 'Thresholds']
