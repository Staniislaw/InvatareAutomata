"""
gesture/cursor.py
Cursor verde afisat in UI (peste interfata Spotify).
Cursorul e doar vizual — click-urile trec prin el la widget-urile de dedesubt.
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

        # Canvas transparent peste UI — doar pentru desen cursor
        self._canvas = tk.Canvas(
            app,
            bg="#000001",
            highlightthickness=0,
            bd=0,
        )
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Dezactiveaza toate evenimentele pe canvas
        # ca sa treaca click-urile la widget-urile de dedesubt
        self._canvas.bind("<Button-1>", lambda e: self._pass_click(e))
        self._canvas.configure(takefocus=False)
        # Seteaza culoarea transparenta pe Windows
        try:
            app.wm_attributes("-transparentcolor", "#000001")
        except Exception:
            pass

        # Elementele cursor
        r = self.RADIUS
        self._ring  = self._canvas.create_oval(0,0,0,0, outline="#1DB954", width=2, fill="")
        self._dot   = self._canvas.create_oval(0,0,0,0, fill="#1DB954", outline="")
        self._text  = self._canvas.create_text(0,0, text="", fill="#1DB954",
                                                font=("Helvetica", 9, "bold"))

        # Ridica canvas-ul deasupra tuturor widget-urilor
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._canvas.after(100, self._raise_canvas)

    def _raise_canvas(self):
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

    def _pass_click(self, event):
        """Transmite click-ul la widget-ul de dedesubt."""
        self._canvas.lower()
        widget = self.app.winfo_containing(event.x_root, event.y_root)
        self._canvas.after(10, self._raise_canvas)
        if widget and widget != self._canvas:
            try:
                widget.event_generate("<Button-1>", x=0, y=0)
            except Exception:
                pass

    def update(self, finger_x, finger_y, thumb_x, thumb_y, frame=None):
        """
        Actualizeaza pozitia cursorului in UI.
        finger_x, finger_y = coordonate normalizate 0-1
        """
        import cv2

        w  = self.app.winfo_width()
        h  = self.app.winfo_height()
        cx = int(finger_x * w)
        cy = int(finger_y * h)
        r  = self.RADIUS

        dist        = ((finger_x - thumb_x)**2 + (finger_y - thumb_y)**2) ** 0.5
        is_pinching = dist < self.CLICK_DIST

        # ── Deseneaza cursorul in UI ──────────────────
        if is_pinching:
            # Cerc alb = click
            self._canvas.itemconfig(self._ring, outline="#ffffff", width=3)
            self._canvas.itemconfig(self._dot,  fill="#ffffff")
            self._canvas.itemconfig(self._text, text="●", fill="#ffffff")
        else:
            # Cerc verde = cursor normal
            self._canvas.itemconfig(self._ring, outline="#1DB954", width=2)
            self._canvas.itemconfig(self._dot,  fill="#1DB954")
            self._canvas.itemconfig(self._text, text="", fill="#1DB954")

        self._canvas.coords(self._ring, cx-r, cy-r, cx+r, cy+r)
        self._canvas.coords(self._dot,  cx-3,  cy-3,  cx+3,  cy+3)
        self._canvas.coords(self._text, cx, cy - r - 10)

        # ── Click la leading edge ─────────────────────
        if is_pinching and not self._is_pinching:
            if time.time() - self._last_click > self.CLICK_COOLDOWN:
                self._last_click = time.time()
                self.app.after(0, lambda: self._do_click(cx, cy))

        self._is_pinching = is_pinching

        # ── Deseneaza indicator mic pe camera ─────────
        if frame is not None:
            fh, fw = frame.shape[:2]
            fx = int(finger_x * fw)
            fy = int(finger_y * fh)
            color = (255,255,255) if is_pinching else (0,255,100)
            cv2.circle(frame, (fx, fy), 8, color, -1)

        return frame

    def hide(self):
        """Ascunde cursorul cand nu e mana detectata."""
        self._canvas.coords(self._ring, 0,0,0,0)
        self._canvas.coords(self._dot,  0,0,0,0)
        self._canvas.itemconfig(self._text, text="")

    def _do_click(self, x, y):
        """Click pe widget-ul de la coordonatele x,y din UI."""
        # Coboara canvas temporar ca sa gasim widget-ul corect
        self._canvas.lower()
        widget = self.app.winfo_containing(
            self.app.winfo_rootx() + x,
            self.app.winfo_rooty() + y
        )
        self._canvas.after(50, self._raise_canvas)

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
        else:
            print(f"[Cursor] Niciun widget la ({x},{y})")