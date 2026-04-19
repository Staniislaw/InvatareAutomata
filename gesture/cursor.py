"""
gesture/cursor.py
Cursor verde afisat in UI — fara transparenta.
Deseneaza doar cursorul, click-urile trec la widget-urile de dedesubt.
"""

import tkinter as tk
import time


class VirtualCursor:

    CLICK_DIST     = 0.07
    CLICK_COOLDOWN = 1.5
    RADIUS         = 16

    def __init__(self, app):
        self.app          = app
        self._is_pinching = False
        self._last_click  = 0
        self._visible     = False

        # Canvas mic — se muta odata cu cursorul, nu acopera tot
        self._canvas = tk.Canvas(
            app,
            width=60, height=60,
            bg="#121212",
            highlightthickness=0,
            bd=0,
        )

        r = self.RADIUS
        self._ring = self._canvas.create_oval(
            60//2-r, 60//2-r, 60//2+r, 60//2+r,
            outline="#1DB954", width=2, fill=""
        )
        self._dot = self._canvas.create_oval(
            60//2-3, 60//2-3, 60//2+3, 60//2+3,
            fill="#1DB954", outline=""
        )

    def update(self, finger_x, finger_y, thumb_x, thumb_y, frame=None):
        import cv2

        w  = self.app.winfo_width()
        h  = self.app.winfo_height()
        cx = int(finger_x * w)
        cy = int(finger_y * h)
        r  = self.RADIUS

        dist        = ((finger_x - thumb_x)**2 + (finger_y - thumb_y)**2) ** 0.5
        is_pinching = dist < self.CLICK_DIST

        # Muta canvas-ul la pozitia cursorului
        offset = r + 5
        self._canvas.place(x=cx - offset, y=cy - offset)
        self._visible = True

        if is_pinching:
            self._canvas.itemconfig(self._ring, outline="#ffffff", width=3)
            self._canvas.itemconfig(self._dot,  fill="#ffffff")
        else:
            self._canvas.itemconfig(self._ring, outline="#1DB954", width=2)
            self._canvas.itemconfig(self._dot,  fill="#1DB954")

        # Click la leading edge
        if is_pinching and not self._is_pinching:
            if time.time() - self._last_click > self.CLICK_COOLDOWN:
                self._last_click = time.time()
                self.app.after(0, lambda: self._do_click(cx, cy))

        self._is_pinching = is_pinching

        # Punct mic pe camera
        if frame is not None:
            fh, fw = frame.shape[:2]
            fx = int(finger_x * fw)
            fy = int(finger_y * fh)
            color = (255,255,255) if is_pinching else (0,255,100)
            cv2.circle(frame, (fx, fy), 8, color, -1)

        return frame

    def hide(self):
        if self._visible:
            self._canvas.place_forget()
            self._visible     = False
            self._is_pinching = False

    def _do_click(self, x, y):
        # Ascunde canvas temporar ca sa gasim widget-ul corect
        self._canvas.place_forget()
        widget = self.app.winfo_containing(
            self.app.winfo_rootx() + x,
            self.app.winfo_rooty() + y
        )
        # Readuce canvas-ul
        r = self.RADIUS + 5
        self._canvas.place(x=x - r, y=y - r)

        if widget and widget != self.app and widget != self._canvas:
            try:
                widget.event_generate("<Button-1>", x=0, y=0)
                name = ""
                try:
                    name = widget.cget("text")[:20]
                except Exception:
                    pass
                print(f"[Cursor] Click: {widget.__class__.__name__} '{name}'")
            except Exception as e:
                print(f"[Cursor] Eroare: {e}")