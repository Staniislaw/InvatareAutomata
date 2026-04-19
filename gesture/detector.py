"""
gesture/detector.py
Responsabil DOAR pentru conectarea la camera si detectarea mainii.
Returneaza landmark-urile brute catre recognizer.
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
import time
import os

# ── Configurare sursa video ───────────────────────────────
# Schimba PHONE_IP cu IP-ul tau din IP Webcam
PHONE_IP   = "192.168.43.1"
PHONE_PORT = 8080
PHONE_URL  = f"http://{PHONE_IP}:{PHONE_PORT}/video"

# Backdrop pentru webcam laptop
LAPTOP_WEBCAM_INDEX = 0

MODEL_PATH = "hand_landmarker.task"
MODEL_URL  = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"


def _download_model():
    if not os.path.exists(MODEL_PATH):
        import urllib.request
        print(f"[Gesture] Descarc modelul MediaPipe...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[Gesture] Model descarcat!")


class HandDetector:
    """
    Detecteaza mainile din stream video (telefon sau laptop).
    Foloseste MediaPipe HandLandmarker (API 0.10.30+).
    """

    def __init__(self, use_laptop_cam=False):
        """
        Args:
            use_laptop_cam: True = webcam laptop | False = IP Webcam telefon
        """
        _download_model()

        self.use_laptop_cam = use_laptop_cam
        self.running = False
        self.cap = None
        self.landmarker = None

        # Ultimul rezultat detectat
        self.last_result = None
        self.last_frame  = None

        self._setup_mediapipe()

    def _setup_mediapipe(self):
        options = HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.65,
            min_hand_presence_confidence=0.65,
            min_tracking_confidence=0.55,
        )
        self.landmarker = HandLandmarker.create_from_options(options)
        print("[Gesture] MediaPipe HandLandmarker initializat!")

    def connect(self):
        """Conecteaza la sursa video."""
        if self.use_laptop_cam:
            print(f"[Gesture] Conectare webcam laptop (index {LAPTOP_WEBCAM_INDEX})...")
            self.cap = cv2.VideoCapture(LAPTOP_WEBCAM_INDEX)
        else:
            print(f"[Gesture] Conectare IP Webcam: {PHONE_URL}")
            self.cap = cv2.VideoCapture(PHONE_URL)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.cap.isOpened():
            raise ConnectionError(
                f"[Gesture] Nu s-a putut conecta la "
                f"{'webcam laptop' if self.use_laptop_cam else PHONE_URL}"
            )

        self.running = True
        print("[Gesture] Conectat!")

    def read_frame(self):
        """
        Citeste un frame si ruleaza detectia MediaPipe.
        Returneaza: (frame_bgr, result) sau (None, None) la eroare.
        """
        if not self.cap or not self.running:
            return None, None

        # Goleste buffer-ul — citeste ultimul frame disponibil (evita freeze)
        for _ in range(2):
            self.cap.grab()

        ret, frame = self.cap.read()
        if not ret:
            return None, None

        frame = cv2.flip(frame, 1)

        # Converteste pentru MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(time.time() * 1000)

        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        self.last_result = result
        self.last_frame  = frame

        return frame, result

    def draw_landmarks(self, frame, result):
        """Deseneaza scheletul mainii pe frame."""
        if not result or not result.hand_landmarks:
            return frame

        h, w = frame.shape[:2]
        CONNECTIONS = [
            (0,1),(1,2),(2,3),(3,4),
            (0,5),(5,6),(6,7),(7,8),
            (0,9),(9,10),(10,11),(11,12),
            (0,13),(13,14),(14,15),(15,16),
            (0,17),(17,18),(18,19),(19,20),
            (5,9),(9,13),(13,17),
        ]

        for hand_lm in result.hand_landmarks:
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lm]

            # Conexiuni
            for a, b in CONNECTIONS:
                cv2.line(frame, pts[a], pts[b], (0, 180, 255), 2)

            # Puncte
            for i, pt in enumerate(pts):
                color = (50, 50, 255) if i in (4,8,12,16,20) else (255,255,255)
                cv2.circle(frame, pt, 5, color, -1)
                cv2.circle(frame, pt, 5, (20,20,20), 1)

        return frame

    def get_hand_count(self, result):
        if result and result.hand_landmarks:
            return len(result.hand_landmarks)
        return 0

    def stop(self):
        """Opreste camera si elibereaza resursele."""
        self.running = False
        if self.cap:
            self.cap.release()
        if self.landmarker:
            self.landmarker.close()
        print("[Gesture] Detector oprit.")