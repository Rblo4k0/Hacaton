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
            myHand = self.results.multi_hand_landmarks[handNo]

            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])

        return self.lmList

    def recognize_gesture(self):
        if not self.lmList:
            return "unknown"

        fingers = []

        # Большой палец
        if self.lmList[4][1] > self.lmList[3][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Остальные пальцы
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]

        for tip, pip in zip(tips, pips):
            if self.lmList[tip][2] < self.lmList[pip][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        if fingers == [0, 0, 0, 0, 0]:
            return "rock"

        if fingers[1:] == [1, 1, 1, 1]:
            return "paper"

        if fingers == [0, 1, 1, 0, 0]:
            return "scissors"

        return "unknown"