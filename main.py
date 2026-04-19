import threading
from spotify_service import SpotifyService
from ui.app import SpotifyApp
from gesture.detector import HandDetector
from gesture.recognizer import GestureRecognizer
import cv2


def start_gesture_loop(service: SpotifyService, use_laptop_cam=False):
    """
    Ruleaza camera + MediaPipe intr-un thread separat.
    Nu atinge UI-ul — apeleaza direct service-ul Spotify.
    """
    detector   = HandDetector(use_laptop_cam=use_laptop_cam)
    recognizer = GestureRecognizer()

    try:
        detector.connect()
    except ConnectionError as e:
        print(e)
        return

    print("[Gesture] Loop pornit! Apasa Q in fereastra camerei pentru stop.")

    while detector.running:
        frame, result = detector.read_frame()
        if frame is None:
            continue

        # Deseneaza scheletul mainii
        frame = detector.draw_landmarks(frame, result)

        # Recunoaste gestul
        data = recognizer.process(result)
        gesture = data['gesture']

        # Afiseaza label pe ecran
        if data['raw_label']:
            cv2.putText(frame, data['raw_label'], (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 100), 2, cv2.LINE_AA)

        # ── Actioneaza pe baza gestului ──────────────
        if gesture and recognizer.can_trigger(gesture):
            recognizer.mark_triggered(gesture)

            if gesture == "PLAY_PAUSE":
                print("[Gesture] → Play/Pause")
                try:
                    state = service.get_current_playback()
                    if state and state.get("is_playing"):
                        service.pause()
                    else:
                        service.play()
                except Exception as e:
                    print(f"[Gesture] Eroare play/pause: {e}")

            elif gesture == "NEXT" or gesture == "SWIPE_LEFT":
                print("[Gesture] → Next track")
                try:
                    service.next_track()
                except Exception as e:
                    print(f"[Gesture] Eroare next: {e}")

            elif gesture == "PREV" or gesture == "SWIPE_RIGHT":
                print("[Gesture] → Prev track")
                try:
                    service.previous_track()
                except Exception as e:
                    print(f"[Gesture] Eroare prev: {e}")

            elif gesture == "LIKE":
                print("[Gesture] → Like")
                try:
                    state = service.get_current_playback()
                    if state and state.get("item"):
                        service.toggle_like(state["item"]["id"])
                except Exception as e:
                    print(f"[Gesture] Eroare like: {e}")

            elif gesture == "VOLUME_UP":
                try:
                    state = service.get_current_playback()
                    if state and state.get("device"):
                        vol = min(100, state["device"]["volume_percent"] + 8)
                        service.set_volume(vol)
                        print(f"[Gesture] → Volum: {vol}%")
                except Exception as e:
                    print(f"[Gesture] Eroare volum: {e}")

            elif gesture == "VOLUME_DOWN":
                try:
                    state = service.get_current_playback()
                    if state and state.get("device"):
                        vol = max(0, state["device"]["volume_percent"] - 8)
                        service.set_volume(vol)
                        print(f"[Gesture] → Volum: {vol}%")
                except Exception as e:
                    print(f"[Gesture] Eroare volum: {e}")

        # Afiseaza fereastra camerei
        cv2.imshow("Camera Gesturi", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
            break

    detector.stop()
    cv2.destroyAllWindows()


def main():
    print("[INFO] Conectare la Spotify...")
    service = SpotifyService()
    print("[OK]   Conectat!")

    # ── Porneste camera intr-un thread separat ────────────────────────────────
    # use_laptop_cam=False → IP Webcam telefon
    # use_laptop_cam=True  → webcam laptop (backdoor)
    gesture_thread = threading.Thread(
        target=start_gesture_loop,
        args=(service,),
        kwargs={"use_laptop_cam": True},
        daemon=True,
    )
    gesture_thread.start()

    # ── Deschide UI ───────────────────────────────────────────────────────────
    print("[OK]   Deschid interfata...")
    app = SpotifyApp(service)
    app.mainloop()


if __name__ == "__main__":
    main()