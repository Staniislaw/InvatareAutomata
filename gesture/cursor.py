"""
gesture/cursor.py
Cursor virtual controlat de degetul aratator.
- Deget aratator = misca cursorul
- Deget mare + aratator apropiati = click
Se suprapune peste fereastra tkinter ca un canvas transparent.
"""

import tkinter as tk
import time


class VirtualCursor:
    """
    Deseneaza un cursor verde peste UI si detecteaza click-uri.
    Se ataseaza la fereastra principala SpotifyApp.
    """

    CURSOR_RADIUS  = 18
    CLICK_DIST     = 0.07   # distanta normalizata thumb+index pentru click
    CLICK_COOLDOWN = 1.0    # secunde intre click-uri

    def __init__(self, app):
        """
        app = instanta SpotifyApp (tk.Tk)
        """
        self.app     = app
        self.visible = False
        self.x       = 0
        self.y       = 0

        self._last_click_time = 0
        self._click_pending   = False

        # Canvas transparent peste toata fereastra
        self._canvas = tk.Canvas(
            app,
            bg="black",
            highlightthickness=0,
            cursor="none",
        )
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Transparent pe Windows
        try:
            app.wm_attributes("-transparentcolor", "black")
        except Exception:
            pass

        # Cursorul (cerc + punct central)
        self._circle = self._canvas.create_oval(
            0, 0, 0, 0,
            outline="#1DB954", width=2, fill=""
        )
        self._dot = self._canvas.create_oval(
            0, 0, 0, 0,
            fill="#1DB954", outline=""
        )
        self._label = self._canvas.create_text(
            0, 0, text="", fill="#1DB954",
            font=("Helvetica", 10)
        )

        # Click indicator
        self._click_circle = self._canvas.create_oval(
            0, 0, 0, 0,
            outline="#ffffff", width=2, fill=""
        )

        self.app.lift(self._canvas)

    def update(self, finger_x: float, finger_y: float,
               thumb_x: float, thumb_y: float):
        """
        Actualizeaza pozitia cursorului.
        finger_x, finger_y = pozitia normalizata (0-1) a varfului degetului aratator
        thumb_x, thumb_y   = pozitia normalizata a degetului mare
        """
        self.visible = True

        # Converteste din coordonate camera (0-1) in coordonate ecran
        w = self.app.winfo_width()
        h = self.app.winfo_height()

        # Camera e flip-ata deja in detector — x e direct
        self.x = int(finger_x * w)
        self.y = int(finger_y * h)

        r = self.CURSOR_RADIUS

        # Deseneaza cursorul
        self._canvas.coords(self._circle,
                            self.x - r, self.y - r,
                            self.x + r, self.y + r)
        self._canvas.coords(self._dot,
                            self.x - 3, self.y - 3,
                            self.x + 3, self.y + 3)

        # Detecteaza click (thumb + index apropiati)
        dist = ((finger_x - thumb_x)**2 + (finger_y - thumb_y)**2) ** 0.5
        is_clicking = dist < self.CLICK_DIST

        if is_clicking:
            # Cerc alb = click activ
            self._canvas.coords(self._click_circle,
                                self.x - r - 6, self.y - r - 6,
                                self.x + r + 6, self.y + r + 6)
            self._canvas.itemconfig(self._click_circle, outline="#ffffff")
            self._canvas.itemconfig(self._label, text="CLICK",
                                    fill="#ffffff")
            self._canvas.coords(self._label, self.x, self.y - r - 18)

            # Declanseaza click o singura data
            if not self._click_pending and self._can_click():
                self._click_pending = True
                self.app.after(0, lambda: self._do_click(self.x, self.y))
        else:
            self._canvas.coords(self._click_circle, 0, 0, 0, 0)
            self._canvas.itemconfig(self._label, text="")
            self._click_pending = False

        self.app.lift(self._canvas)

    def hide(self):
        """Ascunde cursorul cand nu se vede mana."""
        self.visible = False
        self._canvas.coords(self._circle, 0, 0, 0, 0)
        self._canvas.coords(self._dot, 0, 0, 0, 0)
        self._canvas.coords(self._click_circle, 0, 0, 0, 0)
        self._canvas.itemconfig(self._label, text="")

    def _can_click(self):
        return time.time() - self._last_click_time > self.CLICK_COOLDOWN

    def _do_click(self, x, y):
        """Simuleaza un click tkinter la coordonatele x, y."""
        self._last_click_time = time.time()

        # Gaseste widget-ul de sub cursor
        widget = self._find_widget_at(x, y)
        if widget:
            try:
                # Simuleaza Button-1 click pe widget
                widget.event_generate("<Button-1>", x=0, y=0)
                print(f"[Cursor] Click pe: {widget.__class__.__name__}")
            except Exception as e:
                print(f"[Cursor] Eroare click: {e}")

    def _find_widget_at(self, x, y):
        """Gaseste widget-ul tkinter la coordonatele absolute x, y."""
        try:
            # Coboram in ierarhia de widget-uri
            widget = self.app.winfo_containing(
                self.app.winfo_rootx() + x,
                self.app.winfo_rooty() + y
            )
            # Sarim canvas-ul propriu
            if widget == self._canvas:
                return None
            return widget
        except Exception:
            return None