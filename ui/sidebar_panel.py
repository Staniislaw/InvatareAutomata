# ── ui/sidebar_panel.py ───────────────────────────────────────────────────────
# Sidebar stanga: lista playlist-uri cu cover art (ca "Your Library" Spotify).
# Click pe playlist => incarca piesele in TracklistPanel din dreapta.
# ──────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from PIL import Image, ImageTk
from io import BytesIO

from config import BG_DARK, BG_CARD, BG_HOVER, BG_ACTIVE, ACCENT, TEXT_PRI, TEXT_SEC, TEXT_DIM, BORDER


class SidebarPanel(tk.Frame):
    """
    Sidebar stanga cu:
      - Header "Your Library"
      - Lista de playlist-uri: [cover 48x48] [Nume playlist] [subtitlu]
      - Click => callback on_select_playlist(playlist_dict)
    """

    def __init__(self, parent, callbacks: dict, **kwargs):
        super().__init__(parent, bg="#121212", **kwargs)
        self._cb = callbacks
        self._playlists: list[dict] = []
        self._cover_cache: dict[str, ImageTk.PhotoImage] = {}
        self._selected_idx = -1
        self._row_frames: list[tk.Frame] = []

        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)

        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#121212")
        header.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(header, text="⊞", bg="#121212", fg=TEXT_SEC,
                 font=("Helvetica", 14)).pack(side="left")
        tk.Label(header, text="  Your Library", bg="#121212", fg=TEXT_PRI,
                 font=("Helvetica", 13, "bold")).pack(side="left")

        # ── Scrollable list ───────────────────────────────────────────────────
        container = tk.Frame(self, bg="#121212")
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="#121212", bd=0,
                           highlightthickness=0, relief="flat")
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=canvas.yview,
                                 bg="#121212", troughcolor="#121212",
                                 width=4, bd=0, relief="flat")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._list_frame = tk.Frame(canvas, bg="#121212")
        self._canvas_window = canvas.create_window(
            (0, 0), window=self._list_frame, anchor="nw"
        )

        def on_frame_configure(_e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self._list_frame.bind("<Configure>", on_frame_configure)

        def on_canvas_configure(e):
            canvas.itemconfig(self._canvas_window, width=e.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # Mouse wheel scroll
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # ── Metode publice ────────────────────────────────────────────────────────

    def update_playlists(self, playlists: list[dict]) -> None:
        """
        playlists: [{"name": str, "uri": str, "cover_url": str | None, "owner": str}, ...]
        """
        self._playlists = playlists
        self._selected_idx = -1

        # Sterge randurile vechi
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._row_frames.clear()

        for i, pl in enumerate(playlists):
            self._add_row(i, pl)

    def set_cover(self, uri: str, img: ImageTk.PhotoImage) -> None:
        """Seteaza cover-ul pentru un playlist dupa uri."""
        self._cover_cache[uri] = img
        # Gaseste randul si actualizeaza
        for i, pl in enumerate(self._playlists):
            if pl["uri"] == uri and i < len(self._row_frames):
                row = self._row_frames[i]
                cover_lbl = row.winfo_children()[0] if row.winfo_children() else None
                if cover_lbl and isinstance(cover_lbl, tk.Label):
                    cover_lbl.config(image=img)
                break

    # ── Intern ────────────────────────────────────────────────────────────────

    def _add_row(self, idx: int, pl: dict):
        row = tk.Frame(self._list_frame, bg="#121212", cursor="hand2")
        row.pack(fill="x", pady=1)
        self._row_frames.append(row)

        # Cover placeholder 48x48
        ph = self._make_placeholder(pl.get("name", "?"))
        cover_lbl = tk.Label(row, image=ph, bg="#121212",
                             width=48, height=48)
        cover_lbl.image = ph  # referinta
        cover_lbl.pack(side="left", padx=(8, 10), pady=4)

        # Daca avem cover din cache
        uri = pl.get("uri", "")
        if uri in self._cover_cache:
            cover_lbl.config(image=self._cover_cache[uri])

        # Text
        text_frame = tk.Frame(row, bg="#121212")
        text_frame.pack(side="left", fill="x", expand=True)

        name_lbl = tk.Label(text_frame,
                            text=pl["name"][:30],
                            bg="#121212", fg=TEXT_PRI,
                            font=("Helvetica", 11),
                            anchor="w")
        name_lbl.pack(anchor="w")

        owner = pl.get("owner", "Playlist")
        sub_lbl = tk.Label(text_frame,
                           text=f"Playlist · {owner[:20]}",
                           bg="#121212", fg=TEXT_DIM,
                           font=("Helvetica", 9),
                           anchor="w")
        sub_lbl.pack(anchor="w")

        # Hover + click
        widgets = [row, cover_lbl, text_frame, name_lbl, sub_lbl]
        for w in widgets:
            w.bind("<Enter>", lambda e, r=row, i=idx: self._on_enter(r, i))
            w.bind("<Leave>", lambda e, r=row, i=idx: self._on_leave(r, i))
            w.bind("<Button-1>", lambda e, i=idx: self._on_click(i))

    def _on_enter(self, row: tk.Frame, idx: int):
        if idx != self._selected_idx:
            for w in row.winfo_children():
                self._set_bg_recursive(w, "#1a1a1a")
            row.config(bg="#1a1a1a")

    def _on_leave(self, row: tk.Frame, idx: int):
        if idx != self._selected_idx:
            for w in row.winfo_children():
                self._set_bg_recursive(w, "#121212")
            row.config(bg="#121212")

    def _on_click(self, idx: int):
        # Deselect previous
        if 0 <= self._selected_idx < len(self._row_frames):
            old = self._row_frames[self._selected_idx]
            self._set_bg_recursive(old, "#121212")
            old.config(bg="#121212")
            # Reset text color
            for child in old.winfo_children():
                if isinstance(child, tk.Frame):
                    for lbl in child.winfo_children():
                        if isinstance(lbl, tk.Label):
                            lbl.config(fg=TEXT_PRI if lbl.cget("font") and "bold" not in str(lbl.cget("font")) else TEXT_PRI)

        self._selected_idx = idx

        # Highlight selected
        row = self._row_frames[idx]
        self._set_bg_recursive(row, "#1a1a1a")
        row.config(bg="#1a1a1a")

        # Verde pe numele selectat
        for child in row.winfo_children():
            if isinstance(child, tk.Frame):
                labels = child.winfo_children()
                if labels:
                    labels[0].config(fg=ACCENT)  # Numele = verde

        pl = self._playlists[idx]
        cb = self._cb.get("on_select_playlist")
        if cb:
            cb(pl)

    def _set_bg_recursive(self, widget, color: str):
        try:
            widget.config(bg=color)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_bg_recursive(child, color)

    def _make_placeholder(self, name: str) -> ImageTk.PhotoImage:
        """Cover placeholder colorat cu initiala."""
        colors = ["#1DB954", "#E91429", "#509BF5", "#FF6437",
                  "#B49BC8", "#F037A5", "#90D2D8", "#FFFF00"]
        color = colors[hash(name) % len(colors)]
        img = Image.new("RGB", (48, 48), color=color)
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        letter = name[0].upper() if name else "?"
        # Center letter
        bbox = draw.textbbox((0, 0), letter, font=None)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((48 - w) // 2, (48 - h) // 2 - 2), letter,
                  fill="white")
        return ImageTk.PhotoImage(img)