import cv2 
from cvzone.HandTrackingModule import HandDetector
from time import sleep, time
from pynput.keyboard import Controller

cap = cv2.VideoCapture(0)
cap.set(3, 900)
cap.set(4, 400)

detector = HandDetector(detectionCon=0.8, maxHands=2)


keys = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "Delete"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L", "Enter"],
    ["Z", "X", "C", "V", "B", "N", "M", ".", "CapsLock", "Space"]
]

finalText = ""
caps_lock_on = False
keyboard = Controller()


GOLD = (97, 208, 245)
DARK = (5, 3, 1)
DARK_BOX = (20, 12, 5)
WHITE = (255, 255, 255)
HOVER = (80, 190, 230)
CLICK = (180, 240, 255)

fist_count = 0
both_fists_before = False
last_fist_time = 0

last_key_time = 0
key_delay = 0.5


class Button:
    def __init__(self, pos, text, size=[60, 60]):
        self.pos = pos
        self.size = size
        self.text = text


def drawAll(img, buttonList):
    for button in buttonList:
        x, y = button.pos
        w, h = button.size

        color = GOLD

        if button.text == "CapsLock" and caps_lock_on:
            color = CLICK

        cv2.rectangle(img, (x, y), (x + w, y + h), color, cv2.FILLED)
        cv2.rectangle(img, (x, y), (x + w, y + h), DARK_BOX, 2)

        display_text = "Caps" if button.text == "CapsLock" else button.text

        if display_text in ["Caps", "Delete"]:
            font_scale = 1
            thickness = 2
        elif display_text in ["Space", "Enter"]:
            font_scale = 1.3
            thickness = 2
        else:
            font_scale = 2
            thickness = 2

        text_size = cv2.getTextSize(
            display_text,
            cv2.FONT_HERSHEY_PLAIN,
            font_scale,
            thickness
        )[0]

        text_x = x + (w - text_size[0]) // 2
        text_y = y + (h + text_size[1]) // 2

        cv2.putText(
            img,
            display_text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_PLAIN,
            font_scale,
            DARK,
            thickness
        )

    return img


def draw_gold_hand(img, hand):
    lmList = hand["lmList"]

    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (0, 9), (9, 10), (10, 11), (11, 12),
        (0, 13), (13, 14), (14, 15), (15, 16),
        (0, 17), (17, 18), (18, 19), (19, 20),
        (5, 9), (9, 13), (13, 17)
    ]

    for a, b in connections:
        x1, y1 = lmList[a][0], lmList[a][1]
        x2, y2 = lmList[b][0], lmList[b][1]
        cv2.line(img, (x1, y1), (x2, y2), GOLD, 2)

    for i, lm in enumerate(lmList):
        x, y = lm[0], lm[1]

        if i == 4 or i == 8:
            cv2.circle(img, (x, y), 9, WHITE, cv2.FILLED)
            cv2.circle(img, (x, y), 12, GOLD, 2)
        else:
            cv2.circle(img, (x, y), 5, WHITE, cv2.FILLED)
            cv2.circle(img, (x, y), 7, GOLD, 1)

    if hand["type"] == "Left":
        label = "Right Hand"
    else:
        label = "Left Hand"

    x, y = lmList[0][0], lmList[0][1]

    cv2.putText(
        img,
        label,
        (x - 40, y + 35),
        cv2.FONT_HERSHEY_PLAIN,
        1.5,
        GOLD,
        2
    )


def both_hands_fist(hands):
    if len(hands) < 2:
        return False

    for hand in hands[:2]:
        fingers = detector.fingersUp(hand)

        if sum(fingers) != 0:
            return False

    return True


def check_fist_close(hands):
    global fist_count, both_fists_before, last_fist_time

    now = time()
    both_fists_now = both_hands_fist(hands)

    if both_fists_now and not both_fists_before:
        if now - last_fist_time > 0.6:
            fist_count += 1
            last_fist_time = now

    if not both_fists_now:
        both_fists_before = False
    else:
        both_fists_before = True

    if now - last_fist_time > 3:
        fist_count = 0

    return fist_count >= 2


start_x = 280
start_y = 500

buttonList = []

for i in range(len(keys)):
    for j, key in enumerate(keys[i]):
        pos_x = start_x + 65 * j
        pos_y = start_y + 65 * i
        size = [60, 60]

        if key == "P":
            size = [56, 60]

        elif key == "Delete":
            size = [59, 60]
            pos_x = start_x + 65 * j - 4

        elif key == "Space":
            size = [120, 60]
            pos_x = start_x + 65 * 9
            pos_y = start_y + 65 * 2

        elif key == "Enter":
            size = [120, 60]

        buttonList.append(Button([pos_x, pos_y], key, size))


try:
    while True:
        success, img = cap.read()

        if not success:
            print("Ignoring empty frame")
            continue

        img = cv2.flip(img, 1)

        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (img.shape[1], img.shape[0]), DARK, -1)
        img = cv2.addWeighted(overlay, 0.65, img, 0.35, 0)

        hands, img = detector.findHands(img, draw=False)

        if hands:
            for hand in hands:
                draw_gold_hand(img, hand)

            if check_fist_close(hands):
                break

        img = drawAll(img, buttonList)

        if hands:
            hand = hands[0]
            lmList = hand["lmList"]

            index_finger_tip = lmList[8]
            thumb_tip = lmList[4]

            for button in buttonList:
                x, y = button.pos
                w, h = button.size

                if x < index_finger_tip[0] < x + w and y < index_finger_tip[1] < y + h:
                    cv2.rectangle(
                        img,
                        (x - 3, y - 3),
                        (x + w + 3, y + h + 3),
                        HOVER,
                        cv2.FILLED
                    )
                    cv2.rectangle(
                        img,
                        (x - 3, y - 3),
                        (x + w + 3, y + h + 3),
                        GOLD,
                        2
                    )

                    display_text = "Caps" if button.text == "CapsLock" else button.text

                    if display_text in ["Caps", "Delete"]:
                        font_scale = 1
                        thickness = 2
                    elif display_text in ["Space", "Enter"]:
                        font_scale = 1.3
                        thickness = 2
                    else:
                        font_scale = 2
                        thickness = 2

                    text_size = cv2.getTextSize(
                        display_text,
                        cv2.FONT_HERSHEY_PLAIN,
                        font_scale,
                        thickness
                    )[0]

                    text_x = x + (w - text_size[0]) // 2
                    text_y = y + (h + text_size[1]) // 2

                    cv2.putText(
                        img,
                        display_text,
                        (text_x, text_y),
                        cv2.FONT_HERSHEY_PLAIN,
                        font_scale,
                        WHITE,
                        thickness
                    )

                    dist_result = detector.findDistance(
                    thumb_tip[:2],
                    index_finger_tip[:2],
                    img,
                    color=WHITE,
                    scale=8
                    )

                    if isinstance(dist_result, (tuple, list)):
                        dist = dist_result[0]
                    else:
                        dist = dist_result

                    if dist < 25 and time() - last_key_time > key_delay:
                        last_key_time = time()

                        if button.text == "CapsLock":
                            caps_lock_on = not caps_lock_on
                            sleep(0.2)

                        elif button.text == "Enter":
                            keyboard.press('\n')
                            keyboard.release('\n')
                            finalText += '\n'
                            sleep(0.15)

                        elif button.text == "Space":
                            keyboard.press(' ')
                            keyboard.release(' ')
                            finalText += ' '
                            sleep(0.15)

                        elif button.text == "Delete":
                            keyboard.press('\b')
                            keyboard.release('\b')
                            finalText = finalText[:-1]
                            sleep(0.15)

                        else:
                            key_to_press = button.text.lower()

                            if caps_lock_on:
                                key_to_press = key_to_press.upper()

                            keyboard.press(key_to_press)
                            keyboard.release(key_to_press)

                            finalText += key_to_press
                            sleep(0.15)

                        cv2.rectangle(
                            img,
                            (x, y),
                            (x + w, y + h),
                            CLICK,
                            cv2.FILLED
                        )
                        cv2.rectangle(
                            img,
                            (x, y),
                            (x + w, y + h),
                            GOLD,
                            2
                        )

                        cv2.putText(
                            img,
                            display_text,
                            (text_x, text_y),
                            cv2.FONT_HERSHEY_PLAIN,
                            font_scale,
                            DARK,
                            thickness
                        )

        frame_height, frame_width, _ = img.shape

        cv2.rectangle(
            img,
            (10, 10),
            (frame_width - 10, 60),
            DARK_BOX,
            cv2.FILLED
        )
        cv2.rectangle(
            img,
            (10, 10),
            (frame_width - 10, 60),
            GOLD,
            2
        )

        cv2.putText(
            img,
            finalText,
            (20, 40),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            GOLD,
            2
        )

        cv2.putText(
            img,
            f"Close fists twice to quit: {fist_count}/2",
            (20, frame_height - 5),
            cv2.FONT_HERSHEY_PLAIN,
            1.2,
            GOLD,
            2
        )

        cv2.imshow("Virtual Keyboard", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
