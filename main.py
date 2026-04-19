import threading
import cv2
from spotify_service import SpotifyService
from ui.app import SpotifyApp
from gesture.detector import HandDetector
from gesture.recognizer import GestureRecognizer
from gesture.cursor import VirtualCursor


def start_gesture_loop(service: SpotifyService, app: SpotifyApp, use_laptop_cam=False):
    detector = HandDetector(use_laptop_cam=use_laptop_cam)
    recognizer = GestureRecognizer()

    try:
        detector.connect()
    except ConnectionError as e:
        print(e)
        return

    print("[Gesture] Pornit!")

    local_volume = 50

    # ── Cache playback ────────────────────────────────
    _cached_state = None
    _last_fetch_time = 0
    FETCH_INTERVAL = 5.0  # apelează API max o dată la 5 secunde

    def get_state():
        nonlocal _cached_state, _last_fetch_time
        if time.time() - _last_fetch_time > FETCH_INTERVAL:
            try:
                _cached_state = service.get_current_playback()
                _last_fetch_time = time.time()
            except Exception as e:
                print(f"[Gesture] Eroare fetch: {e}")
        return _cached_state

    # ─────────────────────────────────────────────────

    while detector.running:
        frame, result = detector.read_frame()
        if frame is None:
            continue

        frame = detector.draw_landmarks(frame, result)
        data = recognizer.process(result)
        gesture = data['gesture']

        if result and result.hand_landmarks:
            hand_lm = result.hand_landmarks[0]
            fingers = data['fingers']
            if len(fingers) == 5:
                thumb, index, middle, ring, pinky = fingers

                only_index = not thumb and index and not middle and not ring and not pinky
                pinch_mid = thumb and not index and middle and not ring and not pinky

                if only_index or pinch_mid:
                    fx = hand_lm[8].x if only_index else hand_lm[12].x
                    fy = hand_lm[8].y if only_index else hand_lm[12].y
                    tx = hand_lm[4].x
                    ty = hand_lm[4].y
                    frame = app.cursor.update(fx, fy, tx, ty, frame=frame)
                else:
                    app.after(0, app.cursor.hide)

        if data['raw_label']:
            cv2.putText(frame, data['raw_label'], (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 100), 2, cv2.LINE_AA)

        if gesture and recognizer.can_trigger(gesture):
            recognizer.mark_triggered(gesture)

            if gesture == "LIKE":
                print("[Gesture] → LIKE ❤")
                try:
                    state = get_state()  # ← cache, nu apel direct
                    if state and state.get("item"):
                        service.toggle_like(state["item"]["id"])
                        _last_fetch_time = 0  # forteaza refresh dupa actiune
                except Exception as e:
                    print(f"[Gesture] Eroare: {e}")

            elif gesture == "PLAY_PAUSE":
                print("[Gesture] → PLAY/PAUSE")
                try:
                    state = get_state()  # ← cache, nu apel direct
                    if state and state.get("is_playing"):
                        service.pause()
                    else:
                        service.play()
                    _last_fetch_time = 0  # forteaza refresh dupa actiune
                except Exception as e:
                    print(f"[Gesture] Eroare: {e}")

            elif gesture == "SWIPE_RIGHT":
                print("[Gesture] → NEXT SONG")
                try:
                    service.next_track()
                    _last_fetch_time = 0
                except Exception as e:
                    print(f"[Gesture] Eroare: {e}")

            elif gesture == "SWIPE_LEFT":
                print("[Gesture] → PREV SONG")
                try:
                    service.previous_track()
                    _last_fetch_time = 0
                except Exception as e:
                    print(f"[Gesture] Eroare: {e}")

            elif gesture == "VOLUME_UP":
                try:
                    local_volume = min(100, local_volume + 10)
                    service.set_volume(local_volume)
                    print(f"[Gesture] → VOLUM: {local_volume}%")
                except Exception as e:
                    print(f"[Gesture] Eroare: {e}")

            elif gesture == "VOLUME_DOWN":
                try:
                    local_volume = max(0, local_volume - 10)
                    service.set_volume(local_volume)
                    print(f"[Gesture] → VOLUM: {local_volume}%")
                except Exception as e:
                    print(f"[Gesture] Eroare: {e}")

        cv2.imshow("Camera Gesturi", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
            break

    detector.stop()
    cv2.destroyAllWindows()


def main():
    print("[INFO] Conectare la Spotify...")
    service = SpotifyService()
    print("[OK]   Conectat!")

    print("[OK]   Deschid interfata...")
    app = SpotifyApp(service)

    # Cursor virtual — deseneaza pe camera, click pe UI
    app.cursor = VirtualCursor(app)

    gesture_thread = threading.Thread(
        target=start_gesture_loop,
        args=(service, app),
        kwargs={"use_laptop_cam": True},
        daemon=True,
    )
    gesture_thread.start()

    app.mainloop()


if __name__ == "__main__":
    main()