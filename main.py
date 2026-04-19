import threading
import cv2
from spotify_service import SpotifyService
from ui.app import SpotifyApp
from gesture.detector import HandDetector
from gesture.recognizer import GestureRecognizer


def start_gesture_loop(service: SpotifyService, use_laptop_cam=False):
    detector   = HandDetector(use_laptop_cam=use_laptop_cam)
    recognizer = GestureRecognizer()

    try:
        detector.connect()
    except ConnectionError as e:
        print(e)
        return

    print("[Gesture] Pornit! Gesturi active: ✌ Play/Pause | 🖐 Sus=Volum+ | 🖐 Jos=Volum-")

    while detector.running:
        frame, result = detector.read_frame()
        if frame is None:
            continue

        frame = detector.draw_landmarks(frame, result)
        data  = recognizer.process(result)

        gesture = data['gesture']

        # Debug — vezi ce detecteaza in terminal
        if data['raw_label']:
            print(f"  {data['raw_label']}  | fingers: {data['fingers']}")

        # ── Play / Pause ──────────────────────────────
        if gesture == "PLAY_PAUSE" and recognizer.can_trigger("PLAY_PAUSE"):
            recognizer.mark_triggered("PLAY_PAUSE")
            print("[Gesture] → PLAY/PAUSE")
            try:
                state = service.get_current_playback()
                if state and state.get("is_playing"):
                    service.pause()
                else:
                    service.play()
            except Exception as e:
                print(f"[Gesture] Eroare: {e}")

        # ── Volum + ───────────────────────────────────
        elif gesture == "VOLUME_UP" and recognizer.can_trigger("VOLUME_UP"):
            recognizer.mark_triggered("VOLUME_UP")
            try:
                state = service.get_current_playback()
                if state and state.get("device"):
                    vol = min(100, state["device"]["volume_percent"] + 10)
                    service.set_volume(vol)
                    print(f"[Gesture] → VOLUM: {vol}%")
            except Exception as e:
                print(f"[Gesture] Eroare volum: {e}")

        # ── Volum - ───────────────────────────────────
        elif gesture == "VOLUME_DOWN" and recognizer.can_trigger("VOLUME_DOWN"):
            recognizer.mark_triggered("VOLUME_DOWN")
            try:
                state = service.get_current_playback()
                if state and state.get("device"):
                    vol = max(0, state["device"]["volume_percent"] - 10)
                    service.set_volume(vol)
                    print(f"[Gesture] → VOLUM: {vol}%")
            except Exception as e:
                print(f"[Gesture] Eroare volum: {e}")

        # Afiseaza fereastra camerei
        if data['raw_label']:
            cv2.putText(frame, data['raw_label'], (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 100), 2, cv2.LINE_AA)

        cv2.imshow("Camera Gesturi", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
            break

    detector.stop()
    cv2.destroyAllWindows()


def main():
    print("[INFO] Conectare la Spotify...")
    service = SpotifyService()
    print("[OK]   Conectat!")

    gesture_thread = threading.Thread(
        target=start_gesture_loop,
        args=(service,),
        kwargs={"use_laptop_cam": True},  # False = telefon
        daemon=True,
    )
    gesture_thread.start()

    print("[OK]   Deschid interfata...")
    app = SpotifyApp(service)
    app.mainloop()


if __name__ == "__main__":
    main()