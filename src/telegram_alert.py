from collections import deque
import time
import requests
import cv2


class TelegramAlert:
    def __init__(self, bot_token, chat_id, cooldown=15, window_size=30, min_positive_frames=12):
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

        self.cooldown = cooldown
        self.window = deque(maxlen=window_size)
        self.min_positive_frames = min_positive_frames
        self.last_sent_time = 0

    def to_send_or_not(self, person_detected):
        current_time = time.time()
        self.window.append(person_detected)

        positive_count = sum(self.window)
        print(f"[ALERT DEBUG] positives={positive_count}/{len(self.window)}")

        if positive_count >= self.min_positive_frames:
            if current_time - self.last_sent_time >= self.cooldown:
                self.last_sent_time = current_time
                self.window.clear()
                return True

        return False

    def sending_to_telegram(self):
        payload = {
            "chat_id": self.chat_id,
            "text": "🚨 Intrusion detected inside ROI"
        }

        r = requests.post(
            f"{self.api_url}/sendMessage",
            data=payload,
            timeout=5
        )

        print("[TELEGRAM STATUS]", r.status_code, r.text)

    def send_image_to_telegram(self, frame):
        # Encode frame as JPEG
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            print("[TELEGRAM ERROR] Failed to encode image")
            return

        files = {
            "photo": buffer.tobytes()
        }

        data = {
            "chat_id": self.chat_id,
            "caption": "🚨 Intrusion detected inside ROI"
        }

        r = requests.post(
            f"{self.api_url}/sendPhoto",
            data=data,
            files=files,
            timeout=5
        )

        print("[TELEGRAM IMAGE STATUS]", r.status_code, r.text)










