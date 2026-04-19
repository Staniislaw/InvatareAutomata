"""
gesture/recognizer.py
Primeste landmark-urile de la detector si returneaza gestul detectat.
"""

import time
import collections


class GestureRecognizer:
    # Cooldown intre actiuni (secunde)
    COOLDOWN = {
        "SWIPE_LEFT":    1.5,
        "SWIPE_RIGHT":   1.5,
        "PLAY_PAUSE":    1.5,
        "LIKE":          3.0,   # mare — evita spam
        "SELECT":        1.5,
        "SCROLL_UP":     0.15,
        "SCROLL_DOWN":   0.15,
        "VOLUME_UP":     0.4,
        "VOLUME_DOWN":   0.4,
    }

    # Cate frame-uri consecutive trebuie un gest ca sa fie confirmat
    CONFIRM_FRAMES = {
        "PLAY_PAUSE":  8,
        "LIKE":       12,   # trebuie tinut mai mult
        "SELECT":      8,
        "VOLUME_UP":   3,
        "VOLUME_DOWN": 3,
        "SWIPE_LEFT":  1,
        "SWIPE_RIGHT": 1,
        "SCROLL_UP":   2,
        "SCROLL_DOWN": 2,
    }

    SWIPE_VELOCITY = 1.8
    SWIPE_MIN_DIST = 0.12

    def __init__(self):
        self._last_action_time = {}
        self._position_history = collections.deque(maxlen=12)

        # Contor frame-uri consecutive per gest
        self._gesture_streak        = {}   # gest → count
        self._last_confirmed_gesture = None

    # ─────────────────────────────────────────────────
    #  API PUBLIC
    # ─────────────────────────────────────────────────

    def process(self, result):
        """
        Proceseaza un rezultat MediaPipe.
        Returneaza dict cu gesture confirmat (sau None daca nu e stabil inca).
        """
        empty = {'gesture': None, 'cursor': None,
                 'hand_y': None, 'fingers': [], 'raw_label': ''}

        if not result or not result.hand_landmarks:
            self._position_history.clear()
            self._gesture_streak.clear()
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

        # Gestul raw din frame-ul curent
        raw_gesture, label = self._classify(fingers, hand_lm, palm_y)

        # ── Confirmare pe N frame-uri consecutive ────
        confirmed = self._confirm(raw_gesture)

        return {
            'gesture':   confirmed,
            'cursor':    cursor,
            'hand_y':    palm_y,
            'fingers':   fingers,
            'raw_label': label,
        }

    def can_trigger(self, gesture):
        cooldown = self.COOLDOWN.get(gesture, 1.0)
        last = self._last_action_time.get(gesture, 0)
        return time.time() - last > cooldown

    def mark_triggered(self, gesture):
        self._last_action_time[gesture] = time.time()
        # Reset streak dupa declansare — nu se mai repeta pana nu eliberezi
        self._gesture_streak[gesture] = 0

    # ─────────────────────────────────────────────────
    #  CONFIRMARE FRAME-URI
    # ─────────────────────────────────────────────────

    def _confirm(self, raw_gesture):
        """
        Un gest e confirmat doar daca apare pe N frame-uri consecutive.
        Daca gestul se schimba, resetam contorul.
        """
        if raw_gesture is None:
            self._gesture_streak.clear()
            return None

        needed = self.CONFIRM_FRAMES.get(raw_gesture, 5)

        # Incrementam contorul pentru gestul curent
        # si resetam toate celelalte
        for g in list(self._gesture_streak.keys()):
            if g != raw_gesture:
                self._gesture_streak[g] = 0

        self._gesture_streak[raw_gesture] = self._gesture_streak.get(raw_gesture, 0) + 1
        count = self._gesture_streak[raw_gesture]

        # Confirmat exact cand atinge pragul — nu la fiecare frame dupa
        if count == needed:
            return raw_gesture

        return None

    # ─────────────────────────────────────────────────
    #  LOGICA INTERNA
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

    def _detect_swipe(self):
        if len(self._position_history) < 6:
            return None
        oldest  = self._position_history[0]
        newest  = self._position_history[-1]
        dt = newest[2] - oldest[2]
        if dt < 0.001:
            return None
        dx = newest[0] - oldest[0]
        velocity_x = dx / dt
        dist = abs(dx)
        if dist > self.SWIPE_MIN_DIST:
            if velocity_x > self.SWIPE_VELOCITY:
                return "SWIPE_RIGHT"
            elif velocity_x < -self.SWIPE_VELOCITY:
                return "SWIPE_LEFT"
        return None

    def _classify(self, fingers, lm, palm_y):
        thumb, index, middle, ring, pinky = fingers
        count = sum(fingers)

        # Swipe prioritate maxima
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