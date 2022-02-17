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
    # try:
        response = recognizer.recognize_google(audio)
    # except:
    #     response = "I didn't catch that"
    return response

print(stt())
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for Microphone(device_index={0})".format(
        index, name))