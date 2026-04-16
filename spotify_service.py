# ── spotify_service.py ────────────────────────────────────────────────────────
# Toate apelurile catre Spotify Web API prin biblioteca spotipy.
# Aceasta clasa NU atinge UI-ul — returneaza date brute sau ridica exceptii.
# ──────────────────────────────────────────────────────────────────────────────

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPES,
)


class SpotifyService:
    """Wrapper peste spotipy — singura clasa care vorbeste cu Spotify API."""

    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=SPOTIFY_SCOPES,
        ))

    # ── Playback ──────────────────────────────────────────────────────────────

    def get_current_playback(self) -> dict | None:
        """Returneaza starea curenta a redarii (sau None daca nimic nu ruleaza)."""
        return self.sp.current_playback()

    def play(self, context_uri: str = None, uris: list = None) -> None:
        """Porneste redarea. Optional: context_uri (playlist/album) sau lista de uris."""
        self.sp.start_playback(context_uri=context_uri, uris=uris)

    def pause(self) -> None:
        """Pune redarea pe pauza."""
        self.sp.pause_playback()

    def next_track(self) -> None:
        """Sare la melodia urmatoare."""
        self.sp.next_track()

    def previous_track(self) -> None:
        """Se intoarce la melodia anterioara."""
        self.sp.previous_track()

    def set_volume(self, volume_percent: int) -> None:
        """Seteaza volumul intre 0 si 100."""
        self.sp.volume(volume_percent)

    # ── Like / Saved Tracks ───────────────────────────────────────────────────

    def is_track_saved(self, track_id: str) -> bool:
        """Verifica daca o melodie e in biblioteca utilizatorului."""
        result = self.sp.current_user_saved_tracks_contains([track_id])
        return result[0] if result else False

    def save_track(self, track_id: str) -> None:
        """Adauga o melodie in biblioteca (like)."""
        self.sp.current_user_saved_tracks_add([track_id])

    def remove_track(self, track_id: str) -> None:
        """Sterge o melodie din biblioteca (unlike)."""
        self.sp.current_user_saved_tracks_delete([track_id])

    def toggle_like(self, track_id: str) -> bool:
        """
        Toggle like pentru o melodie.
        Returneaza True daca a fost salvata, False daca a fost stearsa.
        """
        if self.is_track_saved(track_id):
            self.remove_track(track_id)
            return False
        else:
            self.save_track(track_id)
            return True

    # ── Playlists ─────────────────────────────────────────────────────────────

    def get_user_playlists(self, limit: int = 30) -> list[dict]:
        """
        Returneaza lista de playlist-uri ale utilizatorului.
        Fiecare dict contine: name, uri.
        """
        raw = self.sp.current_user_playlists(limit=limit)
        return [
            {"name": p["name"], "uri": p["uri"]}
            for p in raw["items"]
            if p
        ]

    # ── Recent Tracks ─────────────────────────────────────────────────────────

    def get_recently_played(self, limit: int = 20) -> list[dict]:
        """
        Returneaza melodiile recent ascultate (fara duplicate).
        Fiecare dict contine: name, artist, uri.
        """
        raw = self.sp.current_user_recently_played(limit=limit)
        seen = set()
        tracks = []
        for item in raw["items"]:
            t = item["track"]
            if t["id"] not in seen:
                seen.add(t["id"])
                tracks.append({
                    "name":   t["name"],
                    "artist": t["artists"][0]["name"],
                    "uri":    t["uri"],
                })
        return tracks

    # ── Snapshot complet (folosit de refresh) ─────────────────────────────────

    def get_player_snapshot(self) -> dict | None:
        """
        Returneaza un dict cu toate datele necesare pentru a actualiza UI-ul:
        track, artist, cover_url, is_playing, volume, track_id, liked.
        Returneaza None daca nu se reda nimic.
        """
        state = self.get_current_playback()
        if not state or not state.get("item"):
            return None

        track_id  = state["item"]["id"]
        images    = state["item"]["album"]["images"]
        cover_url = images[0]["url"] if images else None

        return {
            "track":      state["item"]["name"],
            "artist":     state["item"]["artists"][0]["name"],
            "cover_url":  cover_url,
            "is_playing": state["is_playing"],
            "volume":     state["device"]["volume_percent"] if state.get("device") else 50,
            "track_id":   track_id,
            "liked":      self.is_track_saved(track_id),
        }