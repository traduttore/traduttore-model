import pyttsx3

def tts(sentence):
    engine = pyttsx3.init()
    engine.say(sentence)
    engine.runAndWait()
