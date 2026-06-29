import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np
from collections import deque


GOLD = (97, 208, 245)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK = (5, 3, 1)


mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True
)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
LEFT_IRIS = [474, 475, 476, 477]

BLINK_THRESHOLD = 0.16
blink_cooldown = 0.3

last_blink_time = {
    "left": 0,
    "right": 0
}

both_eyes_closed_start = None
close_app_time = 3.5

screen_w, screen_h = pyautogui.size()

pyautogui.FAILSAFE = False

smooth_window = 5

gaze_history_x = deque(maxlen=smooth_window)
gaze_history_y = deque(maxlen=smooth_window)

calib_min_x = None
calib_max_x = None
calib_min_y = None
calib_max_y = None


def eye_aspect_ratio(landmarks, eye_points, img_w, img_h):

    coords = [
        (
            int(landmarks[p].x * img_w),
            int(landmarks[p].y * img_h)
        )
        for p in eye_points
    ]

    v1 = np.linalg.norm(np.array(coords[1]) - np.array(coords[5]))
    v2 = np.linalg.norm(np.array(coords[2]) - np.array(coords[4]))
    h = np.linalg.norm(np.array(coords[0]) - np.array(coords[3]))

    return (v1 + v2) / (2.0 * h)

def iris_position(landmarks, iris_points, img_w, img_h):

    iris_coords = [
        (
            int(landmarks[p].x * img_w),
            int(landmarks[p].y * img_h)
        )
        for p in iris_points
    ]

    iris_center = np.mean(iris_coords, axis=0)

    return iris_center


def draw_calibration_target(img, point, countdown):

    radius = 30

    cv2.circle(
        img,
        point,
        radius,
        BLACK,
        cv2.FILLED
    )

    cv2.circle(
        img,
        point,
        radius,
        GOLD,
        3
    )

    cv2.putText(
        img,
        f"Look here: {countdown:.1f}s",
        (point[0] - 80, point[1] - 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        GOLD,
        2
    )


def calibrate_eye(cap):

    global calib_min_x
    global calib_max_x
    global calib_min_y
    global calib_max_y

    calibration_points = [
        (screen_w // 2, screen_h // 2),
        (50, 50),
        (screen_w - 50, 50),
        (50, screen_h - 50),
        (screen_w - 50, screen_h - 50),
        (screen_w // 2, 50),
        (screen_w // 2, screen_h - 50),
        (50, screen_h // 2),
        (screen_w - 50, screen_h // 2)
    ]

    all_x = []
    all_y = []

    wait_time = 2.5

    print("Calibration starting...")

    for point in calibration_points:

        start_time = time.time()

        while True:

            ret, frame = cap.read()

            if not ret:
                continue

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

            img_h, img_w = frame.shape[:2]

            results = face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:

                mesh_points = results.multi_face_landmarks[0].landmark

                iris_center = iris_position(
                    mesh_points,
                    LEFT_IRIS,
                    img_w,
                    img_h
                )

                all_x.append(iris_center[0])
                all_y.append(iris_center[1])

            elapsed = time.time() - start_time
            remaining = max(0, wait_time - elapsed)

            draw_calibration_target(
                frame,
                point,
                remaining
            )

            cv2.imshow("Calibration", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                return

            if elapsed > wait_time:
                break

    calib_min_x = min(all_x)
    calib_max_x = max(all_x)

    calib_min_y = min(all_y)
    calib_max_y = max(all_y)

    print("Calibration complete!")

    cv2.destroyWindow("Calibration")



def map_gaze_to_screen(rel_x, rel_y):

    norm_x = (
        (rel_x - calib_min_x)
        /
        (calib_max_x - calib_min_x)
    )

    norm_y = (
        (rel_y - calib_min_y)
        /
        (calib_max_y - calib_min_y)
    )

    norm_x = max(0, min(1, norm_x))
    norm_y = max(0, min(1, norm_y))

    return (
        int(norm_x * screen_w),
        int(norm_y * screen_h)
    )

# ========================
# Start Camera
# ========================

cap = cv2.VideoCapture(0)

calibrate_eye(cap)

app_start_time = time.time()

# ========================
# Main Loop
# ========================

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

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    img_h, img_w = frame.shape[:2]

    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:

        mesh_points = results.multi_face_landmarks[0].landmark

        left_ear = eye_aspect_ratio(
            mesh_points,
            LEFT_EYE,
            img_w,
            img_h
        )

        right_ear = eye_aspect_ratio(
            mesh_points,
            RIGHT_EYE,
            img_w,
            img_h
        )



        for p in LEFT_EYE + RIGHT_EYE:

            x = int(mesh_points[p].x * img_w)
            y = int(mesh_points[p].y * img_h)

            cv2.circle(
                frame,
                (x, y),
                2,
                GOLD,
                -1
            )

        # ========================
        # Iris Tracking
        # ========================

        iris_center = iris_position(
            mesh_points,
            LEFT_IRIS,
            img_w,
            img_h
        )

        mouse_x, mouse_y = map_gaze_to_screen(
            iris_center[0],
            iris_center[1]
        )

        gaze_history_x.append(mouse_x)
        gaze_history_y.append(mouse_y)

        smooth_x = int(np.mean(gaze_history_x))
        smooth_y = int(np.mean(gaze_history_y))

        pyautogui.moveTo(
            smooth_x,
            smooth_y,
            duration=0
        )



        left_closed = left_ear < BLINK_THRESHOLD
        right_closed = right_ear < BLINK_THRESHOLD


        if (
            left_closed
            and right_closed
            and time.time() - app_start_time > 5
        ):

            if both_eyes_closed_start is None:
                both_eyes_closed_start = time.time()

            closed_time = (
                time.time()
                - both_eyes_closed_start
            )

            cv2.putText(
                frame,
                f"Closing in: {max(0, close_app_time - closed_time):.1f}s",
                (30, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                GOLD,
                2
            )

            if closed_time >= close_app_time:
                break

        else:
            both_eyes_closed_start = None



        if left_closed and not right_closed:

            if (
                time.time()
                - last_blink_time["left"]
                > blink_cooldown
            ):

                pyautogui.click(button="left")

                last_blink_time["left"] = time.time()



        elif right_closed and not left_closed:

            if (
                time.time()
                - last_blink_time["right"]
                > blink_cooldown
            ):

                pyautogui.click(button="right")

                last_blink_time["right"] = time.time()



        cv2.putText(
            frame,
            f"Left Ear: {left_ear:.2f}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            GOLD,
            2
        )

        cv2.putText(
            frame,
            f"Right Ear: {right_ear:.2f}",
            (30, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            GOLD,
            2
        )

    cv2.imshow("Eye Tracker", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
