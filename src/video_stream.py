import cv2

class VideoStream:
    def __init__(self, url):
        self._URL = url


    def get_video_from_url(self):
        # """
        # Creates a new video streaming object to extract video frame by frame to make prediction on.
        # :return: opencv2 video capture object, with lowest quality frame available for video.
        # """
        return cv2.VideoCapture(self._URL)
    # return cv2.VideoCapture(self._URL,cv2.CAP_DSHOW)