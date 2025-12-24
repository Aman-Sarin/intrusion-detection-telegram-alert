import cv2
import torch
import numpy as np

from detector import Detector
from roi import ROIHandler
from telegram_alert import TelegramAlert
from video_stream import VideoStream

def main():
    url_of_camera = 0
    chat_id = 12345678

    import os
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = 1086434406

    telegram_alert = TelegramAlert(
        bot_token=BOT_TOKEN,
        chat_id=chat_id
    )

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    detector = Detector(device)
    roi_handler = ROIHandler()
    video_stream = VideoStream(url_of_camera)

    player = video_stream.get_video_from_url()
    assert player.isOpened()

    cv2.namedWindow('image')

    while True:
        ret, frame = player.read()
        if not ret:
            break

        param = frame.copy()
        cv2.imshow('image', frame)

        if not roi_handler.right_click_happened:
            if not roi_handler.mouse_callback_happened:
                cv2.setMouseCallback('image', roi_handler.extract_coordinates, param)
                roi_handler.mouse_callback_happened = True

            for x, y in roi_handler.image_coordinates:
                cv2.circle(param, (x, y), 2, (0, 0, 255), 2)
                cv2.imshow('image', param)

        else:
            points = np.array(roi_handler.image_coordinates, dtype=np.int32)
            pts = points.reshape((-1, 1, 2))

            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.fillConvexPoly(mask, pts, 1)
            mask = mask.astype(bool)

            out = frame.copy()
            out[~mask] = 0

            results = detector.score_frame(out)
            out = detector.plot_boxes(results, out)
            frame = detector.plot_boxes(results, frame)

            cv2.imshow('masked_image', out)
            cv2.imshow('image', frame)

            person_detected = False

            labels, cords = results
            for i in range(len(labels)):
                if int(labels[i]) == 0 and float(cords[i][4]) >= 0.6:
                    person_detected = True
                    break

            person_detected = detector.person_detected_in_frame(results)

            if telegram_alert.to_send_or_not(person_detected):
                telegram_alert.sending_to_telegram()
                telegram_alert.send_image_to_telegram(out)

        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    player.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
