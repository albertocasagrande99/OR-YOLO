import os
from flask import Flask, request, render_template, send_from_directory, jsonify
from flask import Flask, session, request, Response, after_this_request
import yolo_detection_images
import yolo_detection_videos
import string
import random
import cv2
from PIL import Image
import PIL
import imutils
import time
import pafy

__author__ = 'Alberto Casagrande'

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
goAhead = True
goAhead2 = True

#Frammento di codice usato per gestire l'errore 404 lato client (eccezione 404 page not found)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#Visualizzazione index della web app
@app.route("/")
def index():
    return render_template("index.html")

#############   Immagini   #############
#Visualizzazione pagina image.html
@app.route("/image")
def upload_get():
    return render_template("image.html")

#Metodo richiamato quando si carica un'immagine sul server
@app.route("/image", methods=["POST"])
def upload():
    global goAhead
    while goAhead==False:
        time.sleep(3)
    goAhead = False
    
    check_session()
    
    #Creazione cartella ./images se non presente
    target = os.path.join(APP_ROOT, 'images/')
    check_target(target)

    #Salvataggio immagine caricata dall'utente nella cartella ./images
    for upload in request.files.getlist("file"):
        listImmagini = os.listdir(APP_ROOT+"/images")
        print("Il file caricato è {}".format(upload.filename))
        filename = upload.filename
        session["quality"] = request.form.get('qualità')
        estensione = os.path.splitext(filename)[1] #Prelievo estensione immagine utente
        filename = session.get("user") + estensione #Rinominazione immagine caricata dall'utente con il nome della sessione corrente (per utilizzo multi-utente contemporaneamente)
        
        #Sovrascrivere l'ultima immagine caricata da un utente (se presente)  
        if filename in listImmagini:
            os.remove(APP_ROOT+"/images/"+filename)
        session["lastImage"] = filename 
        destination = "/".join([target, filename])
        #Salvataggio immagine nella cartella ./images
        upload.save(destination)
        
        #Salvataggio dell'immagine secondo la qualità selezionata dall'utente
        im = Image.open(APP_ROOT+"/images/"+session.get("lastImage"))
        print(f"The image size dimensions are: {im.size}")
        if(session.get("quality") == "high"):
            #im.save(APP_ROOT+"/images/"+session.get("lastImage"),quality=100, subsampling=0)
            print(os.stat(APP_ROOT+"/images/"+session.get("lastImage")).st_size)
        elif(session.get("quality") == "medium"):
            im.save(APP_ROOT+"/images/"+session.get("lastImage"),optimize=True,quality=50)
            print(os.stat(APP_ROOT+"/images/"+session.get("lastImage")).st_size)
        else:
            im.save(APP_ROOT+"/images/"+session.get("lastImage"),optimize=True,quality=10)
            print(os.stat(APP_ROOT+"/images/"+session.get("lastImage")).st_size)

        obj, tempo = yolo_detection_images.result(session.get("lastImage"))
        goAhead=True

        #Salvataggio degli oggetti presenti nell'immagine in una lista e conteggio elementi per ogni classe di oggetti
        objects = []
        for elem in obj:
            objects.append(elem[0])
        objects = {i:objects.count(i) for i in objects}
        obj_count = []
        obj_count = [(k, v) for k, v in objects.items()]
    return render_template("image.html", filename = session.get("lastImage"), oggetti=obj, ogg_count=obj_count, tempo = tempo, qualità=session.get("quality"))

#Invio al client dell'immagine elaborata
@app.route('/image/<filename>')
def send_image(filename):
    global goAhead
    goAhead=True
    return send_from_directory("images", filename)

#############   Video   #############
#Visualizzazione pagina video.html
@app.route("/video")
def video():
    return render_template("video.html")

#Metodo richiamato quando si carica un video sul server
@app.route("/video", methods=["POST"])
def upload_video():
    check_session()
    
    #Creazione cartella ./videos se non presente
    target = os.path.join(APP_ROOT, 'videos/')
    check_target(target)

    #Salvataggio video caricato dall'utente nella cartella ./videos
    for upload in request.files.getlist("file"):
        listVideo = os.listdir(APP_ROOT+"/videos")
        print("Il file caricato è {}".format(upload.filename))
        filename = upload.filename
        estensione = filename[-3:]  #Prelievo estensione video utente
        filename = session.get("user") +"."+ estensione #Rinominazione video caricato dall'utente con il nome della sessione corrente (per utilizzo multi-utente contemporaneamente)
        
        #Sovrascrivere l'ultimo video caricato da un utente (se presente)  
        if filename in listVideo:
            os.remove(APP_ROOT+"/videos/"+filename)
        session["lastVideo"] = filename 
        destination = "/".join([target, filename])
        #Salvataggio video nella cartella ./videos
        upload.save(destination)

        #Numero di frame del video. Se num_frame <= 200, il video di output viene salvato.
        vs = cv2.VideoCapture(APP_ROOT+'/videos/'+session.get("lastVideo"))
        fps = vs.get(cv2.CAP_PROP_FPS)
        try:
            prop = cv2.CAP_PROP_FRAME_COUNT if imutils.is_cv2() else cv2.CAP_PROP_FRAME_COUNT
            total = int(vs.get(prop))
            print(f"[INFO] {total} frames in the video")

	    # if error occurs print
        except:
            print(f"[INFO] {total} frames in the video")
            total = -1
        vs.release()
        if(total < 200):
            oggetti = []
            obj = yolo_detection_videos.detectObjectsSaveVideo(session.get("lastVideo"))
            for i in obj: 
                if i not in oggetti: 
                    oggetti.append(i) 
            return render_template("video.html", filename=session.get("lastVideo"), type="video", oggetti=oggetti)

    return render_template("video.html", filename=session.get("lastVideo"), type="immagini")

#Invio al client del video elaborato
@app.route('/video/<filename>')
def send_video(filename):
    return send_from_directory("videos", '00'+filename)


#############   Video YouTube   #############
#Visualizzazione pagina YTvideo.html
@app.route("/YouTubeVideo")
def YTvideo():
    return render_template("YTvideo.html")

#Metodo richiamato quando l'utente invia al server il link al video di youtube
@app.route("/YouTubeVideo", methods=["POST"])
def link_video():
    check_session()

    url = request.form.get('url')
    try:
        video = pafy.new(url)
        titolo = video.title
    except:
        titolo = "Error"
    session["url"] = url
    return render_template("YTvideo.html", filename=session.get("url"), titolo=titolo)


#############   Webcam   #############
#Visualizzazione della pagina webcam.html e invio delle informazioni relative alle webcam disponibili
@app.route("/Webcam")
def webcam():
    check_session()

    #Controllo webcam disponibili
    valid_cams = []
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap is None or not cap.isOpened():
            print('Warning: unable to open video source: ', i)
        else:
            valid_cams.append(i)
        cap.release()

    session["webcams"] = valid_cams
    session["webcam"] = ""
    return render_template("webcam.html", webcam=session.get("webcam") , webcams=session.get("webcams"))

#Metodo richiamato quando l'utente seleziona la webcam desiderata
@app.route("/Webcam", methods=["POST"])
def select_webcam():
    check_session()

    webcam = request.form.get('selectedWebcam')
    session["webcam"] = webcam
    
    return render_template("webcam.html", webcam=session.get("webcam"), webcams=session.get("webcams"))


@app.route('/video_feed/<filename>')
def video_feed(filename):
    if(filename == "link"):
        return Response(yolo_detection_videos.findVideoObjects("link", session.get("url")),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    elif(filename=="webcam"):
        return Response(yolo_detection_videos.findVideoObjects("webcam", session.get("webcam")),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(yolo_detection_videos.findVideoObjects("video", filename),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

#############   Webcam Client   #############
#Visualizzazione della pagine WebcamClient
@app.route("/WebcamClient")
def webcamClient():
    return render_template("webcamClient.html")

#Metodo richiamato quando l'utente scatta una foto o registra un video
@app.route("/WebcamClient", methods=["POST"])
def upload_data():
    global goAhead2
    while goAhead2==False:
        time.sleep(3)
    goAhead2 = False

    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    check_session()

    if(len(request.files.getlist("image")) > 0):  #L'utente ha scattato una foto?
        #Creazione cartella ./images se non presente
        target = os.path.join(APP_ROOT, 'images/')
        check_target(target)

        for upload in request.files.getlist("image"):
            listImmagini = os.listdir(APP_ROOT+"/images")
            print("Il file caricato è {}".format(upload.filename))
            filename = upload.filename
            estensione = os.path.splitext(filename)[1] #Prelievo estensione immagine utente
            filename = session.get("user") + estensione #Rinominazione immagine caricata dall'utente con il nome della sessione corrente (per utilizzo multi-utente contemporaneamente)
            
            #Sovrascrivere l'ultima immagine caricata da un utente (se presente)  
            if filename in listImmagini:
                os.remove(APP_ROOT+"/images/"+filename)
            session["lastImage"] = filename
            destination = "/".join([target, filename])
            #Salvataggio immagine nella cartella ./images
            upload.save(destination)
    
        obj, tempo = yolo_detection_images.result(session.get("lastImage"))
        jsonResp = {'filename': filename, 'oggetti': obj}
        goAhead2=True
           
    elif(len(request.files.getlist("video")) > 0):  #L'utente ha registrato un video?
        #Creazione cartella ./videos se non presente
        target = os.path.join(APP_ROOT, 'videos/')
        check_target(target)

        for upload in request.files.getlist("video"):
            listVideo = os.listdir(APP_ROOT+"/videos")
            print("Il file caricato è {}".format(upload.filename))
            filename = upload.filename
            estensione = os.path.splitext(filename)[1] #Prelievo estensione video utente
            filename = session.get("user") + estensione #Rinominazione video caricato dall'utente con il nome della sessione corrente (per utilizzo multi-utente contemporaneamente)
            
            #Sovrascrivere l'ultimo video caricato da un utente (se presente)  
            if filename in listVideo:
                os.remove(APP_ROOT+"/videos/"+filename)
            session["lastVideo"] = filename
            destination = "/".join([target, filename])
            #Salvataggio video nella cartella ./videos
            upload.save(destination)
        
        obj = yolo_detection_videos.detectObjectsSaveVideo(session.get("lastVideo"))
        jsonResp = {'filename': filename}
        goAhead2=True

    return jsonify(jsonResp)

#Invio al client dell'immagine elaborata
@app.route('/WebcamClient/<filename>')
def send_image_webcam(filename):
    global goAhead2
    goAhead2=True
    return send_from_directory("images", filename)

#Funzione per agire sulla cache
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

#Funzione per generare id casuale utente
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

#Controllo sessione dell'utente
def check_session():
    if not session.get('user') is None:
        print("Sessione già creata per l'utente")
    else:
        print("Nuovo Utente, creazione sessione")
        session["user"] = id_generator(10)

#Creazione cartella target se non presente
def check_target(target):
    if not os.path.isdir(target):
        os.mkdir(target)

#Funzioni richiamate al momento della creazione del Server
if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(host='0.0.0.0', port=4555, debug=True, threaded=True)
