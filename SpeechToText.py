import speech_recognition as sr
import pyaudio
import time

recognizer = sr.Recognizer()
microphone = sr.Microphone()

for i in range(5):
    print("speak")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        response = recognizer.recognize_google(audio)
    except:
        print("I didn't catch that")

    print(response)
    time.sleep(2)
