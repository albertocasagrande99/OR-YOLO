FROM python:3.8.0-buster

#Make a directory for our application
WORKDIR /app

#Install dependences
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

COPY /app .

CMD ["python3", "app.py"]



#Comando da usare per build: docker build -t dockerpython .
#Comando per run: docker run -p 4555:4555 dockerpython