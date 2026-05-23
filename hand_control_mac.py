import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import mediapipe as mp
import pyautogui
import math
import time
from _thread import start_new_thread


GOLD = (97, 208, 245)
WHITE = (255, 255, 255)
DARK = (5, 3, 1)


class Mouse:
    def __init__(self):
        pass

    def distance(self, x1, y1, x2, y2):
        return math.sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))

    def leftClick(self, distance_thumb_index):
        if distance_thumb_index <= 40:
            pyautogui.click()

    def rightClick(self, distance_index_middle):
        if distance_index_middle <= 40:
            pyautogui.click(button="right")

    def moveCursor(self, x, y):
        pyautogui.moveTo(x, y)

cap = cv2.VideoCapture(0)

mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1)

ms = Mouse()

screen_w, screen_h = pyautogui.size()

fist_count = 0
fist_was_down = False
last_fist_time = 0

connections = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17)
]

def is_fist(handLms):

    finger_tips = [8, 12, 16, 20]

    for tip in finger_tips:
        if handLms.landmark[tip].y < handLms.landmark[tip - 2].y:
            return False

    return True

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(frame, 1)

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (0, 0),
        (frame.shape[1], frame.shape[0]),
        DARK,
        -1
    )

    frame = cv2.addWeighted(
        overlay,
        0.65,
        frame,
        0.35,
        0
    )

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)

    finger_pos = {
        4: None,
        8: None,
        12: None
    }

    should_close = False

    if results.multi_hand_landmarks:

        for handLms in results.multi_hand_landmarks:

            h, w, _ = frame.shape

            for a, b in connections:

                x1 = int(handLms.landmark[a].x * w)
                y1 = int(handLms.landmark[a].y * h)

                x2 = int(handLms.landmark[b].x * w)
                y2 = int(handLms.landmark[b].y * h)

                cv2.line(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    GOLD,
                    2
                )


            for id, lm in enumerate(handLms.landmark):

                cx = int(lm.x * w)
                cy = int(lm.y * h)

                if id in finger_pos:

                    screen_x = cx * screen_w / w
                    screen_y = cy * screen_h / h

                    
                    wrist_x = handLms.landmark[0].x
                    thumb_x = handLms.landmark[4].x

                    if thumb_x < wrist_x:
                        screen_x -= 400
                        screen_y -= 100

                    else:
                        screen_x += 30
                        screen_y -= 100

                    screen_x = max(0, min(screen_w, screen_x))
                    screen_y = max(0, min(screen_h, screen_y))

                    finger_pos[id] = (
                        screen_x,
                        screen_y
                    )

                if id == 4 or id == 8 or id == 12:

                    cv2.circle(
                        frame,
                        (cx, cy),
                        10,
                        WHITE,
                        cv2.FILLED
                    )

                    cv2.circle(
                        frame,
                        (cx, cy),
                        13,
                        GOLD,
                        2
                    )

                else:

                    cv2.circle(
                        frame,
                        (cx, cy),
                        5,
                        WHITE,
                        cv2.FILLED
                    )

                    cv2.circle(
                        frame,
                        (cx, cy),
                        7,
                        GOLD,
                        1
                    )


            current_fist = is_fist(handLms)

            now = time.time()

            if current_fist and not fist_was_down:

                if now - last_fist_time > 0.5:
                    fist_count += 1
                    last_fist_time = now

            if not current_fist:
                fist_was_down = False
            else:
                fist_was_down = True

            if now - last_fist_time > 3:
                fist_count = 0

            if fist_count >= 2:
                should_close = True


            try:

                if all(finger_pos.values()) and not should_close and not current_fist:

                    start_new_thread(
                        ms.moveCursor,
                        finger_pos[8]
                    )

                    thumb_index_dist = ms.distance(
                        *finger_pos[4],
                        *finger_pos[8]
                    )

                    index_middle_dist = ms.distance(
                        *finger_pos[4],
                        *finger_pos[12]
                    )

                    start_new_thread(
                        ms.leftClick,
                        (thumb_index_dist,)
                    )

                    start_new_thread(
                        ms.rightClick,
                        (index_middle_dist,)
                    )

            except:
                pass
    

    cv2.putText(
        frame,
        f"Fist twice to quit: {fist_count}/2",
        (15, frame.shape[0] - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        GOLD,
        2
    )

    cv2.imshow("Hand Mouse", frame)

    if should_close:
        break

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
