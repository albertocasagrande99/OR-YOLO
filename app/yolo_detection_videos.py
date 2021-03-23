import numpy as np
import argparse
import imutils
import time
import cv2
import os
import time
import pafy
import datetime

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
labels = APP_ROOT+'/cfg/coco.names'
model_config = APP_ROOT+'/cfg/yolov3.cfg'
model = APP_ROOT+'/cfg/yolov3.weights'
input_videos = APP_ROOT+'/videos/'

LABELS = open(labels).read().strip().split('\n')
COLORS = np.random.randint(0, 255, size = (len(LABELS), 3), dtype = 'uint8')



#Salvataggio video e successiva visualizzazione
def detectObjectsSaveVideo(video):
	oggetti = []

# get video frames and pass to YOLO for output

	# load YOLO from cv2.dnn 
	# determine only the output layer names we need from YOLO
	net = cv2.dnn.readNetFromDarknet(model_config, model)

	ln = net.getLayerNames()
	ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

	# initialize video stream, pointer to output video file and grabbing frame dimension
	vs = cv2.VideoCapture(input_videos+''+video)
	fps = vs.get(cv2.CAP_PROP_FPS)
	writer_width = int(vs.get(cv2.CAP_PROP_FRAME_WIDTH))
	writer_height = int(vs.get(cv2.CAP_PROP_FRAME_HEIGHT))

	writer = None
	(W,H) = (None, None)

	KPS = 6  # Target Keyframes Per Second
	hop = round(fps / KPS)
	curr_frame = 0

	# loop over on entire video frames
	while True:
		# read next frame
		(grabbed, frame) = vs.read()
		if curr_frame % hop == 0:
			# if no frame is grabbed, we reached the end of video, so break the loop
			if not grabbed:
				break
			# if the frame dimensions are empty, grab them
			if W is None or H is None:
				(H,W) = frame.shape[:2]

			# build blob and feed forward to YOLO to get bounding boxes and probability
			blob = cv2.dnn.blobFromImage(frame, 1/255.0, (320,320), swapRB = True, crop = False)
			net.setInput(blob)
			layerOutputs = net.forward(ln)

	
	# get metrics from YOLO

			boxes = []
			confidences = []
			classIDs = []

			# loop over each output from layeroutputs
			for output in layerOutputs:
				# loop over each detecton in output
				for detection in output:
					# extract score, ids and confidence of current object detection
					score = detection[5:]
					classID = np.argmax(score)
					confidence = score[classID]

					# filter out weak detections with confidence threshold
					if confidence > 0.5:
						# scale bounding box coordinates back relative to image size
						# YOLO spits out center (x,y) of bounding boxes followed by 
						# boxes width and heigth
						box = detection[0:4] * np.array([W, H, W, H])
						(centerX, centerY, width, height) = box.astype('int')

						# grab top left coordinate of the box
						x = int(centerX - (width/2))
						y = int(centerY - (height/2))

						boxes.append([x,y, int(width), int(height)])
						confidences.append(float(confidence))
						classIDs.append(classID)


	# Apply Non-Max Suppression, draw boxes and write output video 

			idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.3)
			# ensure detection exists
			if len(idxs) > 0:
				for i in idxs.flatten():
					# getting box coordinates
					(x,y) = (boxes[i][0], boxes[i][1])
					(w,h) = (boxes[i][2], boxes[i][3])

					# color and draw boxes
					color = [int(c) for c in COLORS[classIDs[i]]]
					cv2.rectangle(frame, (x,y), (x+w, y+h), color, 2)
					perc = '%.2f'%(confidences[i]*100)
					text = f"{LABELS[classIDs[i]]}: {perc}%"
					cv2.putText(frame, text.upper(), (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
					oggetti.append(LABELS[classIDs[i]])

			
			if writer is None:
				# initialize video writer by setting fourcc
				# and writing output video to output path
				# fourcc = cv2.VideoWriter_fourcc(*'H264')
				fourcc = cv2.VideoWriter_fourcc(*'H264')
				writer = cv2.VideoWriter(APP_ROOT+'/videos/00'+video, fourcc, fps, (writer_width, writer_height), True)

			for i in range(6):
				writer.write(frame)
			
		curr_frame += 1
	writer.release()
	vs.release()
	return oggetti


def findVideoObjects(video, type, source):
	oggetti = []
	net = cv2.dnn.readNetFromDarknet(model_config, model)
	ln = net.getLayerNames()
	ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    
	"""Video streaming generator function."""
	if(type=="video"):
		cap = cv2.VideoCapture(input_videos+''+video)
	elif(type=="webcam"):
		cap = cv2.VideoCapture(int(source))
	fps = cap.get(cv2.CAP_PROP_FPS)
	
	(W,H) = (None, None)
    # determine the total number of frames in a video
	if(type=="video"):
		try:
			prop = cv2.CAP_PROP_FRAME_COUNT if imutils.is_cv2() else cv2.CAP_PROP_FRAME_COUNT
			total = int(cap.get(prop))
			print(f"[INFO] {total} frames in the video")

		# if error occurs print
		except:
			print(f"[INFO] {total} frames in the video")
			total = -1
		
	KPS = 5  # Target Keyframes Per Second
	hop = round(fps / KPS)
	curr_frame = 0
    # Read until video is completed
	while(cap.isOpened()):
        # read next frame
		(grabbed, frame) = cap.read()
		if curr_frame % hop == 0:
            # if no frame is grabbed, we reached the end of video, so break the loop
			if not grabbed:
				break
			# if the frame dimensions are empty, grab them
			if W is None or H is None:
				(H,W) = frame.shape[:2]

			# build blob and feed forward to YOLO to get bounding boxes and probability
			blob = cv2.dnn.blobFromImage(frame, 1/255.0, (320,320), swapRB = True, crop = False)
			start = time.time()
			net.setInput(blob)
			layerOutputs = net.forward(ln)
			end = time.time()

	
	# get metrics from YOLO
			boxes = []
			confidences = []
			classIDs = []

			# loop over each output from layeroutputs
			for output in layerOutputs:
				# loop over each detecton in output
				for detection in output:
					# extract score, ids and confidence of current object detection
					score = detection[5:]
					classID = np.argmax(score)
					confidence = score[classID]

					# filter out weak detections with confidence threshold
					if confidence > 0.5:
						# scale bounding box coordinates back relative to image size
						# YOLO spits out center (x,y) of bounding boxes followed by 
						# boxes width and heigth
						box = detection[0:4] * np.array([W, H, W, H])
						(centerX, centerY, width, height) = box.astype('int')

						# grab top left coordinate of the box
						x = int(centerX - (width/2))
						y = int(centerY - (height/2))
                        
						boxes.append([x,y, int(width), int(height)])
						confidences.append(float(confidence))
						classIDs.append(classID)


	# Apply Non-Max Suppression, draw boxes and write output video
			idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.3)
			# ensure detection exists
			if len(idxs) > 0:
				for i in idxs.flatten():
					# getting box coordinates
					(x,y) = (boxes[i][0], boxes[i][1])
					(w,h) = (boxes[i][2], boxes[i][3])

					# color and draw boxes
					color = [int(c) for c in COLORS[classIDs[i]]]
					cv2.rectangle(frame, (x,y), (x+w, y+h), color, 2)
					perc = '%.2f'%(confidences[i]*100)
					text = f"{LABELS[classIDs[i]]}: {perc}%"
					cv2.putText(frame, text.upper(), (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
					oggetti.append(LABELS[classIDs[i]])
					
			frame = cv2.imencode('.jpg', frame)[1].tobytes()
			yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
			
		curr_frame += 1
	
	oggetti = list(dict.fromkeys(oggetti))
	print("Detected objects: ")
	for elem in oggetti:
		print("- ", elem)
	cap.release()

#Link video YouTube
def findYouTubeObjects(url):
	print(url)
	net = cv2.dnn.readNetFromDarknet(model_config, model)
	ln = net.getLayerNames()
	ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

	vPafy = pafy.new(url)
	play = vPafy.getbest(preftype="mp4")
    
	"""Video streaming generator function."""
	cap = cv2.VideoCapture(play.url)
	fps = cap.get(cv2.CAP_PROP_FPS)
	
	(W,H) = (None, None)
    # determine the total number of frames in a video
	try:
		prop = cv2.CAP_PROP_FRAME_COUNT if imutils.is_cv2() else cv2.CAP_PROP_FRAME_COUNT
		total = int(cap.get(prop))
		print(f"[INFO] {total} frames in the video")

    # if error occurs print
	except:
		print(f"[INFO] {total} frames in the video")
		total = -1
		
	KPS = 5  # Target Keyframes Per Second
	hop = round(fps / KPS)
	curr_frame = 0
    # Read until video is completed
	while(cap.isOpened()):
        # read next frame
		(grabbed, frame) = cap.read()
		if curr_frame % hop == 0:
            # if no frame is grabbed, we reached the end of video, so break the loop
			if not grabbed:
				break
			# if the frame dimensions are empty, grab them
			if W is None or H is None:
				(H,W) = frame.shape[:2]

			# build blob and feed forward to YOLO to get bounding boxes and probability
			blob = cv2.dnn.blobFromImage(frame, 1/255.0, (320,320), swapRB = True, crop = False)
			start = time.time()
			net.setInput(blob)
			layerOutputs = net.forward(ln)
			end = time.time()

	
	# get metrics from YOLO
			boxes = []
			confidences = []
			classIDs = []

			# loop over each output from layeroutputs
			for output in layerOutputs:
				# loop over each detecton in output
				for detection in output:
					# extract score, ids and confidence of current object detection
					score = detection[5:]
					classID = np.argmax(score)
					confidence = score[classID]

					# filter out weak detections with confidence threshold
					if confidence > 0.5:
						# scale bounding box coordinates back relative to image size
						# YOLO spits out center (x,y) of bounding boxes followed by 
						# boxes width and heigth
						box = detection[0:4] * np.array([W, H, W, H])
						(centerX, centerY, width, height) = box.astype('int')

						# grab top left coordinate of the box
						x = int(centerX - (width/2))
						y = int(centerY - (height/2))
                        
						boxes.append([x,y, int(width), int(height)])
						confidences.append(float(confidence))
						classIDs.append(classID)


	# Apply Non-Max Suppression, draw boxes and write output video
			idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.3)
			# ensure detection exists
			if len(idxs) > 0:
				for i in idxs.flatten():
					# getting box coordinates
					(x,y) = (boxes[i][0], boxes[i][1])
					(w,h) = (boxes[i][2], boxes[i][3])

					# color and draw boxes
					color = [int(c) for c in COLORS[classIDs[i]]]
					cv2.rectangle(frame, (x,y), (x+w, y+h), color, 2)
					perc = '%.2f'%(confidences[i]*100)
					text = f"{LABELS[classIDs[i]]}: {perc}%"
					cv2.putText(frame, text.upper(), (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
					
			frame = cv2.imencode('.jpg', frame)[1].tobytes()
			yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
			
		curr_frame += 1
	cap.release()