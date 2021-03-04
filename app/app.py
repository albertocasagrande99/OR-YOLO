import os
from flask import Flask, request, render_template, send_from_directory
from flask import Flask, session, request, redirect, url_for
#import yolo_detection_images
import string
import random
import json
import cv2
from PIL import Image
import PIL
import glob

######
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
#######

__author__ = 'IO'

app = Flask(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

#Frammento di codice usato per gestire gli errori del Server (eccezione 404 page not found)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#Visualizzazione index della web app
@app.route("/")
def index():
    return render_template("index.html")

#Visualizzazione della pagine di upload
@app.route("/image")
def upload_get():
    return render_template("image.html")

#Metodo richiamato quando si fa l'upload dell'immagine
@app.route("/image", methods=["POST"])
def upload():
    #Controllo sessione dell'utente
    if not session.get('user') is None:
        print("Sessione già creata per l'utente")
    else:
        print("Nuovo Utente, creazione sessione")
        session["user"] = id_generator(10)
    print("Codice sessione corrente: "+session.get("user"))

    
    target = os.path.join(APP_ROOT, 'images/')
    #Creazione cartella ./images se non presente
    if not os.path.isdir(target):
        os.mkdir(target)

    #Salvataggio immagine caricata dall'utente nella cartella ./images
    for upload in request.files.getlist("file"):
        listImmagini = os.listdir(APP_ROOT+"/images")
        print("Il file caricato è {}".format(upload.filename))
        filename = upload.filename
        q = request.form.get('qualità')
        estensione = filename[-3:]  #Prelievo estensione immagine utente
        filename = session.get("user") +"."+ estensione #Rinominazione immagine caricata dall'utente con il nome della sessione corrente (per utilizzo multi-utente contemporaneamente)
        #Sovrascrivere l'ultima immagine caricata da un utente (se presente)  

        if filename in listImmagini:
            os.remove(APP_ROOT+"/images/"+filename)
        session["lastImage"] = filename 
        destination = "/".join([target, filename])
        #Salvataggio immagine nella cartella ./images
        upload.save(destination)
        
        im = Image.open(APP_ROOT+"/images/"+filename)
        print(f"The image size dimensions are: {im.size}")
        if(q == "alta"):
            im.save(APP_ROOT+"/images/"+filename,optimize=True,quality=100)
        elif(q == "media"):
            im.save(APP_ROOT+"/images/"+filename,optimize=True,quality=50)
        else:
            im.save(APP_ROOT+"/images/"+filename,optimize=True,quality=10)

        #img, obj, tempo = yolo_detection_images.result(filename)
        img, obj, tempo = result(filename)
        #print(obj)
        oggetti = []
        for elem in obj:
            oggetti.append(elem.split())

    return render_template("image.html", filename = filename, oggetti = oggetti, tempo = tempo)


@app.route('/image/<filename>')
def send_image(filename):
    return send_from_directory("images", filename)

#Funzione per agire sulla cache
@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

#Funzione per generare id casuale utente
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))







with open(classesFiles, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

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
        if(wid > 1500 and hgt > 1500):
            cv2.rectangle(img,(x,y),(x+w, y+h),(0,0,255),8)
            cv2.putText(img,f'{classNames[classIds[i]].upper()} {int(confs[i]*100)}%', (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 5.5, (0,0,255),11)
        else:
            cv2.rectangle(img,(x,y),(x+w, y+h),(0,0,255),2)
            cv2.putText(img,f'{classNames[classIds[i]].upper()} {int(confs[i]*100)}%', (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255),2)
        
        oggetti.append(""+classNames[classIds[i]]+" "+str('%.2f'%(float(confs[i]*100)))+"%")
    
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

#Funzioni richiamate al momento della creazione del Server
if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(host='0.0.0.0', port=4555, debug=True)
