# ── ui/player_panel.py ────────────────────────────────────────────────────────
# Panoul din stanga: coperta albumului, titlu, artist, butoane control, volum.
# Nu face apeluri Spotify direct — primeste callbacks din app.py.
# ──────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk
from PIL import ImageTk

from config import (
    BG_DARK, BG_ACTIVE,
    ACCENT, TEXT_PRI, TEXT_SEC, TEXT_DIM,
)
from utils import make_placeholder_cover


class PlayerPanel(tk.Frame):
    """
    Panou stanga: cover + info melodie + butoane play/pause/prev/next/like + volum.

    Callbacks asteptate (transmise din SpotifyApp):
        on_play_pause, on_next, on_prev, on_like, on_volume_change(value:int)
    """

    def __init__(self, parent, callbacks: dict, **kwargs):
        super().__init__(parent, bg=BG_DARK, width=300, **kwargs)
        self.pack_propagate(False)

        self._cb = callbacks          # dict cu callbacks
        self._volume_job = None       # debounce volum

        self._build(parent)

    def _build(self, parent):
        # ── Coperta ───────────────────────────────────────────────────────────
        self.cover_label = tk.Label(self, bg=BG_DARK)
        self.cover_label.pack(pady=(8, 16))
        self._show_placeholder()

        # ── Titlu melodie ─────────────────────────────────────────────────────
        self.title_var = tk.StringVar(value="—")
        tk.Label(self, textvariable=self.title_var,
                 bg=BG_DARK, fg=TEXT_PRI,
                 font=("Helvetica", 15, "bold"),
                 wraplength=260, justify="center").pack()

        # ── Artist ────────────────────────────────────────────────────────────
        self.artist_var = tk.StringVar(value="—")
        tk.Label(self, textvariable=self.artist_var,
                 bg=BG_DARK, fg=TEXT_SEC,
                 font=("Helvetica", 11)).pack(pady=(2, 16))

        # ── Butoane control ───────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.pack()

        base_btn = dict(
            bg=BG_DARK, fg=TEXT_SEC, bd=0, relief="flat",
            font=("Helvetica", 18), cursor="hand2",
            activebackground=BG_DARK, activeforeground=TEXT_PRI,
        )

        self.prev_btn = tk.Button(btn_frame, text="⏮",
                                  command=self._cb.get("on_prev"), **base_btn)
        self.play_btn = tk.Button(btn_frame, text="▶",
                                  command=self._cb.get("on_play_pause"),
                                  bg=BG_DARK, fg=ACCENT, bd=0, relief="flat",
                                  font=("Helvetica", 26), cursor="hand2",
                                  activebackground=BG_DARK, activeforeground=ACCENT)
        self.next_btn = tk.Button(btn_frame, text="⏭",
                                  command=self._cb.get("on_next"), **base_btn)
        self.like_btn = tk.Button(btn_frame, text="♡",
                                  command=self._cb.get("on_like"), **base_btn)

        self.prev_btn.grid(row=0, column=0, padx=8)
        self.play_btn.grid(row=0, column=1, padx=8)
        self.next_btn.grid(row=0, column=2, padx=8)
        self.like_btn.grid(row=0, column=3, padx=8)

        # ── Volum ─────────────────────────────────────────────────────────────
        vol_frame = tk.Frame(self, bg=BG_DARK)
        vol_frame.pack(fill="x", padx=16, pady=(20, 8))

        tk.Label(vol_frame, text="🔉", bg=BG_DARK, fg=TEXT_SEC,
                 font=("Helvetica", 12)).pack(side="left")

        self.vol_var = tk.IntVar(value=50)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("green.Horizontal.TScale",
                        background=BG_DARK,
                        troughcolor=BG_ACTIVE,
                        sliderlength=14,
                        sliderrelief="flat")

        self.vol_slider = ttk.Scale(
            vol_frame, from_=0, to=100, orient="horizontal",
            variable=self.vol_var,
            style="green.Horizontal.TScale",
            command=self._on_volume_move,
        )
        self.vol_slider.pack(side="left", fill="x", expand=True, padx=6)

        tk.Label(vol_frame, text="🔊", bg=BG_DARK, fg=TEXT_SEC,
                 font=("Helvetica", 12)).pack(side="left")

        self.vol_label = tk.Label(self, text="50%",
                                  bg=BG_DARK, fg=TEXT_DIM,
                                  font=("Helvetica", 10))
        self.vol_label.pack()

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Conectat")
        tk.Label(self, textvariable=self.status_var,
                 bg=BG_DARK, fg=TEXT_DIM,
                 font=("Helvetica", 9)).pack(side="bottom", pady=8)

    # ── Metode publice (apelate din app.py) ───────────────────────────────────

    def update_track(self, track: str, artist: str) -> None:
        self.title_var.set(track[:35] + "..." if len(track) > 35 else track)
        self.artist_var.set(artist[:30] + "..." if len(artist) > 30 else artist)

    def update_play_state(self, is_playing: bool) -> None:
        self.play_btn.config(text="⏸" if is_playing else "▶")

    def update_like(self, liked: bool) -> None:
        self.like_btn.config(
            text="♥" if liked else "♡",
            fg=ACCENT if liked else TEXT_SEC,
        )

    def update_volume(self, volume: int) -> None:
        self.vol_var.set(volume)
        self.vol_label.config(text=f"{volume}%")

    def update_cover(self, tk_image: ImageTk.PhotoImage) -> None:
        self._cover_tk = tk_image          # pastreaza referinta sa nu fie GC
        self.cover_label.config(image=self._cover_tk)

    def set_status(self, msg: str) -> None:
        self.status_var.set(msg)

    # ── Intern ────────────────────────────────────────────────────────────────

    def _show_placeholder(self) -> None:
        img = make_placeholder_cover((200, 200))
        from PIL import ImageTk as ITk
        self._cover_tk = ITk.PhotoImage(img)
        self.cover_label.config(image=self._cover_tk)

    def _on_volume_move(self, val: str) -> None:
        """Debounce: trimite volumul la Spotify dupa 2s de inactivitate."""
        v = int(float(val))
        self.vol_label.config(text=f"{v}%")
        if self._volume_job:
            self.after_cancel(self._volume_job)
        on_vol = self._cb.get("on_volume_change")
        if on_vol:
            self._volume_job = self.after(2000, lambda: on_vol(v))