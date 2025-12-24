import torch
import cv2

class Detector:
    def __init__(self, device):
        self.device = device
        self.model = self.load_model()
        self.classes = self.model.names


    def load_model(self):
        # """
        # Loads Yolo5 model from pytorch hub.
        # :return: Trained Pytorch model.
        # """
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        return model


    def score_frame(self, frame):
        # """
        # Takes a single frame as input, and scores the frame using yoloV5 model.
        # :param frame: input frame in numpy/list/tuple format.
        # :return: Labels and Coordinates of objects detected by model in the frame.
        # """
        self.model.to(self.device)
        frame = [frame]
        results = self.model(frame)
        # results.#print()
        labels, cord = results.xyxyn[0][:, -1], results.xyxyn[0][:, :-1]
        return labels, cord

    def class_to_label(self, x):
        # """
        # For a given label value, return corresponding string label.
        # :param x: numeric label
        # :return: corresponding string label
        # """
        return self.classes[int(x)]  # Example- input = 0, output = 'person'


    def plot_boxes(self, results, frame):
        labels, cord = results
        n = len(labels)
        x_shape, y_shape = frame.shape[1], frame.shape[0]
        for i in range(n):
            row = cord[i]
            print('the value of row4 is:', row[4])
            if row[4] >= 0.6 and self.class_to_label(labels[i]) == 'person':
                x1, y1, x2, y2 = int(row[0] * x_shape), int(row[1] * y_shape), int(row[2] * x_shape), int(row[3] * y_shape)
                # print(x1,y1,x2,y2)
                bgr = (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
                text = self.class_to_label(labels[i])  # +" "+row[4]
                cv2.putText(frame, text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)
        return frame

    def person_detected_in_frame(self, results, conf_thresh=0.6):
        labels, cord = results
        for i in range(len(labels)):
            if cord[i][4] >= conf_thresh and self.class_to_label(labels[i]) == 'person':
                return True
        return False
