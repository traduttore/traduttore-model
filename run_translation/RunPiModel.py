import cv2
import numpy as np
import mediapipe as mp
# from tensorflow.keras.models import load_model
from timeit import default_timer as timer
import tflite_runtime.interpreter as tflite
# import pyttsx3
import time
from gestures import actions

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


def prob_viz(res, actions, input_frame, colors):
    output_frame = input_frame.copy()
    for num, prob in enumerate(res):
        cv2.rectangle(output_frame, (0,60+num*40), (int(prob*100), 90+num*40), colors[num], -1)
        cv2.putText(output_frame, actions[num], (0, 85+num*40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        
    return output_frame

# 1. New detection variables

threshold = 0.9

colors = [(245, 117, 16)]*(actions.size)
# hand_in_screen = True

# model = load_model('action')
interpreter = tflite.Interpreter(model_path='model.tflite')
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def model_predict(data):
    inp = data.astype('float32')
    interpreter.set_tensor(input_details[0]['index'], inp)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data

def rasp_translation():
    sequence = []
    sentence = []
    start = None
    cap = cv2.VideoCapture(0)
    holistic_def = mp_holistic.Holistic(
        min_detection_confidence=0.5, min_tracking_confidence=0.5)
    # Set mediapipe model 
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
            res = model_predict(np.expand_dims(sequence, axis=0))[0]
            
        # 3. Viz logic
            if res[np.argmax(res)] > threshold: 
                if actions[np.argmax(res)] == '-':
                    if start:
                        elapsed = timer() - start
                        if elapsed>5:
                            return "STOP_RECORDING"
                    else:
                        start = timer()
                elif start:
                    start = None
                else:
                    sentence.append(actions[np.argmax(res)])
                    output_sentence = (' '.join(sentence)).replace('-', ' ')
                    print(output_sentence)
                    return output_sentence
        # try:
        #     y_coordinate_left_hand = results.pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_INDEX].y
        #     y_coordinate_right_hand = results.pose_landmarks.landmark[mp_holistic.PoseLandmark.RIGHT_INDEX].y
        #     if (y_coordinate_right_hand or y_coordinate_left_hand) \
        #         and not (0.15 < y_coordinate_left_hand < 0.9) \
        #         and not (0.15 < y_coordinate_right_hand < 0.9):
        #         output_sentence = "Please make sure the hand is within frame."
        #         hand_in_screen = False
        #     else:
        #         hand_in_screen = True
        # except:
        #     pass
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
    print(sentence)