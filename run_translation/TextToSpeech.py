from gtts import gTTS
import os
import playsound


def tts(text):
    tts = gTTS(text=text, lang='en')

    filename = "tempfile.mp3"
    tts.save(filename)
    playsound.playsound(filename)
    os.remove(filename)
