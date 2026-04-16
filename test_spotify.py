import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
client_id=SPOTIFY_CLIENT_ID,
client_secret=SPOTIFY_CLIENT_SECRET,
redirect_uri="http://127.0.0.1:8888/callback",
scope="user-modify-playback-state user-read-playback-state user-read-email",
cache_path=r"D:\ProjectD.spotify_cache"
))


def get_current_track():
    try:
        state = sp.currently_playing()

        if state is None:
            print("Nu rulează nimic acum.")
            return

        item = state.get("item")
        if not item:
            print("Nu există track activ.")
            return

        track_name = item.get("name")
        artists = ", ".join([artist["name"] for artist in item.get("artists", [])])
        devices = sp.devices()
        print(devices)
        print("Track:", track_name)
        print("Artist:", artists)

    except Exception as e:
        print("Eroare:", e)


if __name__ == "__main__":
    get_current_track()
