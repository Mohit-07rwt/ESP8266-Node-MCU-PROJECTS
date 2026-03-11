import cv2
import mediapipe as mp
import socket
import math
import time

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

ESP8266_IP = "10.187.221.187"
ESP8266_PORT = 80

# MediaPipe Tasks initialization
BaseOptions = python.BaseOptions
HandLandmarker = vision.HandLandmarker
HandLandmarkerOptions = vision.HandLandmarkerOptions

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="hand_landmarker.task"),
    num_hands=1
)

detector = HandLandmarker.create_from_options(options)


class GestureController:

    def __init__(self):
        self.prev_finger_count = -1
        self.prev_brightness = -1
        self.prev_angle = -1
        self.socket = None

        self.tip_ids = [4, 8, 12, 16, 20]

    def connect_esp32(self):
        try:
            if self.socket:
                self.socket.close()

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(3)
            self.socket.connect((ESP8266_IP, ESP8266_PORT))

            print("Connected to MOHIT")
            return True

        except Exception as e:
            print("ESP32 connection failed:", e)
            self.socket = None
            return False

    def send_command(self, command):

        if not self.socket:
            if not self.connect_esp32():
                return False

        try:
            self.socket.send((command + "\n").encode())
            self.socket.recv(1024)
            return True

        except Exception as e:
            print("Send error:", e)
            self.socket = None
            return False

    def count_fingers(self, landmarks):

        lm_list = []

        for lm in landmarks:
            lm_list.append([lm.x, lm.y])

        fingers = []

        if lm_list[17][0] < lm_list[0][0]:
            if lm_list[4][0] > lm_list[3][0]:
                fingers.append(1)
            else:
                fingers.append(0)
        else:
            if lm_list[4][0] < lm_list[3][0]:
                fingers.append(1)
            else:
                fingers.append(0)

        pip = [6, 10, 14, 18]

        for i in range(4):

            tip = self.tip_ids[i + 1]

            if lm_list[tip][1] < lm_list[pip[i]][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        total = sum(fingers)

        return total

    def palm_openness(self, landmarks):

        wrist = landmarks[0]
        middle_tip = landmarks[12]

        distance = math.sqrt(
            (wrist.x - middle_tip.x) ** 2 +
            (wrist.y - middle_tip.y) ** 2
        )

        min_d = 0.05
        max_d = 0.25

        brightness = int(((distance - min_d) / (max_d - min_d)) * 255)

        brightness = max(0, min(255, brightness))

        return brightness

    def hand_angle(self, landmarks):

        wrist = landmarks[0]
        middle = landmarks[9]

        dx = middle.x - wrist.x
        dy = middle.y - wrist.y

        angle = math.degrees(math.atan2(-dy, dx))

        if angle < 0:
            angle += 360

        return angle


def main():

    cap = cv2.VideoCapture(0)

    controller = GestureController()

    controller.connect_esp32()

    mode = "fingers"

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = detector.detect(mp_image)

        if result.hand_landmarks:

            for landmarks in result.hand_landmarks:

                finger_count = controller.count_fingers(landmarks)

                brightness = controller.palm_openness(landmarks)

                angle = controller.hand_angle(landmarks)

                if mode == "fingers":

                    num_leds = int((brightness / 255) * finger_count)

                    command = f"FINGERS:{num_leds},{brightness}"

                    controller.send_command(command)

                    cv2.putText(frame,
                                f"Fingers: {finger_count}",
                                (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (0, 255, 0),
                                2)

                    cv2.putText(frame,
                                f"Brightness: {brightness}",
                                (10, 100),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (0, 255, 255),
                                2)

                if mode == "direction":

                    command = f"DIRECTION:{angle},{brightness}"

                    controller.send_command(command)

                    cv2.putText(frame,
                                f"Angle: {angle:.1f}",
                                (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (255, 255, 0),
                                2)

        else:

            controller.send_command("CLEAR")

            cv2.putText(frame,
                        "No Hand Detected",
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2)

        cv2.putText(frame,
                    "f=Finger  d=Direction  q=Quit",
                    (10, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1)

        cv2.imshow("Gesture Control", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        elif key == ord("f"):
            mode = "fingers"

        elif key == ord("d"):
            mode = "direction"

    controller.send_command("CLEAR")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()