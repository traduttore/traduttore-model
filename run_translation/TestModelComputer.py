import cv2
import numpy as np
import mediapipe as mp
# from tensorflow.keras.models import load_model
from timeit import default_timer as timer
import tflite_runtime.interpreter as tflite
import time
from gestures import actions
from gestures import letters
from CvFpsCalc import CvFpsCalc

mp_holistic = mp.solutions.holistic  # Holistic model
mp_drawing = mp.solutions.drawing_utils  # Drawing utilities

def mediapipe_detection(image, model):
    # COLOR CONVERSION BGR 2 RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False                  # Image is no longer writeable
    results = model.process(image)                 # Make prediction
    image.flags.writeable = True                   # Image is now writeable
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # COLOR COVERSION RGBß 2 BGR
    return image, results


def draw_landmarks(image, results):
    mp_drawing.draw_landmarks(image, results.pose_landmarks,
                              mp_holistic.POSE_CONNECTIONS)  # Draw pose connections
    mp_drawing.draw_landmarks(image, results.left_hand_landmarks,
                              mp_holistic.HAND_CONNECTIONS)  # Draw left hand connections
    mp_drawing.draw_landmarks(image, results.right_hand_landmarks,
                              mp_holistic.HAND_CONNECTIONS)  # Draw right hand connections


def draw_styled_landmarks(image, results):
    # Draw pose connections
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                              mp_drawing.DrawingSpec(
                                  color=(80, 22, 10), thickness=2, circle_radius=4),
                              mp_drawing.DrawingSpec(
                                  color=(80, 44, 121), thickness=2, circle_radius=2)
                              )
    # Draw left hand connections
    mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                              mp_drawing.DrawingSpec(
                                  color=(121, 22, 76), thickness=2, circle_radius=4),
                              mp_drawing.DrawingSpec(
                                  color=(121, 44, 250), thickness=2, circle_radius=2)
                              )
    # Draw right hand connections
    mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                              mp_drawing.DrawingSpec(
                                  color=(245, 117, 66), thickness=2, circle_radius=4),
                              mp_drawing.DrawingSpec(
                                  color=(245, 66, 230), thickness=2, circle_radius=2)
                              )

def extract_keypoints(results):
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten(
    ) if results.pose_landmarks else np.zeros(33*4)
    lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten(
    ) if results.left_hand_landmarks else np.zeros(21*3)
    rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten(
    ) if results.right_hand_landmarks else np.zeros(21*3)
    return np.concatenate([pose, lh, rh])


def prob_viz(res, words, input_frame, colors):
    output_frame = input_frame.copy()
    for num, prob in enumerate(res):
        cv2.rectangle(output_frame, (0, 60+num*30),
                      (int(prob*100), 90+num*30), colors[num], -1)
        cv2.putText(output_frame, words[num], (0, 85+num*30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    return output_frame
# 1. New detection variables
words = actions
MODEL_PATH = 'model.tflite'

interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

threshold = 0.97

colors = [(245, 117, 16)]

def model_predict(data):
    inp = data.astype('float32')
    interpreter.set_tensor(input_details[0]['index'], inp)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data
#model = tf.keras.models.load_model('actions')

def asl_translation(CAM_ID=1):
    sequence = []
    sentence = []
    start = None
    cap = cv2.VideoCapture(CAM_ID)
    # cap = cv2.VideoCapture('http://172.20.10.6:8080/?action=stream')
    cvFpsCalc = CvFpsCalc(buffer_len=10)
    # Set mediapipe model 
    # holistic_def = mp_holistic.Holistic(
    #     min_detection_confidence=0.5, min_tracking_confidence=0.5)
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while cap.isOpened():
            display_fps = cvFpsCalc.get()
            print(display_fps)
            # Read feed
            ret, frame = cap.read()

            # Make detections
            image, results = mediapipe_detection(frame, holistic)
            
            # Draw landmarks
            draw_styled_landmarks(image, results)
            
            # 2. Prediction logic
            keypoints = extract_keypoints(results)

            # sequence.insert(0,keypoints)
            # sequence = sequence[:30]
            sequence.append(keypoints)
            sequence = sequence[-20:]
            
            if len(sequence) == 20:
                res = model_predict(np.expand_dims(sequence, axis=0))[0]
                
            # 3. Viz logic
                print(res[np.argmax(res)])
                if res[np.argmax(res)] > threshold: 
                    if words[np.argmax(res)] == '-':
                        if start:
                            elapsed = timer() - start
                            if elapsed>10:
                                cap.release()
                                cv2.destroyAllWindows()
                                return (' '.join(sentence)).replace('-', ' ')
                        else:
                            start = timer()
                    elif start:
                        start = None
                    else:
                        if len(sentence) > 0:
                            if words[np.argmax(res)] != sentence[-1]:
                                sentence.append(words[np.argmax(res)])
                        else:
                            sentence.append(words[np.argmax(res)])

                if len(sentence) > 7: 
                    sentence = []

                # Viz probabilities
                image = prob_viz(res, words, image, colors*(words.size))
                
            cv2.rectangle(image, (0,0), (4000, 40), (245, 117, 16), -1)
            output_sentence = (' '.join(sentence)).replace('-', ' ')
            print(output_sentence)
            try:
                y_coordinate_left_hand = results.pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_INDEX].y
                y_coordinate_right_hand = results.pose_landmarks.landmark[mp_holistic.PoseLandmark.RIGHT_INDEX].y
                if (y_coordinate_right_hand or y_coordinate_left_hand) \
                    and not (0.15 < y_coordinate_left_hand < 0.9) \
                    and not (0.15 < y_coordinate_right_hand < 0.9):
                    output_sentence = "Please make sure the hand is within frame."
            except:
                pass
            cv2.putText(image, output_sentence, (3,30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            # Show to screen
            cv2.imshow('OpenCV Feed', image)

            # Break gracefully
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    sentence = asl_translation()
    print(sentence)
