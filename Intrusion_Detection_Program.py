from sympy import false
import torch
import numpy as np
import cv2
import time
import telebot
import requests  
from apscheduler.schedulers.background import BackgroundScheduler
import threading

 


class IntrusionDetection:
	"""
	Class implements YoloV5 model to detect Intrusion from Camera
	"""

	def __init__(self, url,token,receiver_id,url_of_group,chat_id, out_file):
		"""
			>Initialization:
				*URL: Stream address
				*token: token of the Chatbot
				*reciever_id: Reciever id of the Telegram Group
				*url_of_group: URL of the group
				*chat_id: ID of the chat
				*out_file: Output file
		"""

		self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
		self._URL = url
		self.model = self.load_model()
		self.classes = self.model.names
		self.token = token
		self.receiver_id = receiver_id
		self.bot=telebot.TeleBot(token)
		self.out_file = out_file
		self.url_of_group = url_of_group
		self.chat_id = chat_id
		self.image_coordinates = []
		self.right_click_happened = False
		self.count=0
		self.var = True
		print("\n\nDevice Used:",self.device)
	




	def get_video_from_url(self):
		# """
				# Creates a new video streaming object to extract video frame by frame to make prediction on.
				# :return: opencv2 video capture object, with lowest quality frame available for video.
		# """
		return cv2.VideoCapture(self._URL)
		# return cv2.VideoCapture(self._URL,cv2.CAP_DSHOW)


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
		#results.#print()
		labels, cord = results.xyxyn[0][:, -1], results.xyxyn[0][:, :-1]
		return labels, cord


	def class_to_label(self, x):
		# """
				# For a given label value, return corresponding string label.
				# :param x: numeric label
				# :return: corresponding string label
		# """
		return self.classes[int(x)] #Example- input = 0, output = 'person'


	def plot_boxes(self, results, frame):
		labels, cord = results
		n = len(labels)
		x_shape, y_shape = frame.shape[1], frame.shape[0]
		for i in range(n):
			row = cord[i]
			print('the value of row4 is:',row[4])
			if row[4] >= 0.6 and self.class_to_label(labels[i])=='person':
				x1, y1, x2, y2 = int(row[0]*x_shape), int(row[1]*y_shape), int(row[2]*x_shape), int(row[3]*y_shape)
				#print(x1,y1,x2,y2)
				bgr = (0, 255, 0)
				cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
				text = self.class_to_label(labels[i]) #+" "+row[4]
				cv2.putText(frame,text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)
		return frame


	def sending_to_telegram(self,results):
		labels, cord = results
		n = len(labels)

		for i in range(n):
			row = cord[i]
			if row[4] >= 0.6 and self.class_to_label(labels[i])=='person':
				self.count+=1
				if self.count==10:
					self.count = 0
					self.var = True

				if self.var == True:
					self.var = False
					base_url = self.url_of_group+f'/sendMessage?chat_id={self.chat_id}&text={self.class_to_label(labels[i])} has been detected'
					requests.get(base_url)
					

	def to_send_or_not(self,results):
		labels, cord = results
		n = len(labels)
		for i in range(n):
			row=cord[i]
			if row[4] >= 0.6 and self.class_to_label(labels[i])=='person': #and labels[i]=='person':
				return True
		return False


	def extract_coordinates(self,event, x, y, flag, param):
		if event == cv2.EVENT_LBUTTONDOWN:
			self.image_coordinates.append([x,y])

		elif event == cv2.EVENT_RBUTTONDOWN:
			cv2.setMouseCallback('image', lambda *args : None)
			self.right_click_happened = True


	def call(self):

		# """
				# This function is called when class is executed, it runs the loop to read the video frame by frame,
				# and sends the photo if a person is detected.
				# :return: void
		# """

		player = self.get_video_from_url()
		assert player.isOpened()
		x_shape = int(player.get(cv2.CAP_PROP_FRAME_WIDTH))
		y_shape = int(player.get(cv2.CAP_PROP_FRAME_HEIGHT))
		base_url = self.url_of_group+f'/sendMessage?chat_id={self.chat_id}&text=Your Camera is Active Now.'
		requests.get(base_url)

		self.mouse_callback_happened = False
		while True:
			ret, frame = player.read()
			param=frame
			cv2.imshow('image',frame)
			if cv2.waitKey(50) & 0xFF == ord('q'):
				break

			if self.right_click_happened==False:
				if self.mouse_callback_happened==False:
					cv2.setMouseCallback('image', self.extract_coordinates,param)
					self.mouse_callback_happened = True
				for i in range(len(self.image_coordinates)):
					x=self.image_coordinates[i][0]
					y=self.image_coordinates[i][1]
					cv2.circle(param,center = (x,y),radius=2,color = (0,0,255),thickness=2)
					cv2.imshow('image',param)
					if cv2.waitKey(50) & 0xFF == ord('q'):
						break


			elif self.right_click_happened==True:
				points = np.array(self.image_coordinates)
				points = points.reshape((-1, 1, 2))

				color = (255, 0, 0)
				thickness = 2
				isClosed = True

				# drawPolyline
				image = cv2.polylines(frame, [points], isClosed, color, thickness)
				cv2.imshow('image',param)
				if cv2.waitKey(50) & 0xFF == ord('q'):
					break
				image = cv2.polylines(frame, [points], isClosed, color, thickness)

				#masking
				mask = np.zeros((frame.shape[0], frame.shape[1]))
				cv2.fillConvexPoly(mask, points, 1)
				mask = mask.astype(np.bool_)

				out = np.zeros_like(frame)
				out[mask] = frame[mask]
				cv2.imshow('masked_image',out)
				if cv2.waitKey(50) & 0xFF == ord('q'):
					break

				#Detection
				results = self.score_frame(out)
				out = self.plot_boxes(results,out)
				cv2.imshow("masked_image",out)
				if cv2.waitKey(50) & 0xFF == ord('q'):
					break


				frame = self.plot_boxes(results,frame)
				cv2.imshow("image",frame)
				if cv2.waitKey(50) & 0xFF == ord('q'):
					break
			
				if self.to_send_or_not(results):
						self.sending_to_telegram(results)
		


	#IP Webcam: 'http://192.168.43.1:8080/video'
	# Creating a new object and executing



# url_of_camera = input('Enter the url of the camera: ') 	#Enter integer 0 in case of Webcam
url_of_camera = 'http://192.168.40.205:8080/video'
#detetction = IntrusionDetection(url,token,receiver_id,url_of_group,chat_id, out_file)


#Following line needs to be replaced
detection = IntrusionDetection(url_of_camera,'5106030113:AAG0_RShiDbA7eK***********','*******','https://api.telegram.org/bot**********' ,'-75027****',"video2.avi")
detection.call()
cv2.destroyAllWindows()