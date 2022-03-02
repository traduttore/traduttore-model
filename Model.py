from sklearn.metrics import multilabel_confusion_matrix, accuracy_score
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.models import Sequential
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
import tensorflow as tf

import numpy as np
import os
from matplotlib import pyplot as plt
from gestures import actions

# Path for exported data, numpy arrays
DATA_PATH = os.path.join('MP_Data')

# Videos are going to be 30 frames in lengh
sequence_length = 20

label_map = {label: num for num, label in enumerate(actions)}

sequences, labels = [], []
for action in actions:
    folder_path = os.path.join(DATA_PATH, action)
    len_data = len(os.listdir(folder_path))
    print(action)
    print(len_data)
    for sequence in range(len_data):
        window = []
        for frame_num in range(sequence_length):
            res = np.load(os.path.join(DATA_PATH, action, str(
                sequence), "{}.npy".format(frame_num)))
            window.append(res)
        sequences.append(window)
        labels.append(label_map[action])

X = np.array(sequences)
y = to_categorical(labels).astype(int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.10)

model = Sequential()
model.add(LSTM(64, return_sequences=True,
          activation='relu', input_shape=(20, 258)))
model.add(LSTM(128, return_sequences=True, activation='relu'))
model.add(LSTM(64, return_sequences=False, activation='relu'))
model.add(Dense(64, activation='relu'))
model.add(Dense(32, activation='relu'))
model.add(Dense(actions.shape[0], activation='softmax'))

model.compile(optimizer='Adam', loss='categorical_crossentropy',
              metrics=['categorical_accuracy'])
model.fit(X_train, y_train, epochs=500)

model.save('action')
converter = tf.lite.TFLiteConverter.from_saved_model('action')
tflite_model = converter.convert()

with open('model.tflite', 'wb') as f:
    f.write(tflite_model)