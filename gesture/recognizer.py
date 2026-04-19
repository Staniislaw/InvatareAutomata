"""
gesture/recognizer.py
O functie separata pentru fiecare gest.
Activ momentan: PLAY_PAUSE, VOLUME_UP, VOLUME_DOWN
"""

import time
import collections


class GestureRecognizer:

    def __init__(self):
        self._last_action_time = {}
        self._position_history = collections.deque(maxlen=15)

    # ─────────────────────────────────────────────────
    #  FUNCTII INDIVIDUALE DE DETECTARE
    # ─────────────────────────────────────────────────

    def detect_play_pause(self, fingers):
        """
        Gest: Peace ✌ — index + middle ridicate, restul jos.
        """
        thumb, index, middle, ring, pinky = fingers
        return (not thumb and index and middle and not ring and not pinky)

    def detect_volume_up(self, fingers, palm_y):
        """
        Gest: Palma deschisa in jumatatea de SUS a ecranului.
        palm_y < 0.4 inseamna sus (0=top, 1=bottom).
        """
        count = sum(fingers)
        return count >= 4 and palm_y < 0.4

    def detect_volume_down(self, fingers, palm_y):
        """
        Gest: Palma deschisa in jumatatea de JOS a ecranului.
        palm_y > 0.6 inseamna jos.
        """
        count = sum(fingers)
        return count >= 4 and palm_y > 0.6

    # ─────────────────────────────────────────────────
    #  PROCESOR PRINCIPAL
    # ─────────────────────────────────────────────────

    def process(self, result):
        """
        Proceseaza rezultatul MediaPipe si returneaza gestul activ.
        """
        empty = {'gesture': None, 'fingers': [], 'palm_y': None, 'raw_label': ''}

        if not result or not result.hand_landmarks:
            return empty

        hand_lm    = result.hand_landmarks[0]
        handedness = "Right"
        if result.handedness:
            handedness = result.handedness[0][0].display_name

        fingers = self._get_fingers(hand_lm, handedness)
        palm_y  = hand_lm[9].y  # 0=sus, 1=jos

        # ── Testeaza fiecare gest ─────────────────────
        gesture   = None
        raw_label = f"({sum(fingers)} degete)"

        if self.detect_play_pause(fingers):
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
        cooldowns = {
            "PLAY_PAUSE":  2.0,
            "VOLUME_UP":   0.5,
            "VOLUME_DOWN": 0.5,
        }
        cooldown = cooldowns.get(gesture, 1.0)
        return time.time() - self._last_action_time.get(gesture, 0) > cooldown

    def mark_triggered(self, gesture):
        self._last_action_time[gesture] = time.time()

    # ─────────────────────────────────────────────────
    #  HELPER
    # ─────────────────────────────────────────────────

    def _get_fingers(self, lm, handedness):
        """Returneaza [thumb, index, middle, ring, pinky] True=ridicat."""
        fingers = []
        if handedness == "Right":
            fingers.append(lm[4].x < lm[3].x)
        else:
            fingers.append(lm[4].x > lm[3].x)
        for tip, joint in [(8,6),(12,10),(16,14),(20,18)]:
            fingers.append(lm[tip].y < lm[joint].y)
        return fingers