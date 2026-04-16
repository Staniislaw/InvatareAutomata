# ── ui/app.py ─────────────────────────────────────────────────────────────────
# Clasa principala SpotifyApp — leaga SpotifyService cu cele doua panouri UI.
# Aici se gestioneaza: thread-urile de refresh, cache-ul de coperte, callbacks.
# ──────────────────────────────────────────────────────────────────────────────

import threading
import tkinter as tk
from PIL import ImageTk

from config import BG_DARK
from spotify_service import SpotifyService
from utils import fetch_image
from ui.player_panel import PlayerPanel
from ui.lists_panel import ListsPanel


class SpotifyApp(tk.Tk):
    """
    Fereastra principala a aplicatiei.
    Rol: orchestreaza SpotifyService, PlayerPanel si ListsPanel.
    """

    def __init__(self, service: SpotifyService):
        super().__init__()
        self.service = service

        self.title("Spotify Controller")
        self.geometry("900x620")
        self.minsize(800, 560)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        # Cache imagini (url -> ImageTk.PhotoImage)
        self._cover_cache: dict[str, ImageTk.PhotoImage] = {}
        self._update_job = None

        self._build_ui()
        self._refresh()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Callbacks trimise catre panouri (evita dependenta circulara)
        player_callbacks = {
            "on_play_pause":    self._action_play_pause,
            "on_next":          self._action_next,
            "on_prev":          self._action_prev,
            "on_like":          self._action_like,
            "on_volume_change": self._action_set_volume,
        }

        lists_callbacks = {
            "on_play_playlist": self._action_play_playlist,
            "on_play_recent":   self._action_play_recent,
        }

        # Panou stanga
        self.player = PlayerPanel(self, player_callbacks)
        self.player.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)

        # Panou dreapta
        self.lists = ListsPanel(self, lists_callbacks)
        self.lists.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

    # ── Actions (callbacks din UI -> SpotifyService pe thread separat) ────────

    def _action_play_pause(self):
        def run():
            try:
                state = self.service.get_current_playback()
                if state and state["is_playing"]:
                    self.service.pause()
                    self.after(0, lambda: self.player.update_play_state(False))
                    self.after(0, lambda: self.player.set_status("⏸ Pauza"))
                else:
                    self.service.play()
                    self.after(0, lambda: self.player.update_play_state(True))
                    self.after(0, lambda: self.player.set_status("▶ Redare"))
                self.after(500, self._refresh)
            except Exception as e:
                self.after(0, lambda: self.player.set_status(f"Eroare: {e}"))
        threading.Thread(target=run, daemon=True).start()

    def _action_next(self):
        def run():
            try:
                self.service.next_track()
                self.after(0, lambda: self.player.set_status("⏭ Melodie urmatoare"))
                self.after(800, self._refresh)
            except Exception as e:
                self.after(0, lambda: self.player.set_status(f"Eroare: {e}"))
        threading.Thread(target=run, daemon=True).start()

    def _action_prev(self):
        def run():
            try:
                self.service.previous_track()
                self.after(0, lambda: self.player.set_status("⏮ Melodie anterioara"))
                self.after(800, self._refresh)
            except Exception as e:
                self.after(0, lambda: self.player.set_status(f"Eroare: {e}"))
        threading.Thread(target=run, daemon=True).start()

    def _action_like(self):
        def run():
            try:
                state = self.service.get_current_playback()
                if state and state.get("item"):
                    tid   = state["item"]["id"]
                    liked = self.service.toggle_like(tid)
                    self.after(0, lambda: self.player.update_like(liked))
                    msg = "❤ Salvat!" if liked else "💔 Eliminat din liked"
                    self.after(0, lambda: self.player.set_status(msg))
            except Exception as e:
                self.after(0, lambda: self.player.set_status(f"Eroare like: {e}"))
        threading.Thread(target=run, daemon=True).start()

    def _action_set_volume(self, volume: int):
        def run():
            try:
                self.service.set_volume(volume)
                self.after(0, lambda: self.player.set_status(f"🔊 Volum: {volume}%"))
            except Exception as e:
                self.after(0, lambda: self.player.set_status(f"Eroare volum: {e}"))
        threading.Thread(target=run, daemon=True).start()

    def _action_play_playlist(self, uri: str):
        def run():
            try:
                self.service.play(context_uri=uri)
                self.after(0, lambda: self.player.set_status("▶ Playlist pornit"))
                self.after(1000, self._refresh)
            except Exception as e:
                self.after(0, lambda: self.player.set_status(f"Eroare: {e}"))
        threading.Thread(target=run, daemon=True).start()

    def _action_play_recent(self, uri: str):
        def run():
            try:
                self.service.play(uris=[uri])
                self.after(0, lambda: self.player.set_status("▶ Pornit"))
                self.after(1000, self._refresh)
            except Exception as e:
                self.after(0, lambda: self.player.set_status(f"Eroare: {e}"))
        threading.Thread(target=run, daemon=True).start()

    # ── Refresh (poll Spotify la fiecare 5s) ──────────────────────────────────

    def _refresh(self):
        threading.Thread(target=self._fetch_all_data, daemon=True).start()
        if self._update_job:
            self.after_cancel(self._update_job)
        self._update_job = self.after(5000, self._refresh)

    def _fetch_all_data(self):
        """Ruleaza pe thread secundar — nu atinge widget-urile direct."""
        try:
            # ── Player snapshot ───────────────────────────────────────────────
            snap = self.service.get_player_snapshot()
            if snap:
                def update_player():
                    self.player.update_track(snap["track"], snap["artist"])
                    self.player.update_play_state(snap["is_playing"])
                    self.player.update_like(snap["liked"])
                    self.player.update_volume(snap["volume"])
                    status = "▶ Redare" if snap["is_playing"] else "⏸ Pauza"
                    self.player.set_status(status)
                self.after(0, update_player)

                # Coperta (cu cache)
                url = snap["cover_url"]
                if url and url not in self._cover_cache:
                    img    = fetch_image(url, (200, 200))
                    tk_img = ImageTk.PhotoImage(img)
                    self._cover_cache[url] = tk_img

                if url and url in self._cover_cache:
                    tk_img = self._cover_cache[url]
                    self.after(0, lambda i=tk_img: self.player.update_cover(i))
            else:
                self.after(0, lambda: self.player.set_status("Spotify nu reda nimic"))

            # ── Playlists ─────────────────────────────────────────────────────
            playlists = self.service.get_user_playlists(limit=30)
            self.after(0, lambda: self.lists.update_playlists(playlists))

            # ── Recent ────────────────────────────────────────────────────────
            recent = self.service.get_recently_played(limit=20)
            self.after(0, lambda: self.lists.update_recent(recent))

        except Exception as e:
            self.after(0, lambda: self.player.set_status(f"Eroare: {str(e)[:40]}"))