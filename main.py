from run_translation.TestModelComputer import asl_translation
from run_translation.TextToSpeech import tts
from run_translation.RunPiModel import rasp_translation
# from run_translation.SpeechToText import stt

if __name__ == "__main__":
    sentence = asl_translation()
    # rasp_sentence = rasp_translation()
    tts(sentence)
    # print(stt())