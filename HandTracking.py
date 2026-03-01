import cv2
import mediapipe as mp


class HandDetector:
    def __init__(self,
                 mode=False,
                 maxHands=1,
                 detectionCon=0.7,
                 trackCon=0.7):

        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )

        self.mpDraw = mp.solutions.drawing_utils
        self.results = None
        self.lmList = []

    def find_hands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(
                        img,
                        handLms,
                        self.mpHands.HAND_CONNECTIONS
                    )
        return img

    def find_position(self, img, handNo=0):
        self.lmList = []

        if self.results and self.results.multi_hand_landmarks:
            if handNo < len(self.results.multi_hand_landmarks):
                myHand = self.results.multi_hand_landmarks[handNo]
                for id, lm in enumerate(myHand.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    self.lmList.append([id, cx, cy])

        return self.lmList

    def _get_fingers(self):
        """
        Возвращает список [большой, указ., средний, безымян., мизинец]
        1 = разогнут, 0 = согнут.
        """
        if not self.lmList:
            return None

        fingers = []

        # Большой палец: сравниваем по X (зеркально для правой руки)
        if self.lmList[4][1] > self.lmList[3][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Остальные 4 пальца: кончик выше PIP-сустава → разогнут
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        for tip, pip in zip(tips, pips):
            fingers.append(1 if self.lmList[tip][2] < self.lmList[pip][2] else 0)

        return fingers

    def recognize_gesture(self):
        """
        Возвращает:
          'neutral'  — ☝️ один указательный (нейтральное/базовое положение)
          'rock'     — ✊ кулак
          'scissors' — ✌️ указательный + средний
          'paper'    — 🖐️ все пальцы
          'unknown'  — что-то непонятное

        Нейтральный жест (☝️) распознаётся в том числе из любого положения.
        """
        fingers = self._get_fingers()
        if fingers is None:
            return "unknown"

        thumb, idx, mid, ring, pinky = fingers

        # Нейтральный жест: только указательный поднят (☝️)
        # Большой палец и остальные — сжаты (не учитываем большой)
        if idx == 1 and mid == 0 and ring == 0 and pinky == 0:
            return "neutral"

        # Камень (✊): все 4 пальца (без большого) сжаты
        if idx == 0 and mid == 0 and ring == 0 and pinky == 0:
            return "rock"

        # Ножницы (✌️): указательный + средний подняты, безымянный и мизинец сжаты
        if idx == 1 and mid == 1 and ring == 0 and pinky == 0:
            return "scissors"

        # Бумага (🖐️): все 4 пальца (без большого) подняты
        if idx == 1 and mid == 1 and ring == 1 and pinky == 1:
            return "paper"

        # Доп. распознавание: бумага с большим пальцем (все 5)
        if thumb == 1 and idx == 1 and mid == 1 and ring == 1 and pinky == 1:
            return "paper"

        return "unknown"

    def is_neutral(self):
        """Возвращает True, если текущий жест — нейтральный (☝️)."""
        return self.recognize_gesture() == "neutral"
