import spotipy
from spotipy.oauth2 import SpotifyOAuth

# ── Pune credentialele tale aici ──────────────────────
SPOTIFY_CLIENT_ID     = "c8aada1c5ab34175af092fd21d39f1e7"
SPOTIFY_CLIENT_SECRET = "10e80cdce1e143e3b284ca22698ded94"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"
# ─────────────────────────────────────────────────────

def conectare():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="user-modify-playback-state user-read-playback-state user-library-modify user-library-read"
    ))
    return sp

def melodie_curenta(sp):
    state = sp.current_playback()
    if state and state.get('item'):
        track  = state['item']['name']
        artist = state['item']['artists'][0]['name']
        status = "▶ Redare" if state['is_playing'] else "⏸ Pauza"
        print(f"\n{status}: {artist} — {track}")
    else:
        print("\n(Spotify nu redă nimic momentan)")

def play_pause(sp):
    state = sp.current_playback()
    if state and state['is_playing']:
        sp.pause_playback()
        print("⏸  Pauza")
    else:
        sp.start_playback()
        print("▶  Redare")

def like_melodie(sp):
    state = sp.current_playback()
    if state and state.get('item'):
        track_id = state['item']['id']
        track    = state['item']['name']
        artist   = state['item']['artists'][0]['name']
        sp.current_user_saved_tracks_add([track_id])
        print(f"❤  Salvat: {artist} — {track}")
    else:
        print("(Nicio melodie în redare)")

def urmatoarea(sp):
    sp.next_track()
    print("⏭  Melodie următoare")

def anterioara(sp):
    sp.previous_track()
    print("⏮  Melodie anterioară")

def meniu():
    print("\n" + "═"*35)
    print("  SPOTIFY MINI CONTROLLER")
    print("═"*35)
    print("  1 — Melodia curentă")
    print("  2 — Play / Pause")
    print("  3 — Melodie următoare")
    print("  4 — Melodie anterioară")
    print("  5 — Like melodie ❤")
    print("  0 — Ieșire")
    print("═"*35)

if __name__ == "__main__":
    print("[INFO] Conectare la Spotify...")
    sp = conectare()
    print("[OK] Conectat!\n")

    while True:
        meniu()
        optiune = input("  Alege opțiunea: ").strip()

        if optiune == "1":
            melodie_curenta(sp)
        elif optiune == "2":
            play_pause(sp)
        elif optiune == "3":
            urmatoarea(sp)
        elif optiune == "4":
            anterioara(sp)
        elif optiune == "5":
            like_melodie(sp)
        elif optiune == "0":
            print("\nLa revedere!")
            break
        else:
            print("Opțiune invalidă.")