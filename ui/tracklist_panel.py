# ── ui/tracklist_panel.py ─────────────────────────────────────────────────────
# Panoul din dreapta: afiseaza piesele din playlist-ul selectat.
# Click pe piesa => porneste redarea prin callback on_play_track.
# ──────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from config import BG_DARK, ACCENT, TEXT_PRI, TEXT_SEC, TEXT_DIM


def _ms_to_min(ms: int) -> str:
    """Converteste milisecunde in format mm:ss."""
    total_sec = ms // 1000
    return f"{total_sec // 60}:{total_sec % 60:02d}"


class TracklistPanel(tk.Frame):
    """
    Panou dreapta cu lista de piese din playlist-ul activ.
      - Header cu numele playlist-ului
      - Coloana: #  Titlu  Artist  Durata
      - Click pe rand => callback on_play_track(track_dict)
      - Randul curent redat e evidentiat cu verde
    """

    def __init__(self, parent, callbacks: dict, **kwargs):
        super().__init__(parent, bg="#121212", **kwargs)
        self._cb = callbacks
        self._tracks: list[dict] = []
        self._current_uri: str = ""
        self._row_frames: list[tk.Frame] = []
        self._build()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        self._header_var = tk.StringVar(value="Selecteaza un playlist")
        header = tk.Frame(self, bg="#121212")
        header.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(
            header,
            textvariable=self._header_var,
            bg="#121212", fg=TEXT_PRI,
            font=("Helvetica", 16, "bold"),
            anchor="w",
        ).pack(side="left")

        # Separator
        tk.Frame(self, bg="#282828", height=1).pack(fill="x", padx=20)

        # Coloana headere
        col_frame = tk.Frame(self, bg="#121212")
        col_frame.pack(fill="x", padx=20, pady=(4, 2))
        tk.Label(col_frame, text="#",      bg="#121212", fg=TEXT_DIM, font=("Helvetica", 10), width=3,  anchor="w").pack(side="left")
        tk.Label(col_frame, text="TITLU",  bg="#121212", fg=TEXT_DIM, font=("Helvetica", 10), width=30, anchor="w").pack(side="left", padx=(4, 0))
        tk.Label(col_frame, text="ARTIST", bg="#121212", fg=TEXT_DIM, font=("Helvetica", 10), width=20, anchor="w").pack(side="left", padx=(4, 0))
        tk.Label(col_frame, text="DURATA", bg="#121212", fg=TEXT_DIM, font=("Helvetica", 10), width=8,  anchor="e").pack(side="right", padx=(0, 4))

        tk.Frame(self, bg="#282828", height=1).pack(fill="x", padx=20)

        # Lista scrollabila
        container = tk.Frame(self, bg="#121212")
        container.pack(fill="both", expand=True, padx=4)

        self._canvas = tk.Canvas(container, bg="#121212", bd=0,
                                 highlightthickness=0, relief="flat")
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=self._canvas.yview,
                                 bg="#121212", troughcolor="#121212",
                                 width=4, bd=0, relief="flat")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._list_frame = tk.Frame(self._canvas, bg="#121212")
        self._win_id = self._canvas.create_window(
            (0, 0), window=self._list_frame, anchor="nw"
        )

        self._list_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(self._win_id, width=e.width)
        )
        self._canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        )

    # ── API public ────────────────────────────────────────────────────────────

    def load_tracks(self, playlist_name: str, tracks: list[dict]) -> None:
        """
        tracks: [{"name": str, "artist": str, "uri": str, "duration_ms": int}, ...]
        """
        self._tracks = tracks
        self._header_var.set(playlist_name)

        for w in self._list_frame.winfo_children():
            w.destroy()
        self._row_frames.clear()

        if not tracks:
            tk.Label(
                self._list_frame,
                text="Playlist gol.",
                bg="#121212", fg=TEXT_DIM,
                font=("Helvetica", 11),
            ).pack(pady=20)
            return

        for i, track in enumerate(tracks):
            self._add_row(i, track)

    def set_current_track(self, uri: str) -> None:
        """Evidentiaza randul corespunzator URI-ului curent redat."""
        old_uri = self._current_uri
        self._current_uri = uri

        for i, track in enumerate(self._tracks):
            if i >= len(self._row_frames):
                break
            row = self._row_frames[i]
            if track["uri"] == uri:
                self._set_row_color(row, "#1a1a2e", ACCENT)
            elif track["uri"] == old_uri:
                self._set_row_color(row, "#121212", TEXT_PRI)

    # ── Intern ────────────────────────────────────────────────────────────────

    def _add_row(self, idx: int, track: dict):
        row = tk.Frame(self._list_frame, bg="#121212", cursor="hand2")
        row.pack(fill="x", padx=16, pady=1)
        self._row_frames.append(row)

        num_lbl = tk.Label(row, text=str(idx + 1),
                           bg="#121212", fg=TEXT_DIM,
                           font=("Helvetica", 10), width=3, anchor="w")
        num_lbl.pack(side="left")

        name_lbl = tk.Label(row,
                            text=(track["name"][:35] + "…") if len(track["name"]) > 35 else track["name"],
                            bg="#121212", fg=TEXT_PRI,
                            font=("Helvetica", 11), width=30, anchor="w")
        name_lbl.pack(side="left", padx=(4, 0))

        artist_lbl = tk.Label(row,
                              text=(track["artist"][:22] + "…") if len(track["artist"]) > 22 else track["artist"],
                              bg="#121212", fg=TEXT_SEC,
                              font=("Helvetica", 10), width=20, anchor="w")
        artist_lbl.pack(side="left", padx=(4, 0))

        dur_lbl = tk.Label(row,
                           text=_ms_to_min(track.get("duration_ms", 0)),
                           bg="#121212", fg=TEXT_DIM,
                           font=("Helvetica", 10), width=8, anchor="e")
        dur_lbl.pack(side="right", padx=(0, 4))

        widgets = [row, num_lbl, name_lbl, artist_lbl, dur_lbl]
        for w in widgets:
            w.bind("<Enter>", lambda e, r=row: self._on_enter(r))
            w.bind("<Leave>", lambda e, r=row, i=idx: self._on_leave(r, i))
            w.bind("<Button-1>", lambda e, i=idx: self._on_click(i))

    def _on_enter(self, row: tk.Frame):
        self._set_row_color(row, "#1a1a1a", TEXT_PRI)

    def _on_leave(self, row: tk.Frame, idx: int):
        if idx < len(self._tracks) and self._tracks[idx]["uri"] == self._current_uri:
            self._set_row_color(row, "#1a1a2e", ACCENT)
        else:
            self._set_row_color(row, "#121212", TEXT_PRI)

    def _on_click(self, idx: int):
        track = self._tracks[idx]
        self.set_current_track(track["uri"])
        cb = self._cb.get("on_play_track")
        if cb:
            cb(track)

    def _set_row_color(self, row: tk.Frame, bg: str, fg_main: str):
        row.config(bg=bg)
        children = row.winfo_children()
        for i, w in enumerate(children):
            try:
                w.config(bg=bg)
                # Primul label = numar (dim), al doilea = titlu (fg_main), rest secundar
                if i == 1:
                    w.config(fg=fg_main)
            except tk.TclError:
                pass