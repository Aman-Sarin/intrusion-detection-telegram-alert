import cv2
import numpy as np

class ROIHandler:
    def __init__(self):
        self.image_coordinates = []
        self.right_click_happened = False
        self.mouse_callback_happened = False


    def extract_coordinates(self, event, x, y, flag, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.image_coordinates.append([x, y])

        elif event == cv2.EVENT_RBUTTONDOWN:
            cv2.setMouseCallback('image', lambda *args: None)
            self.right_click_happened = True


