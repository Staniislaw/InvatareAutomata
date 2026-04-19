"""
test_gesturi.py — debug vizual
Ruleaza separat: python test_gesturi.py
Arata pe ecran exact ce detecteaza MediaPipe pentru fiecare deget.
"""

import cv2
import collections
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
import time

MODEL_PATH = "hand_landmarker.task"

options = HandLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
)

cap = cv2.VideoCapture(0)  # 0 = webcam laptop
position_history = collections.deque(maxlen=15)

print("Pornit! Arata diferite gesturi in fata camerei.")
print("Apasa Q pentru iesire.\n")

with HandLandmarker.create_from_options(options) as landmarker:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        h, w  = frame.shape[:2]

        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result   = landmarker.detect_for_video(mp_image, int(time.time() * 1000))

        if result.hand_landmarks:
            lm         = result.hand_landmarks[0]
            handedness = result.handedness[0][0].display_name if result.handedness else "?"

            # Calculeaza starea fiecarui deget
            if handedness == "Right":
                thumb = lm[4].x < lm[3].x
            else:
                thumb = lm[4].x > lm[3].x

            index  = lm[8].y  < lm[6].y
            middle = lm[12].y < lm[10].y
            ring   = lm[16].y < lm[14].y
            pinky  = lm[20].y < lm[18].y

            fingers = [thumb, index, middle, ring, pinky]
            count   = sum(fingers)
            palm_y  = lm[9].y

            # ── Deseneaza punctele ────────────────────
            CONNECTIONS = [
                (0,1),(1,2),(2,3),(3,4),
                (0,5),(5,6),(6,7),(7,8),
                (0,9),(9,10),(10,11),(11,12),
                (0,13),(13,14),(14,15),(15,16),
                (0,17),(17,18),(18,19),(19,20),
                (5,9),(9,13),(13,17),
            ]
            pts = [(int(lm[i].x * w), int(lm[i].y * h)) for i in range(21)]
            for a, b in CONNECTIONS:
                cv2.line(frame, pts[a], pts[b], (0, 180, 255), 2)
            for i, pt in enumerate(pts):
                color = (0, 0, 255) if i in (4,8,12,16,20) else (255,255,255)
                cv2.circle(frame, pt, 6, color, -1)

            # ── Info panel ───────────────────────────
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (320, 220), (10,10,10), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

            def txt(text, y, color=(255,255,255)):
                cv2.putText(frame, text, (10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)

            txt(f"Mana: {handedness}", 25)
            txt(f"Degete ridicate: {count}", 50)
            txt(f"Palm Y: {palm_y:.2f}  (0=sus 1=jos)", 75)
            txt(f"Thumb:  {'UP' if thumb  else 'down'}", 105, (0,255,100) if thumb  else (100,100,100))
            txt(f"Index:  {'UP' if index  else 'down'}", 125, (0,255,100) if index  else (100,100,100))
            txt(f"Middle: {'UP' if middle else 'down'}", 145, (0,255,100) if middle else (100,100,100))
            txt(f"Ring:   {'UP' if ring   else 'down'}", 165, (0,255,100) if ring   else (100,100,100))
            txt(f"Pinky:  {'UP' if pinky  else 'down'}", 185, (0,255,100) if pinky  else (100,100,100))

            # ── Swipe detection ──────────────────────
            palm_x_norm = lm[9].x
            position_history.append((palm_x_norm, palm_y, time.time()))

            swipe = ""
            if len(position_history) >= 6:
                oldest  = position_history[0]
                newest  = position_history[-1]
                dt      = newest[2] - oldest[2]
                dx      = newest[0] - oldest[0]
                if dt > 0.001:
                    velocity = dx / dt
                    dist     = abs(dx)
                    # Arata valorile in terminal
                    print(f"dx={dx:.2f} velocity={velocity:.1f} dist={dist:.2f}")
                    if dist > 0.15 and velocity > 1.5:
                        swipe = "SWIPE DREAPTA → NEXT"
                        position_history.clear()
                    elif dist > 0.15 and velocity < -1.5:
                        swipe = "SWIPE STANGA ← PREV"
                        position_history.clear()

            if swipe:
                cv2.putText(frame, swipe, (w//2 - 150, h//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,255), 3, cv2.LINE_AA)

            # ── Gest detectat ─────────────────────────
            gest = ""
            color_gest = (0, 255, 100)

            if not thumb and index and middle and not ring and not pinky:
                gest = "✌ PLAY/PAUSE"
            elif count >= 4 and palm_y < 0.4:
                gest = "VOLUM +"
            elif count >= 4 and palm_y > 0.6:
                gest = "VOLUM -"
            elif count >= 4:
                gest = f"Palma (muta sus/jos) y={palm_y:.2f}"
                color_gest = (0, 200, 255)
            else:
                gest = f"({count} degete - nerecunoscut)"
                color_gest = (100, 100, 100)

            cv2.putText(frame, gest, (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_gest, 2, cv2.LINE_AA)

        else:
            cv2.putText(frame, "Nu vad nicio mana...", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.imshow("TEST GESTURI", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
            break

cap.release()
cv2.destroyAllWindows()