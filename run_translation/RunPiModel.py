import cv2
import numpy as np
import mediapipe as mp
# from tensorflow.keras.models import load_model
from timeit import default_timer as timer
import tflite_runtime.interpreter as tflite
# import pyttsx3
import time
from gestures import actions
from gestures import letters

mp_holistic = mp.solutions.holistic  # Holistic model

def mediapipe_detection(image, model):
    # COLOR CONVERSION BGR 2 RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False                  # Image is no longer writeable
    results = model.process(image)                 # Make prediction
    image.flags.writeable = True                   # Image is now writeable
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # COLOR COVERSION RGBß 2 BGR
    return image, results

def extract_keypoints(results):
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten(
    ) if results.pose_landmarks else np.zeros(33*4)
    lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten(
    ) if results.left_hand_landmarks else np.zeros(21*3)
    rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten(
    ) if results.right_hand_landmarks else np.zeros(21*3)
    return np.concatenate([pose, lh, rh])

# 1. New detection variables
words = actions
MODEL_PATH = 'model2.tflite'

interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

threshold = 0.97

# hand_in_screen = True

# model = load_model('action')

def model_predict(data, interpreter, input_details, output_details):
    inp = data.astype('float32')
    interpreter.set_tensor(input_details[0]['index'], inp)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data

def rasp_translation():
    hand_in_screen = True
    sequence = []
    sentence = []
    start = None
    hand_count = 0
    cap = cv2.VideoCapture(1)
    holistic_def = mp_holistic.Holistic(
        min_detection_confidence=0.5, min_tracking_confidence=0.5)
    while cap.isOpened():
        # Read feed
        ret, frame = cap.read()

        # Make detections
        image, results = mediapipe_detection(frame, holistic_def)
        
        # 2. Prediction logic
        keypoints = extract_keypoints(results)

        sequence.append(keypoints)
        sequence = sequence[-20:]
        
        if len(sequence) == 20:
            res = model_predict(np.expand_dims(sequence, axis=0), interpreter, input_details, output_details)[0]
            
        # 3. Viz logic
            if res[np.argmax(res)] > threshold: 
                if words[np.argmax(res)] == '-':
                    # print("its getting do nothing")
                    if start:
                        elapsed = timer() - start
                        # print(elapsed)
                        # if elapsed>2:
                        #     return "STOP_RECORDING"
                    else:
                        start = timer()
                elif start:
                    start = None
                else:
                    sentence.append(words[np.argmax(res)])
                    output_sentence = (' '.join(sentence)).replace('-', ' ')
                    # print(output_sentence)
                    return output_sentence
        try:
            y_coordinate_left_hand = results.pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_INDEX].y
            y_coordinate_right_hand = results.pose_landmarks.landmark[mp_holistic.PoseLandmark.RIGHT_INDEX].y
            if (y_coordinate_right_hand or y_coordinate_left_hand) \
                and not (0.15 < y_coordinate_left_hand < 0.9) \
                and not (0.15 < y_coordinate_right_hand < 0.9):
                output_sentence = "Please make sure the hand is within frame."
                hand_in_screen = False
            else:
                hand_in_screen = True
        except:
            pass
        print(hand_count)
        if not hand_in_screen:
            hand_count = hand_count + 1
            if hand_count > 10:
                return "STOP_RECORDING"
        else:
            hand_count = 0
        # if not hand_in_screen:
        #     cv2.putText(image, output_sentence, (3,30), 
        #                     cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        #     cv2.imshow('OpenCV Feed', image)
        # else:
        #     cv2.destroyAllWindows()

        # Break gracefully
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    sentence = rasp_translation()
    # print(sentence)