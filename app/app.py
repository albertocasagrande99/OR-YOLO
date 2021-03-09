import os
from flask import Flask, request, render_template, send_from_directory
from flask import Flask, session, request, redirect, url_for, Response
import yolo_detection_images
import yolo_detection_videos
import string
import random
import json
import cv2
from PIL import Image
import PIL
import glob
import imutils
import time
import numpy as np
import pafy
import base64

__author__ = 'IO'

app = Flask(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
sub = cv2.createBackgroundSubtractorMOG2()  # create background subtractor
des=os.path.join(APP_ROOT,"static","test.jpeg")

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
        estensione = os.path.splitext(filename)[1] #Prelievo estensione immagine utente
        #estensione = filename[-3:]
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

        img, obj, tempo = yolo_detection_images.result(filename)
    return render_template("image.html", filename = filename, oggetti=obj, tempo = tempo)


@app.route('/image/<filename>')
def send_image(filename):
    return send_from_directory("images", filename)


@app.route("/video")
def video():
    return render_template("video.html")


@app.route("/video", methods=["POST"])
def upload_video():
    #Controllo sessione dell'utente
    if not session.get('user') is None:
        print("Sessione già creata per l'utente")
    else:
        print("Nuovo Utente, creazione sessione")
        session["user"] = id_generator(10)
    print("Codice sessione corrente: "+session.get("user"))

    
    target = os.path.join(APP_ROOT, 'videos/')
    #Creazione cartella ./images se non presente
    if not os.path.isdir(target):
        os.mkdir(target)

    #Salvataggio immagine caricata dall'utente nella cartella ./images
    for upload in request.files.getlist("file"):
        listImmagini = os.listdir(APP_ROOT+"/videos")
        print("Il file caricato è {}".format(upload.filename))
        filename = upload.filename
        estensione = filename[-3:]  #Prelievo estensione video utente
        filename = session.get("user") +"."+ estensione #Rinominazione video caricato dall'utente con il nome della sessione corrente (per utilizzo multi-utente contemporaneamente)
        #Sovrascrivere l'ultimo video caricato da un utente (se presente)  

        if filename in listImmagini:
            os.remove(APP_ROOT+"/videos/"+filename)
        session["lastVideo"] = filename 
        destination = "/".join([target, filename])
        #Salvataggio video nella cartella ./videos
        upload.save(destination)
        #obj = yolo_detection_videos.findObjects(filename)
        
        '''
        oggetti = [] 
        for i in obj: 
            if i not in oggetti: 
                oggetti.append(i) 
        '''
    return render_template("video.html", filename=filename)

'''
@app.route('/video/<filename>')
def send_video(filename):
    return send_from_directory("videos", '00'+filename)
'''

@app.route("/YouTubeVideo")
def YTvideo():
    return render_template("YTvideo.html")

@app.route("/YouTubeVideo", methods=["POST"])
def link_video():
    #Controllo sessione dell'utente
    if not session.get('user') is None:
        print("Sessione già creata per l'utente")
    else:
        print("Nuovo Utente, creazione sessione")
        session["user"] = id_generator(10)
    print("Codice sessione corrente: "+session.get("user"))

    url = request.form.get('url')
    try:
        video = pafy.new(url)
        session["url"] = url
        titolo = video.title
    except:
        titolo = "Error"
    return render_template("YTvideo.html", filename=url, titolo=titolo)


@app.route("/Webcam")
def webcam():
    return render_template("webcam.html")


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

@app.route('/video_feed/<filename>')
def video_feed(filename):
    if(filename == "link"):
        return Response(yolo_detection_videos.findYouTubeObjects(session["url"]),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    elif(filename=="webcam"):
        return Response(yolo_detection_videos.findWebcamObjects(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(yolo_detection_videos.findVideoObjects(filename),
                        mimetype='multipart/x-mixed-replace; boundary=frame')


#Funzioni richiamate al momento della creazione del Server
if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(host='0.0.0.0', port=4555, debug=True)
