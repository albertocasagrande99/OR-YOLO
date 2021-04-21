# Remote image/video recognition using YOLO
<p align="center"><img src="/app/static/assets/images/logo-2.svg" width="30%"></p>
Progetto riguardante lo sviluppo di un'architettura client / server per il riconoscimento di oggetti all'interno di immagini e video, utilizzando YOLO.

## Istruzioni
Per testare l'applicazione (creando un server locale nella propria macchina) è necessario avere installato python sul proprio terminale. 
Inoltre è necessario installare le seguenti librerie che non sono comprese nella libreria standard di Python.
- imutils
- flask
- openCV
- numpy
- pillow
- pafy
- youtube_dl

Dopo aver scaricato lo zip da GitHub e averlo decompresso, per installare le librerie è sufficiente eseguire sul proprio terminale il comando `pip install -r requirements.txt` dopo essersi posizionati nel percorso della cartella decompressa.

Infine, per eseguire l'applicativo da terminale, bisogna digitare il comando `python3 app.py` dopo essersi posizionati all'interno della cartella `app`. 
Una volta fatta partire l'applicazione, è possibile accedervi semplicemente usando un browser, mediante l'indirizzo `localhost:4555`.

**N.B. All'interno di questa repository non è presente il file dei weights, che deve essere scaricato manualmente mediante il [link](https://pjreddie.com/media/files/yolov3.weights). Il file scaricato deve successivamente essere salvato all'interno della cartella `cfg` con il nome di `yolov3.weights`.**

### Come creare un ambiente virtuale
Qualora non si volessero installare le librerie direttamente sul proprio terminale c'è la possibilità di creare un ambiente 
virtuale, ossia uno spazio indipendente dal resto del sistema in cui è possibile testare e lavorare con Python e pip.

E' sufficiente eseguire i seguenti comandi all'interno del terminale:
```
$ cd OR-YOLO
$ python3 -m venv venv
```

Windows:
`$ py -3 -m venv venv`

Una volta creato l'ambiente virtuale, basterà attiavarlo mediante il comando:
```
$ . venv/bin/activate
```

Windows: `> venv\Scripts\activate`

Dopo aver attivato l'ambiente virtuale, digitando il comando `pip install -r requirements.txt` vengono installate le librerie necessarie.
