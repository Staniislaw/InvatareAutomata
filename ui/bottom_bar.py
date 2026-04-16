# ── ui/bottom_bar.py ──────────────────────────────────────────────────────────
# Bara de jos fixa — design identic cu bara de redare Spotify.
# [cover + titlu + artist | prev/play/next | volum]
# ──────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk
from PIL import ImageTk

from config import BG_DARK, BG_ACTIVE, ACCENT, TEXT_PRI, TEXT_SEC, TEXT_DIM
from utils import make_placeholder_cover


class BottomBar(tk.Frame):
    """
    Bara de redare jos (inaltime fixa ~80px), 3 coloane:
      LEFT:   cover mic (56x56) + titlu + artist + like
      CENTER: prev | play/pause | next
      RIGHT:  volum slider
    """

    def __init__(self, parent, callbacks: dict, **kwargs):
        super().__init__(parent, bg="#181818",
                         highlightbackground="#282828",
                         highlightthickness=1,
                         height=80, **kwargs)
        self.pack_propagate(False)

        self._cb = callbacks
        self._volume_job = None
        self._cover_tk = None
        self._is_playing = False

        self._setup_styles()
        self._build()

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Bar.Horizontal.TScale",
            background="#181818",
            troughcolor="#535353",
            sliderlength=12,
            sliderrelief="flat",
            troughrelief="flat",
        )
        style.map(
            "Bar.Horizontal.TScale",
            troughcolor=[("active", "#727272")],
        )

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)

        # ── LEFT: track info ──────────────────────────────────────────────────
        left = tk.Frame(self, bg="#181818")
        left.grid(row=0, column=0, sticky="w", padx=16, pady=12)

        # Cover mic 56x56
        self.cover_lbl = tk.Label(left, bg="#282828", width=56, height=56)
        self.cover_lbl.pack(side="left")
        self._show_placeholder()

        info = tk.Frame(left, bg="#181818")
        info.pack(side="left", padx=(10, 0))

        self.title_var = tk.StringVar(value="Nicio melodie")
        tk.Label(info, textvariable=self.title_var,
                 bg="#181818", fg=TEXT_PRI,
                 font=("Helvetica", 11, "bold"),
                 anchor="w").pack(anchor="w")

        self.artist_var = tk.StringVar(value="—")
        tk.Label(info, textvariable=self.artist_var,
                 bg="#181818", fg=TEXT_SEC,
                 font=("Helvetica", 9),
                 anchor="w").pack(anchor="w")

        # Like buton
        self.like_btn = tk.Button(
            left, text="♡",
            bg="#181818", fg=TEXT_DIM,
            font=("Helvetica", 14),
            bd=0, relief="flat", cursor="hand2",
            activebackground="#181818", activeforeground=ACCENT,
            command=self._cb.get("on_like"),
        )
        self.like_btn.pack(side="left", padx=(12, 0))

        # ── CENTER: playback controls ─────────────────────────────────────────
        center = tk.Frame(self, bg="#181818")
        center.grid(row=0, column=1, pady=12)

        btn_cfg = dict(
            bg="#181818", bd=0, relief="flat", cursor="hand2",
            activebackground="#181818",
        )

        tk.Button(center, text="⏮", fg=TEXT_SEC,
                  font=("Helvetica", 16),
                  activeforeground=TEXT_PRI,
                  command=self._cb.get("on_prev"),
                  **btn_cfg).pack(side="left", padx=8)

        self.play_btn = tk.Button(
            center, text="▶",
            bg=TEXT_PRI, fg="#000000",
            font=("Helvetica", 13, "bold"),
            bd=0, relief="flat", cursor="hand2",
            width=3, height=1,
            activebackground="#e0e0e0",
            activeforeground="#000000",
            command=self._cb.get("on_play_pause"),
        )
        self.play_btn.pack(side="left", padx=6)
        self.play_btn.bind("<Enter>", lambda _: self.play_btn.config(bg="#e0e0e0"))
        self.play_btn.bind("<Leave>", lambda _: self.play_btn.config(bg=TEXT_PRI))

        tk.Button(center, text="⏭", fg=TEXT_SEC,
                  font=("Helvetica", 16),
                  activeforeground=TEXT_PRI,
                  command=self._cb.get("on_next"),
                  **btn_cfg).pack(side="left", padx=8)

        # ── RIGHT: volume ─────────────────────────────────────────────────────
        right = tk.Frame(self, bg="#181818")
        right.grid(row=0, column=2, sticky="e", padx=16)

        tk.Label(right, text="🔉", bg="#181818", fg=TEXT_DIM,
                 font=("Helvetica", 11)).pack(side="left")

        self.vol_var = tk.IntVar(value=50)
        ttk.Scale(
            right, from_=0, to=100, orient="horizontal",
            variable=self.vol_var,
            style="Bar.Horizontal.TScale",
            length=100,
            command=self._on_volume_move,
        ).pack(side="left", padx=6)

        tk.Label(right, text="🔊", bg="#181818", fg=TEXT_DIM,
                 font=("Helvetica", 11)).pack(side="left")

        self.vol_pct = tk.Label(right, text="50%",
                                bg="#181818", fg=TEXT_DIM,
                                font=("Helvetica", 9))
        self.vol_pct.pack(side="left", padx=(6, 0))

    # ── Metode publice ────────────────────────────────────────────────────────

    def update_track(self, track: str, artist: str) -> None:
        self.title_var.set(track[:30] + "…" if len(track) > 30 else track)
        self.artist_var.set(artist[:25] + "…" if len(artist) > 25 else artist)

    def update_play_state(self, is_playing: bool) -> None:
        self._is_playing = is_playing
        self.play_btn.config(text="⏸" if is_playing else "▶")

    def update_like(self, liked: bool) -> None:
        self.like_btn.config(
            text="♥" if liked else "♡",
            fg=ACCENT if liked else TEXT_DIM,
        )

    def update_volume(self, volume: int) -> None:
        self.vol_var.set(volume)
        self.vol_pct.config(text=f"{volume}%")

    def update_cover(self, tk_image: ImageTk.PhotoImage) -> None:
        self._cover_tk = tk_image
        self.cover_lbl.config(image=self._cover_tk, width=56, height=56)

    # ── Intern ────────────────────────────────────────────────────────────────

    def _show_placeholder(self) -> None:
        img = make_placeholder_cover((56, 56))
        from PIL import ImageTk as ITk
        self._cover_tk = ITk.PhotoImage(img)
        self.cover_lbl.config(image=self._cover_tk)

    def _on_volume_move(self, val: str) -> None:
        v = int(float(val))
        self.vol_pct.config(text=f"{v}%")
        if self._volume_job:
            self.after_cancel(self._volume_job)
        on_vol = self._cb.get("on_volume_change")
        if on_vol:
            self._volume_job = self.after(2000, lambda: on_vol(v))