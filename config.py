# ── config.py ─────────────────────────────────────────────────────────────────
# Credentiale Spotify + constante de tema
# ──────────────────────────────────────────────────────────────────────────────

# Credentiale OAuth
SPOTIFY_CLIENT_ID     = "c8aada1c5ab34175af092fd21d39f1e7"
SPOTIFY_CLIENT_SECRET = "10e80cdce1e143e3b284ca22698ded94"
SPOTIFY_REDIRECT_URI  = "http://127.0.0.1:8888/callback"

SPOTIFY_SCOPES = (
    "user-read-playback-state "
    "user-modify-playback-state "   # ← asta e critica pentru pause/play
    "user-read-currently-playing "
    "user-library-read "
    "user-library-modify "
    "user-read-recently-played "
    "playlist-read-private"
)


# Culori tema dark
BG_DARK    = "#0a0a0a"
BG_CARD    = "#141414"
BG_HOVER   = "#1e1e1e"
BG_ACTIVE  = "#282828"
ACCENT     = "#1DB954"        # Verde Spotify
ACCENT_DIM = "#158a3e"
TEXT_PRI   = "#ffffff"
TEXT_SEC   = "#b3b3b3"
TEXT_DIM   = "#535353"
BORDER     = "#2a2a2a"