import cv2
import numpy as np
import os
import time

whT = 320
confThreshold = 0.5
nmsThreshold = 0.3
classesFiles = 'cfg/coco.names'
classNames = []
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

with open(classesFiles, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

# print(classNames)
# print(len(classNames))

modelConfiguration = 'cfg/yolov3.cfg'
modelWeights = 'cfg/yolov3.weights'

net = cv2.dnn.readNetFromDarknet(modelConfiguration, modelWeights)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

def findObjects(outputs, img):
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

    for i in indices:
        i = i[0]
        box = bbox[i]
        x,y,w,h = box[0], box[1], box[2], box[3]
        cv2.rectangle(img,(x,y),(x+w, y+h),(0,0,255),2)
        cv2.putText(img,f'{classNames[classIds[i]].upper()} {int(confs[i]*100)}%', (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255),2)
        oggetti.append(""+classNames[classIds[i]]+" "+str('%.2f'%(float(confs[i]*100)))+"%")
    
    return img, oggetti

def result(input):
    img = cv2.imread("./images/"+input)
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
    res, obj = findObjects(outputs, img)
    end = time.time()
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))
    os.remove("./images/"+input)
    target = os.path.join(APP_ROOT, 'images/')
    destination = "/".join([target, input])
    cv2.imwrite(destination, res)
    return res, obj