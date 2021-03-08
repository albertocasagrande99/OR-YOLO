import cv2
import numpy as np
import os
import time
from PIL import Image
import PIL

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
whT = 320
confThreshold = 0.5
nmsThreshold = 0.3
classesFiles = APP_ROOT+'/cfg/coco.names'
classNames = []


with open(classesFiles, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')
COLORS = np.random.randint(0, 255, size = (len(classNames), 3), dtype = 'uint8')
# print(classNames)
# print(len(classNames))

modelConfiguration = APP_ROOT+'/cfg/yolov3.cfg'
modelWeights = APP_ROOT+'/cfg/yolov3.weights'

net = cv2.dnn.readNetFromDarknet(modelConfiguration, modelWeights)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

def findObjects(outputs, img, input):
    hT, wT, cT = img.shape
    bbox = []
    classIds = []
    confs = []
    oggetti = []

    for output in outputs:
        for det in output:
            scores = det[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                w,h = int(det[2]*wT) , int(det[3]*hT)
                x,y = int((det[0]*wT)-w/2), int((det[1]*hT)-h/2)
                bbox.append([x,y,w,h])
                classIds.append(classId)
                confs.append(float(confidence))
    print(len(bbox))
    indices = cv2.dnn.NMSBoxes(bbox, confs, confThreshold, nmsThreshold)

    im = Image.open(APP_ROOT+"/images/"+input)
    wid, hgt = im.size

    for i in indices:
        i = i[0]
        box = bbox[i]
        x,y,w,h = box[0], box[1], box[2], box[3]
        color = [int(c) for c in COLORS[classIds[i]]]
        if(wid > 1500 and hgt > 1500):
            cv2.rectangle(img,(x,y),(x+w, y+h),color,8)
            cv2.putText(img,f'{classNames[classIds[i]].upper()} {int(confs[i]*100)}%', (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 5.5, color,11)
        else:
            cv2.rectangle(img,(x,y),(x+w, y+h),color,2)
            cv2.putText(img,f'{classNames[classIds[i]].upper()} {int(confs[i]*100)}%', (x,y-10), cv2.FONT_HERSHEY_SIMPLEX , 0.6, color,2)
        
        oggetti.append((classNames[classIds[i]], str('%.2f'%(float(confs[i]*100)))+"%"))
    
    return img, oggetti

def result(input):
    img = cv2.imread(APP_ROOT+"/images/"+input)
    start = time.time()
    blob = cv2.dnn.blobFromImage(img, 1/255, (whT,whT), [0,0,0], 1, crop=False)
    net.setInput(blob)
    layerNames = net.getLayerNames()
    #print(layerNames)
    outputNames = [layerNames[i[0]-1] for i in net.getUnconnectedOutLayers()]
    #print(outputNames)
    #print(net.getUnconnectedOutLayers())

    outputs = net.forward(outputNames)
    print(outputs[0])
    print(outputs[1])
    print(outputs[2])

    print(outputs[0][0])
    res, obj = findObjects(outputs, img, input)
    end = time.time()
    tempo = ('%.3f'%(float(end - start)))
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))
    os.remove(APP_ROOT+"/images/"+input)
    target = os.path.join(APP_ROOT, 'images/')
    destination = "/".join([target, input])
    cv2.imwrite(destination, res)
    return res, obj, tempo