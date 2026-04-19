"""
gesture/cursor.py
Cursor virtual — desenat in fereastra CAMEREI (nu peste UI).
Coordonatele degetului sunt mapate pe fereastra tkinter pentru click.
"""

import tkinter as tk
import time


class VirtualCursor:
    """
    Cursorul apare in fereastra camerei ca un cerc verde.
    Cand se face pinch, se detecteaza widget-ul tkinter
    de la coordonatele corespunzatoare si se simuleaza click.
    """

    CLICK_DIST     = 0.07   # distanta normalizata thumb+index pentru click
    CLICK_COOLDOWN = 1.0    # secunde intre click-uri

    def __init__(self, app):
        self.app  = app
        self._last_click_time = 0
        self._click_pending   = False

    def update(self, finger_x: float, finger_y: float,
               thumb_x: float, thumb_y: float, frame=None):
        """
        finger_x, finger_y = pozitia normalizata (0-1) a varfului degetului aratator
        thumb_x, thumb_y   = pozitia normalizata a degetului mare
        frame              = frame-ul OpenCV pe care desenam cursorul (optional)
        Returneaza frame-ul modificat.
        """
        import cv2
        import numpy as np

        # Coordonate in fereastra tkinter
        w = self.app.winfo_width()
        h = self.app.winfo_height()
        cx = int(finger_x * w)
        cy = int(finger_y * h)

        # Detecteaza pinch (click)
        dist = ((finger_x - thumb_x)**2 + (finger_y - thumb_y)**2) ** 0.5
        is_clicking = dist < self.CLICK_DIST

        # Deseneaza pe frame-ul camerei
        if frame is not None:
            fh, fw = frame.shape[:2]
            fx = int(finger_x * fw)
            fy = int(finger_y * fh)

            if is_clicking:
                cv2.circle(frame, (fx, fy), 22, (255, 255, 255), 3)
                cv2.circle(frame, (fx, fy), 6,  (255, 255, 255), -1)
                cv2.putText(frame, "CLICK", (fx - 25, fy - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            else:
                cv2.circle(frame, (fx, fy), 18, (0, 255, 100), 2)
                cv2.circle(frame, (fx, fy), 4,  (0, 255, 100), -1)
                cv2.putText(frame, "cursor", (fx - 20, fy - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,100), 1)

        # Declanseaza click
        if is_clicking and not self._click_pending and self._can_click():
            self._click_pending = True
            self.app.after(0, lambda: self._do_click(cx, cy))
        elif not is_clicking:
            self._click_pending = False

        return frame

    def _can_click(self):
        return time.time() - self._last_click_time > self.CLICK_COOLDOWN

    def _do_click(self, x, y):
        """Simuleaza click la coordonatele x, y in fereastra tkinter."""
        self._last_click_time = time.time()

        widget = self.app.winfo_containing(
            self.app.winfo_rootx() + x,
            self.app.winfo_rooty() + y
        )

        if widget and widget != self.app:
            try:
                widget.event_generate("<Button-1>", x=0, y=0)
                print(f"[Cursor] Click pe: {widget.__class__.__name__} — {widget.cget('text') if hasattr(widget, 'cget') else ''}")
            except Exception as e:
                print(f"[Cursor] Eroare click: {e}")
        else:
            print(f"[Cursor] Niciun widget la ({x}, {y})")