import os
from flask import Flask, request, render_template, send_from_directory
from flask import Flask, session, request, redirect, url_for
import yolo_detection_images
import string
import random
import json
import cv2
from PIL import Image
import PIL
import glob


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
        listImmagini = os.listdir("./images")
        print("Il file caricato è {}".format(upload.filename))
        filename = upload.filename
        q = request.form.get('qualità')
        estensione = filename[-3:]  #Prelievo estensione immagine utente
        filename = session.get("user") +"."+ estensione #Rinominazione immagine caricata dall'utente con il nome della sessione corrente (per utilizzo multi-utente contemporaneamente)
        #Sovrascrivere l'ultima immagine caricata da un utente (se presente)  

        if filename in listImmagini:
            os.remove("./images/"+filename)
        session["lastImage"] = filename 
        destination = "/".join([target, filename])
        #Salvataggio immagine nella cartella ./images
        upload.save(destination)
        
        im = Image.open("./images/"+filename)
        print(f"The image size dimensions are: {im.size}")
        if(q == "alta"):
            im.save("./images/"+filename,optimize=True,quality=100)
        elif(q == "media"):
            im.save("./images/"+filename,optimize=True,quality=50)
        else:
            im.save("./images/"+filename,optimize=True,quality=10)

        img, obj, tempo = yolo_detection_images.result(filename)
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

#Funzioni richiamate al momento della creazione del Server
if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(port=4555, debug=True)
