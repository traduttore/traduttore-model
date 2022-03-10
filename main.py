from run_translation.TestModelComputer import asl_translation
from run_translation.TextToSpeech import tts
from run_translation.RunPiModelStream import rasp_translation
# from run_translation.RunPiModelTesting import rasp_translation
from run_translation.TestModelComputerLetters import asl_translation_letters
# from run_translation.SpeechToText import stt

if __name__ == "__main__":
    # sentence = rasp_translation()
    sentence = asl_translation(CAM_ID=1)
    # rasp_sentence = rasp_translation([])
    # tts(sentence)
    # print(stt())