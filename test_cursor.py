"""
test_cursor.py — pagina de test pentru cursorul virtual
Ruleaza: python test_cursor.py
Arata butoane colorate pe care poti da click cu degetul.
"""

import tkinter as tk
import threading
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
import time
from gesture.cursor import VirtualCursor

MODEL_PATH = "hand_landmarker.task"

# ── UI Test ───────────────────────────────────────────────────────────────────

class TestApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Test Cursor Virtual")
        self.geometry("800x600")
        self.configure(bg="#121212")
        self.resizable(False, False)

        self._build()
        self.cursor = VirtualCursor(self)

    def _build(self):
        # Titlu
        tk.Label(self, text="🖱  Test Cursor Virtual",
                 bg="#121212", fg="#ffffff",
                 font=("Helvetica", 20, "bold")).pack(pady=(30, 10))

        tk.Label(self, text="Arata degetul aratator = cursor  |  Apropie degetul mare = click",
                 bg="#121212", fg="#b3b3b3",
                 font=("Helvetica", 11)).pack(pady=(0, 30))

        # Log clicks
        self._log_var = tk.StringVar(value="Asteapta click...")
        tk.Label(self, textvariable=self._log_var,
                 bg="#121212", fg="#1DB954",
                 font=("Helvetica", 13, "bold")).pack(pady=(0, 30))

        # Grid de butoane
        grid = tk.Frame(self, bg="#121212")
        grid.pack()

        buttons = [
            ("▶  Play",      "#1DB954", 0, 0),
            ("⏸  Pause",     "#E91429", 0, 1),
            ("⏭  Next",      "#509BF5", 0, 2),
            ("⏮  Prev",      "#FF6437", 1, 0),
            ("❤  Like",      "#F037A5", 1, 1),
            ("🔊  Volum +",  "#90D2D8", 1, 2),
            ("🔇  Volum -",  "#B49BC8", 2, 0),
            ("🎵  Playlist", "#FFFF00", 2, 1),
            ("⚙  Settings",  "#ffffff", 2, 2),
        ]

        for text, color, row, col in buttons:
            btn = tk.Button(
                grid,
                text=text,
                bg="#1e1e1e",
                fg=color,
                font=("Helvetica", 14, "bold"),
                width=14, height=3,
                bd=0, relief="flat",
                cursor="hand2",
                activebackground="#282828",
                activeforeground=color,
                command=lambda t=text, c=color: self._on_click(t, c)
            )
            btn.grid(row=row, column=col, padx=10, pady=10)

            # Hover effect
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg="#282828"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#1e1e1e"))

    def _on_click(self, text, color):
        self._log_var.set(f"✅ Click pe: {text}")
        print(f"[Test] Click detectat: {text}")


# ── Gesture Loop ──────────────────────────────────────────────────────────────

def gesture_loop(app: TestApp):
    options = HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[EROARE] Nu s-a putut deschide camera!")
        return

    print("[OK] Camera pornita! Arata degetul aratator spre camera.")

    with HandLandmarker.create_from_options(options) as landmarker:
        while True:
            # Goleste buffer
            for _ in range(2):
                cap.grab()

            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            h, w  = frame.shape[:2]

            rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result   = landmarker.detect_for_video(mp_image, int(time.time() * 1000))

            if result and result.hand_landmarks:
                lm         = result.hand_landmarks[0]
                handedness = result.handedness[0][0].display_name if result.handedness else "Right"

                # Starea degetelor
                if handedness == "Right":
                    thumb = lm[4].x < lm[3].x
                else:
                    thumb = lm[4].x > lm[3].x

                index  = lm[8].y  < lm[6].y
                middle = lm[12].y < lm[10].y
                ring   = lm[16].y < lm[14].y
                pinky  = lm[20].y < lm[18].y

                only_index = not thumb and index and not middle and not ring and not pinky
                pinch_mid = thumb and not index and middle and not ring and not pinky

                if only_index or pinch_mid:
                    fx = lm[8].x if only_index else lm[12].x
                    fy = lm[8].y if only_index else lm[12].y
                    tx = lm[4].x
                    ty = lm[4].y
                    frame = app.cursor.update(fx, fy, tx, ty, frame=frame)
                else:
                    app.after(0, app.cursor.hide)

                # Deseneaza schelet
                CONNECTIONS = [
                    (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
                    (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),
                    (0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17),
                ]
                pts = [(int(lm[i].x*w), int(lm[i].y*h)) for i in range(21)]
                for a, b in CONNECTIONS:
                    cv2.line(frame, pts[a], pts[b], (0,180,255), 1)
                for i, pt in enumerate(pts):
                    cv2.circle(frame, pt, 4,
                               (0,0,255) if i in (4,8,12,16,20) else (255,255,255), -1)

                # Label
                status = "CLICK (middle+thumb)" if pinch_mid else "cursor (middle)" if only_middle else ""
                if status:
                    cv2.putText(frame, status, (10, 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,100), 2)
            else:
                app.after(0, app.cursor.hide)
                cv2.putText(frame, "Nu vad mana...", (10, 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

            cv2.imshow("Camera - Test Cursor", frame)
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break

    cap.release()
    cv2.destroyAllWindows()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = TestApp()

    t = threading.Thread(target=gesture_loop, args=(app,), daemon=True)
    t.start()

    app.mainloop()