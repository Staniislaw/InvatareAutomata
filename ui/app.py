# ── ui/app.py ─────────────────────────────────────────────────────────────────
# Layout nou — identic cu Spotify:
#   [Sidebar stanga] [Tracklist dreapta]
#   [Bottom bar fixa jos]
# ──────────────────────────────────────────────────────────────────────────────

import threading
import time
import tkinter as tk
from PIL import ImageTk

from config import BG_DARK, ACCENT, TEXT_DIM, TEXT_PRI
from spotify_service import SpotifyService
from utils import fetch_image
from ui.sidebar_panel import SidebarPanel
from ui.tracklist_panel import TracklistPanel
from ui.bottom_bar import BottomBar


class SpotifyApp(tk.Tk):
    """
    Fereastra principala — layout Spotify:
        Stanga:  SidebarPanel  (playlist-uri cu cover)
        Dreapta: TracklistPanel (piesele din playlist-ul selectat)
        Jos:     BottomBar      (player fix)
    """

    def __init__(self, service: SpotifyService):
        super().__init__()
        self.service = service
        self._last_user_action = 0
        self.title("Spotify Controller")
        self.geometry("1100x700")
        self.minsize(900, 580)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        self._cover_cache: dict[str, ImageTk.PhotoImage] = {}
        self._pl_cover_cache: dict[str, ImageTk.PhotoImage] = {}
        self._update_job = None

        self._build_ui()
        self._refresh()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top bar ───────────────────────────────────────────────────────────
        topbar = tk.Frame(self, bg="#000000", height=40)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="♫  Spotify Controller",
                 bg="#000000", fg=TEXT_PRI,
                 font=("Helvetica", 12, "bold")).pack(side="left", padx=16, pady=8)

        self._status_var = tk.StringVar(value="Se conectează...")
        tk.Label(topbar, textvariable=self._status_var,
                 bg="#000000", fg=TEXT_DIM,
                 font=("Helvetica", 9)).pack(side="right", padx=16)

        tk.Frame(self, bg="#282828", height=1).pack(fill="x")

        # ── Bottom bar (pack INAINTE de main ca sa fie jos fix) ───────────────
        tk.Frame(self, bg="#282828", height=1).pack(fill="x", side="bottom")

        player_callbacks = {
            "on_play_pause":    self._action_play_pause,
            "on_next":          self._action_next,
            "on_prev":          self._action_prev,
            "on_like":          self._action_like,
            "on_volume_change": self._action_set_volume,
        }
        self.bottom = BottomBar(self, player_callbacks)
        self.bottom.pack(fill="x", side="bottom")

        # ── Main area ─────────────────────────────────────────────────────────
        main = tk.Frame(self, bg=BG_DARK)
        main.pack(fill="both", expand=True)

        # Sidebar stanga
        sidebar_callbacks = {
            "on_select_playlist": self._on_playlist_selected,
        }
        self.sidebar = SidebarPanel(main, sidebar_callbacks, width=280)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Frame(main, bg="#282828", width=1).pack(side="left", fill="y")

        # Tracklist dreapta
        tracklist_callbacks = {
            "on_play_track": self._action_play_track,
        }
        self.tracklist = TracklistPanel(main, tracklist_callbacks)
        self.tracklist.pack(side="left", fill="both", expand=True)

    # ── Playlist selectat ─────────────────────────────────────────────────────

    def _on_playlist_selected(self, playlist: dict):
        self.tracklist.load_tracks(playlist["name"] + " ⏳", [])
        threading.Thread(
            target=self._fetch_playlist_tracks,
            args=(playlist,),
            daemon=True,
        ).start()

    def _fetch_playlist_tracks(self, playlist: dict):
        try:
            tracks = self.service.get_playlist_tracks(playlist["uri"])
            self.after(0, lambda: self.tracklist.load_tracks(playlist["name"], tracks))
        except Exception as e:
            self.after(0, lambda: self.tracklist.show_error(str(e)[:60]))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _action_play_pause(self):
        def run():
            try:
                self._last_user_action = time.time()
                state = self.service.get_current_playback()

                # device_id direct, ca in test
                devices = self.service.sp.devices()["devices"]
                if not devices:
                    self._set_status("Niciun device activ")
                    return
                device_id = devices[0]["id"]

                if state and state.get("is_playing"):
                    self.service.sp.pause_playback(device_id=device_id)
                    self.bottom.update_play_state(False)
                    self._set_status("⏸ Pauză")
                else:
                    self.service.sp.start_playback(device_id=device_id)
                    self.bottom.update_play_state(True)
                    self._set_status("▶ Redare")

                self.after(1000, self._refresh)

            except Exception as e:
                self._set_status(f"Eroare: {e}")
                print(e)

        threading.Thread(target=run, daemon=True).start()

    def _action_next(self):
        def run():
            try:
                self.service.next_track()
                self._set_status("⏭  Urmatoarea")
                self.after(800, self._refresh)
            except Exception as e:
                self._set_status(f"Eroare: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _action_prev(self):
        def run():
            try:
                self.service.previous_track()
                self._set_status("⏮  Anterioara")
                self.after(800, self._refresh)
            except Exception as e:
                self._set_status(f"Eroare: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _action_like(self):
        def run():
            try:
                state = self.service.get_current_playback()
                if state and state.get("item"):
                    tid = state["item"]["id"]
                    liked = self.service.toggle_like(tid)
                    self.after(0, lambda: self.bottom.update_like(liked))
                    self._set_status("❤  Salvat!" if liked else "💔  Eliminat")
            except Exception as e:
                self._set_status(f"Eroare like: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _action_set_volume(self, volume: int):
        def run():
            try:
                self.service.set_volume(volume)
                self._set_status(f"🔊  Volum: {volume}%")
            except Exception as e:
                self._set_status(f"Eroare volum: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _action_play_track(self, track: dict):
        def run():
            try:
                self._last_user_action = time.time()

                devices = self.service.sp.devices()
                if devices["devices"]:
                    device_id = devices["devices"][0]["id"]
                    self.service.sp.transfer_playback(device_id, force_play=False)

                state = self.service.get_current_playback()

                # dacă e aceeași piesă → resume
                if state and state.get("item") and state["item"]["uri"] == track["uri"]:
                    self.service.sp.start_playback()
                else:
                    self.service.play(uris=[track["uri"]])

                self.bottom.update_play_state(True)
                self._set_status("▶ Redare")

                self.after(1000, self._refresh)

            except Exception as e:
                print(e)

        threading.Thread(target=run, daemon=True).start()
    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg: str):
        self.after(0, lambda: self._status_var.set(msg))

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh(self):
        threading.Thread(target=self._fetch_all_data, daemon=True).start()
        if self._update_job:
            self.after_cancel(self._update_job)
        self._update_job = self.after(5000, self._refresh)

    def _fetch_all_data(self):
        if time.time() - self._last_user_action < 2:
            return
        try:
            # Player snapshot
            snap = self.service.get_player_snapshot()
            if snap:
                def upd():
                    self.bottom.update_track(snap["track"], snap["artist"])
                    self.bottom.update_play_state(snap["is_playing"])
                    self.bottom.update_like(snap["liked"])
                    self.bottom.update_volume(snap["volume"])
                    self._set_status("▶  Redare" if snap["is_playing"] else "⏸  Pauza")
                self.after(0, upd)

                url = snap["cover_url"]
                if url and url not in self._cover_cache:
                    img = fetch_image(url, (56, 56))
                    tk_img = ImageTk.PhotoImage(img)
                    self._cover_cache[url] = tk_img
                if url and url in self._cover_cache:
                    tk_img = self._cover_cache[url]
                    self.after(0, lambda i=tk_img: self.bottom.update_cover(i))
            else:
                self._set_status("Spotify nu reda nimic")

            # Playlists cu cover_url
            playlists = self.service.get_user_playlists(limit=50)
            self.after(0, lambda: self.sidebar.update_playlists(playlists))

            # Cover-uri playlist in background
            for pl in playlists:
                uri = pl.get("uri", "")
                url = pl.get("cover_url", "")
                if url and uri and uri not in self._pl_cover_cache:
                    threading.Thread(
                        target=self._load_pl_cover,
                        args=(uri, url),
                        daemon=True,
                    ).start()

        except Exception as e:
            self._set_status(f"Eroare: {str(e)[:40]}")

    def _load_pl_cover(self, uri: str, url: str):
        try:
            img = fetch_image(url, (48, 48))
            tk_img = ImageTk.PhotoImage(img)
            self._pl_cover_cache[uri] = tk_img
            self.after(0, lambda: self.sidebar.set_cover(uri, tk_img))
        except Exception:
            pass