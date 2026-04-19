"""
gesture/recognizer.py
Primeste landmark-urile de la detector si returneaza gestul detectat.
Logica de interpretare este separata complet de camera.
"""

import numpy as np
import time
import collections


class GestureRecognizer:
    """
    Interpreteaza landmark-urile MediaPipe si returneaza gesturi.
    Gesturi suportate:
        - SWIPE_LEFT / SWIPE_RIGHT  → melodie anterioara / urmatoare
        - VOLUME_UP / VOLUME_DOWN   → volum (pozitie mana sus/jos)
        - PLAY_PAUSE                → Peace ✌
        - LIKE                      → Thumbs Up 👍
        - SELECT                    → Pumn ✊ (selectie din playlist)
        - SCROLL_UP / SCROLL_DOWN   → scroll playlist (deget sus/jos)
        - POINTING                  → cursor activ (deget aratator)
    """

    # Cooldown intre actiuni (secunde)
    COOLDOWN = {
        "SWIPE_LEFT":    1.2,
        "SWIPE_RIGHT":   1.2,
        "PLAY_PAUSE":    1.0,
        "LIKE":          1.0,
        "SELECT":        1.0,
        "SCROLL_UP":     0.15,
        "SCROLL_DOWN":   0.15,
        "VOLUME_UP":     0.3,
        "VOLUME_DOWN":   0.3,
    }

    # Prag swipe (unitati normalizate/secunda)
    SWIPE_VELOCITY = 1.8
    SWIPE_MIN_DIST = 0.12

    def __init__(self):
        self._last_action_time = {}
        self._position_history = collections.deque(maxlen=12)
        self._gesture_history  = collections.deque(maxlen=6)

    # ─────────────────────────────────────────────────
    #  API PUBLIC
    # ─────────────────────────────────────────────────

    def process(self, result):
        """
        Proceseaza un rezultat MediaPipe.
        Returneaza dict cu:
            {
                'gesture':   str sau None,   # gestul detectat
                'cursor':    (x, y) sau None, # pozitia cursorului (0-1)
                'hand_y':    float sau None,  # pozitia Y a palmei (0=sus, 1=jos)
                'fingers':   list[bool],      # starea degetelor
                'raw_label': str,             # label descriptiv
            }
        """
        empty = {'gesture': None, 'cursor': None,
                 'hand_y': None, 'fingers': [], 'raw_label': ''}

        if not result or not result.hand_landmarks:
            self._position_history.clear()
            return empty

        hand_lm   = result.hand_landmarks[0]
        handedness = "Right"
        if result.handedness:
            handedness = result.handedness[0][0].display_name

        fingers   = self._get_fingers(hand_lm, handedness)
        palm_x    = hand_lm[9].x
        palm_y    = hand_lm[9].y
        cursor    = (hand_lm[8].x, hand_lm[8].y)  # varf deget aratator

        # Istoric pozitie pentru swipe
        self._position_history.append((palm_x, palm_y, time.time()))

        # Detecteaza gestul
        gesture, label = self._classify(fingers, hand_lm, palm_y)

        return {
            'gesture':   gesture,
            'cursor':    cursor,
            'hand_y':    palm_y,
            'fingers':   fingers,
            'raw_label': label,
        }

    def can_trigger(self, gesture):
        """Verifica daca gestul poate fi declansat (cooldown)."""
        cooldown = self.COOLDOWN.get(gesture, 1.0)
        last = self._last_action_time.get(gesture, 0)
        return time.time() - last > cooldown

    def mark_triggered(self, gesture):
        """Marcheaza gestul ca declansat (reseteaza cooldown)."""
        self._last_action_time[gesture] = time.time()

    # ─────────────────────────────────────────────────
    #  LOGICA INTERNA
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

    def _detect_swipe(self):
        """Detecteaza swipe din istoricul de pozitii."""
        if len(self._position_history) < 6:
            return None

        oldest = self._position_history[0]
        newest = self._position_history[-1]
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
        """Clasifica gestul din starea degetelor si pozitie."""
        thumb, index, middle, ring, pinky = fingers
        count = sum(fingers)

        # ── 1. Swipe (prioritate maxima) ─────────────
        swipe = self._detect_swipe()
        if swipe:
            self._position_history.clear()
            return swipe, f"→ {swipe}"

        # ── 2. Pumn = SELECT ─────────────────────────
        if count == 0:
            return "SELECT", "✊ Select"

        # ── 3. Palma deschisa = VOLUME control ───────
        if count >= 4:
            if palm_y < 0.35:
                return "VOLUME_UP", "🖐 Volum +"
            elif palm_y > 0.65:
                return "VOLUME_DOWN", "🖐 Volum -"
            return "OPEN_PALM", "🖐 Palma"

        # ── 4. Peace = PLAY/PAUSE ────────────────────
        if not thumb and index and middle and not ring and not pinky:
            return "PLAY_PAUSE", "✌ Play/Pause"

        # ── 5. Thumbs up = LIKE ──────────────────────
        if thumb and not index and not middle and not ring and not pinky:
            if lm[4].y < lm[9].y:
                return "LIKE", "👍 Like"

        # ── 6. Pointing = SCROLL / CURSOR ────────────
        if not thumb and index and not middle and not ring and not pinky:
            if lm[8].y < lm[6].y - 0.05:
                return "SCROLL_UP", "☝ Scroll Sus"
            elif lm[8].y > lm[6].y + 0.05:
                return "SCROLL_DOWN", "👇 Scroll Jos"
            return "POINTING", "☝ Cursor"

        # ── 7. Call me = nimic (evita false positive) ─
        if thumb and not index and not middle and not ring and pinky:
            return None, "🤙"

        return None, f"({count} degete)"