"""
gesture/recognizer.py
Gesturi: PLAY_PAUSE, VOLUME_UP, VOLUME_DOWN, SWIPE_RIGHT, SWIPE_LEFT
Swipe se face cu PUMNUL inchis — evita conflicte cu alte gesturi.
"""

import time
import collections


class GestureRecognizer:

    COOLDOWN = {
        "PLAY_PAUSE":   2.0,
        "VOLUME_UP":    0.5,
        "VOLUME_DOWN":  0.5,
        "SWIPE_RIGHT":  1.5,
        "SWIPE_LEFT":   1.5,
        "LIKE":         3.0,
    }

    def __init__(self):
        self._last_action_time = {}
        self._position_history = collections.deque(maxlen=15)
        self._swipe_blocked_until = 0  # bloc dupa swipe

    # ─────────────────────────────────────────────────
    #  FUNCTII INDIVIDUALE
    # ─────────────────────────────────────────────────

    def detect_play_pause(self, fingers):
        """✌ Peace — index + middle sus, restul jos."""
        thumb, index, middle, ring, pinky = fingers
        return not thumb and index and middle and not ring and not pinky

    def detect_volume_up(self, fingers, palm_y):
        """🖐 Palma deschisa in JUMATATEA DE SUS a ecranului."""
        return sum(fingers) >= 4 and palm_y < 0.4

    def detect_volume_down(self, fingers, palm_y):
        """🖐 Palma deschisa in JUMATATEA DE JOS a ecranului."""
        return sum(fingers) >= 4 and palm_y > 0.6

    def detect_like(self, fingers, hand_lm):
        """
        Degetul mare + index ridicate si apropiate, restul inchise.
        Backup: Thumbs up 👍 (doar degetul mare ridicat sus).
        """
        thumb, index, middle, ring, pinky = fingers
        # ── Backup: Thumbs up 👍 ─────────────────────────────────
        if thumb and not index and not middle and not ring and not pinky:
            if hand_lm[4].y < hand_lm[9].y:  # degetul mare ridicat sus
                return True

        return False

    def detect_swipe_right(self, fingers, hand_lm):
        """
        PUMN inchis miscat de la stanga la dreapta = Next song.
        Pumnul evita conflictele cu Play/Pause si Volum.
        """
        if sum(fingers) > 1:  # nu e pumn — ignora
            self._position_history.clear()
            return False

        self._position_history.append((hand_lm[9].x, time.time()))

        if len(self._position_history) < 6:
            return False

        oldest = self._position_history[0]
        newest = self._position_history[-1]
        dt     = newest[1] - oldest[1]
        dx     = newest[0] - oldest[0]
        dist   = abs(dx)

        if dist > 0.3 and dt < 2.0 and dx > 0:
            self._position_history.clear()
            return True
        return False

    def detect_swipe_left(self, fingers, hand_lm):
        """
        PUMN inchis miscat de la dreapta la stanga = Previous song.
        """
        if sum(fingers) > 1:  # nu e pumn — ignora
            self._position_history.clear()
            return False

        self._position_history.append((hand_lm[9].x, time.time()))

        if len(self._position_history) < 6:
            return False

        oldest = self._position_history[0]
        newest = self._position_history[-1]
        dt     = newest[1] - oldest[1]
        dx     = newest[0] - oldest[0]
        dist   = abs(dx)

        if dist > 0.3 and dt < 2.0 and dx < 0:
            self._position_history.clear()
            return True
        return False

    # ─────────────────────────────────────────────────
    #  PROCESOR PRINCIPAL
    # ─────────────────────────────────────────────────

    def process(self, result):
        empty = {'gesture': None, 'fingers': [], 'palm_y': None, 'raw_label': ''}

        if not result or not result.hand_landmarks:
            self._position_history.clear()
            return empty

        hand_lm    = result.hand_landmarks[0]
        handedness = "Right"
        if result.handedness:
            handedness = result.handedness[0][0].display_name

        fingers = self._get_fingers(hand_lm, handedness)
        palm_y  = hand_lm[9].y

        gesture   = None
        raw_label = f"({sum(fingers)} degete)"

        # ── Swipe primul — are prioritate ────────────
        if self.detect_swipe_right(fingers, hand_lm):
            gesture   = "SWIPE_RIGHT"
            raw_label = "✊→ Next"
            # Blocheaza play/pause si volum 1.5s dupa swipe
            self._swipe_blocked_until = time.time() + 1.5

        elif self.detect_swipe_left(fingers, hand_lm):
            gesture   = "SWIPE_LEFT"
            raw_label = "←✊ Prev"
            self._swipe_blocked_until = time.time() + 1.5

        # ── Celelalte gesturi doar daca nu e bloc ────
        elif time.time() > self._swipe_blocked_until:

            if self.detect_like(fingers, hand_lm):
                gesture   = "LIKE"
                raw_label = "🫰 Like!"

            elif self.detect_play_pause(fingers):
                gesture   = "PLAY_PAUSE"
                raw_label = "✌ Play/Pause"

            elif self.detect_volume_up(fingers, palm_y):
                gesture   = "VOLUME_UP"
                raw_label = f"🖐 Volum + (y={palm_y:.2f})"

            elif self.detect_volume_down(fingers, palm_y):
                gesture   = "VOLUME_DOWN"
                raw_label = f"🖐 Volum - (y={palm_y:.2f})"

        return {
            'gesture':   gesture,
            'fingers':   fingers,
            'palm_y':    palm_y,
            'raw_label': raw_label,
        }

    # ─────────────────────────────────────────────────
    #  COOLDOWN
    # ─────────────────────────────────────────────────

    def can_trigger(self, gesture):
        cooldown = self.COOLDOWN.get(gesture, 1.0)
        return time.time() - self._last_action_time.get(gesture, 0) > cooldown

    def mark_triggered(self, gesture):
        self._last_action_time[gesture] = time.time()

    # ─────────────────────────────────────────────────
    #  HELPER
    # ─────────────────────────────────────────────────

    def _get_fingers(self, lm, handedness):
        fingers = []
        if handedness == "Right":
            fingers.append(lm[4].x < lm[3].x)
        else:
            fingers.append(lm[4].x > lm[3].x)
        for tip, joint in [(8,6),(12,10),(16,14),(20,18)]:
            fingers.append(lm[tip].y < lm[joint].y)
        return fingers