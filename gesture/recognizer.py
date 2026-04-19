"""
gesture/recognizer.py
"""

import time
import collections


class GestureRecognizer:

    COOLDOWN = {
        "SWIPE_LEFT":    1.5,
        "SWIPE_RIGHT":   1.5,
        "PLAY_PAUSE":    1.5,
        "LIKE":          3.0,
        "SELECT":        1.5,
        "SCROLL_UP":     0.15,
        "SCROLL_DOWN":   0.15,
        "VOLUME_UP":     0.4,
        "VOLUME_DOWN":   0.4,
    }

    # Frame-uri consecutive necesare dupa smoothing
    CONFIRM_FRAMES = {
        "PLAY_PAUSE":  5,
        "LIKE":        6,
        "SELECT":      5,
        "VOLUME_UP":   3,
        "VOLUME_DOWN": 3,
        "SWIPE_LEFT":  1,
        "SWIPE_RIGHT": 1,
        "SCROLL_UP":   2,
        "SCROLL_DOWN": 2,
    }

    SWIPE_VELOCITY = 1.8
    SWIPE_MIN_DIST = 0.12

    # Fereastra de smoothing — voteaza gestul majoritar din ultimele N frame-uri
    SMOOTH_WINDOW = 8

    def __init__(self):
        self._last_action_time  = {}
        self._position_history  = collections.deque(maxlen=12)
        self._gesture_streak    = {}
        self._raw_history       = collections.deque(maxlen=self.SMOOTH_WINDOW)

    def process(self, result):
        empty = {'gesture': None, 'cursor': None,
                 'hand_y': None, 'fingers': [], 'raw_label': ''}

        if not result or not result.hand_landmarks:
            self._position_history.clear()
            self._gesture_streak.clear()
            self._raw_history.clear()
            return empty

        hand_lm    = result.hand_landmarks[0]
        handedness = "Right"
        if result.handedness:
            handedness = result.handedness[0][0].display_name

        fingers = self._get_fingers(hand_lm, handedness)
        palm_x  = hand_lm[9].x
        palm_y  = hand_lm[9].y
        cursor  = (hand_lm[8].x, hand_lm[8].y)

        self._position_history.append((palm_x, palm_y, time.time()))

        raw_gesture, label = self._classify(fingers, hand_lm, palm_y)

        # ── Smoothing: vot majoritar din ultimele N frame-uri ─────────────────
        self._raw_history.append(raw_gesture)
        smoothed = self._smooth()

        # ── Confirmare pe frame-uri consecutive ───────────────────────────────
        confirmed = self._confirm(smoothed)

        return {
            'gesture':   confirmed,
            'cursor':    cursor,
            'hand_y':    palm_y,
            'fingers':   fingers,
            'raw_label': label,
        }

    def _smooth(self):
        """Returneaza gestul majoritar din fereastra recenta."""
        valid = [g for g in self._raw_history if g is not None]
        if not valid:
            return None
        counts = collections.Counter(valid)
        best, freq = counts.most_common(1)[0]
        # Trebuie sa apara in cel putin 50% din frame-uri
        if freq >= len(self._raw_history) * 0.5:
            return best
        return None

    def _confirm(self, smoothed_gesture):
        """Confirma gestul dupa N frame-uri consecutive stabile."""
        if smoothed_gesture is None:
            self._gesture_streak.clear()
            return None

        needed = self.CONFIRM_FRAMES.get(smoothed_gesture, 4)

        for g in list(self._gesture_streak.keys()):
            if g != smoothed_gesture:
                self._gesture_streak[g] = 0

        self._gesture_streak[smoothed_gesture] = \
            self._gesture_streak.get(smoothed_gesture, 0) + 1
        count = self._gesture_streak[smoothed_gesture]

        # Declanseaza exact la prag — nu la fiecare frame dupa
        if count == needed:
            return smoothed_gesture

        return None

    def can_trigger(self, gesture):
        cooldown = self.COOLDOWN.get(gesture, 1.0)
        return time.time() - self._last_action_time.get(gesture, 0) > cooldown

    def mark_triggered(self, gesture):
        self._last_action_time[gesture] = time.time()
        self._gesture_streak[gesture] = 0
        self._raw_history.clear()

    def _get_fingers(self, lm, handedness):
        fingers = []
        if handedness == "Right":
            fingers.append(lm[4].x < lm[3].x)
        else:
            fingers.append(lm[4].x > lm[3].x)
        for tip, joint in [(8,6),(12,10),(16,14),(20,18)]:
            fingers.append(lm[tip].y < lm[joint].y)
        return fingers

    def _detect_swipe(self):
        if len(self._position_history) < 6:
            return None
        oldest = self._position_history[0]
        newest = self._position_history[-1]
        dt = newest[2] - oldest[2]
        if dt < 0.001:
            return None
        dx = newest[0] - oldest[0]
        velocity_x = dx / dt
        if abs(dx) > self.SWIPE_MIN_DIST:
            if velocity_x > self.SWIPE_VELOCITY:
                return "SWIPE_RIGHT"
            elif velocity_x < -self.SWIPE_VELOCITY:
                return "SWIPE_LEFT"
        return None

    def _classify(self, fingers, lm, palm_y):
        thumb, index, middle, ring, pinky = fingers
        count = sum(fingers)

        swipe = self._detect_swipe()
        if swipe:
            self._position_history.clear()
            return swipe, f"→ {swipe}"

        if count == 0:
            return "SELECT", "✊ Select"

        if count >= 4:
            if palm_y < 0.35:
                return "VOLUME_UP", "🖐 Volum +"
            elif palm_y > 0.65:
                return "VOLUME_DOWN", "🖐 Volum -"
            return "OPEN_PALM", "🖐 Palma"

        if not thumb and index and middle and not ring and not pinky:
            return "PLAY_PAUSE", "✌ Play/Pause"

        if thumb and not index and not middle and not ring and not pinky:
            if lm[4].y < lm[9].y:
                return "LIKE", "👍 Like"

        if not thumb and index and not middle and not ring and not pinky:
            if lm[8].y < lm[6].y - 0.05:
                return "SCROLL_UP", "☝ Scroll Sus"
            elif lm[8].y > lm[6].y + 0.05:
                return "SCROLL_DOWN", "👇 Scroll Jos"
            return "POINTING", "☝ Cursor"

        return None, f"({count} degete)"