# ── ui/lists_panel.py ─────────────────────────────────────────────────────────
# Panoul din dreapta: lista playlist-uri + lista melodii recent ascultate.
# Fiecare lista e un Listbox cu scrollbar si hover effect.
# ──────────────────────────────────────────────────────────────────────────────

import tkinter as tk

from config import (
    BG_DARK, BG_CARD, BG_ACTIVE,
    TEXT_PRI, TEXT_SEC, BORDER,
)


class ListsPanel(tk.Frame):
    """
    Panou dreapta cu doua coloane:
        - Playlist-urile utilizatorului (dublu-click => porneste playback)
        - Melodiile recent ascultate  (dublu-click => porneste melodia)

    Callbacks:
        on_play_playlist(uri: str)
        on_play_recent(uri: str)
    """

    def __init__(self, parent, callbacks: dict, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self._cb = callbacks

        self._playlist_uris: list[str] = []
        self._recent_uris:   list[str] = []

        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Playlist-uri ──────────────────────────────────────────────────────
        tk.Label(self, text="PLAYLIST-URI", bg=BG_DARK, fg="#535353",
                 font=("Helvetica", 9, "bold")).grid(
                     row=0, column=0, sticky="w", padx=4, pady=(0, 6))

        pl_frame = tk.Frame(self, bg=BG_CARD,
                            highlightbackground=BORDER, highlightthickness=1)
        pl_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        self.pl_list = self._make_listbox(pl_frame)
        self.pl_list.bind("<Double-Button-1>", self._on_playlist_double_click)

        # ── Melodii recente ───────────────────────────────────────────────────
        tk.Label(self, text="RECENT ASCULTATE", bg=BG_DARK, fg="#535353",
                 font=("Helvetica", 9, "bold")).grid(
                     row=0, column=1, sticky="w", padx=4, pady=(0, 6))

        rec_frame = tk.Frame(self, bg=BG_CARD,
                             highlightbackground=BORDER, highlightthickness=1)
        rec_frame.grid(row=1, column=1, sticky="nsew")

        self.rec_list = self._make_listbox(rec_frame)
        self.rec_list.bind("<Double-Button-1>", self._on_recent_double_click)

    # ── Metode publice ────────────────────────────────────────────────────────

    def update_playlists(self, playlists: list[dict]) -> None:
        """
        Primeste lista din SpotifyService: [{"name": ..., "uri": ...}, ...]
        """
        self.pl_list.delete(0, tk.END)
        self._playlist_uris = []
        for p in playlists:
            self.pl_list.insert(tk.END, f"  {p['name']}")
            self._playlist_uris.append(p["uri"])

    def update_recent(self, tracks: list[dict]) -> None:
        """
        Primeste lista din SpotifyService: [{"name": ..., "artist": ..., "uri": ...}, ...]
        """
        self.rec_list.delete(0, tk.END)
        self._recent_uris = []
        for t in tracks:
            label = f"  {t['artist']} — {t['name']}"
            self.rec_list.insert(tk.END, label[:50])
            self._recent_uris.append(t["uri"])

    # ── Intern ────────────────────────────────────────────────────────────────

    def _make_listbox(self, parent: tk.Frame) -> tk.Listbox:
        """Creeaza un Listbox cu scrollbar si hover effect."""
        lb = tk.Listbox(
            parent,
            bg=BG_CARD, fg=TEXT_SEC,
            selectbackground=BG_ACTIVE, selectforeground=TEXT_PRI,
            font=("Helvetica", 11),
            bd=0, highlightthickness=0,
            activestyle="none",
            cursor="hand2",
        )
        scroll = tk.Scrollbar(parent, orient="vertical", command=lb.yview,
                              bg=BG_CARD, troughcolor=BG_CARD, width=6, bd=0)
        lb.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        lb.pack(fill="both", expand=True, padx=4, pady=4)

        # Hover: schimba culoarea textului cand mouse-ul e deasupra listei
        lb.bind("<Enter>", lambda _: lb.config(fg=TEXT_PRI))
        lb.bind("<Leave>", lambda _: lb.config(fg=TEXT_SEC))

        return lb

    def _on_playlist_double_click(self, _event) -> None:
        sel = self.pl_list.curselection()
        if sel and sel[0] < len(self._playlist_uris):
            uri = self._playlist_uris[sel[0]]
            cb = self._cb.get("on_play_playlist")
            if cb:
                cb(uri)

    def _on_recent_double_click(self, _event) -> None:
        sel = self.rec_list.curselection()
        if sel and sel[0] < len(self._recent_uris):
            uri = self._recent_uris[sel[0]]
            cb = self._cb.get("on_play_recent")
            if cb:
                cb(uri)