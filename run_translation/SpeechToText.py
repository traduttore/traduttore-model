import speech_recognition as sr
import pyaudio
import time

recognizer = sr.Recognizer()
microphone = sr.Microphone()

def stt():
    response = ""
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        response = recognizer.recognize_google(audio)
    except:
        response = "I didn't catch that"
    return response
