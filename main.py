 
from spotify_service import SpotifyService
from ui.app import SpotifyApp
 
 
def main():
    print("[INFO] Conectare la Spotify...")
    service = SpotifyService()
    print("[OK]   Conectat! Deschid interfata...")
    app = SpotifyApp(service)
    app.mainloop()
 
 
if __name__ == "__main__":
    main()
 