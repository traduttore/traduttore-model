from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from timeit import default_timer as timer
from threading import Thread, Event

from run_translation.SpeechToText import stt
from run_translation.RunPiModel import rasp_translation
from run_translation.TextToSpeech import tts

import cv2
import os

root = Builder.load_string('''
#:import RGBA kivy.utils.rgba

<GUI>:
    FloatLayout:
        BoxLayout:
            size_hint: 1, 0.05
            pos_hint: {'top': 1, 'x': 0}
            Button:
                text: 'Traduttore'
                size_hint: 0.8, 1
                pos_hint: {'top': 1, 'x': 0}
            Button:
                id: pause_controller
                text: 'Pause'
                on_press:
                    button_text = pause_controller.text
                    pause_controller.text = 'Resume' if button_text == 'Pause' and controller.text == 'Clear' else 'Pause'
                    app.pause() if button_text == 'Pause' else app.resume()
                size_hint: 0.1, 1
                pos_hint: {'top': 1, 'x': 1}
            Button:
                id: controller
                text: 'Start'
                on_press:
                    button_text = controller.text
                    controller.text = 'Start' if button_text == 'Clear' else 'Clear'
                    camera_module.opacity = 1 if button_text == 'Clear' else 0
                    camera.play = True if button_text == 'Clear' else False
                    pause_controller.text = 'Pause'
                    app.start() if button_text == 'Start' else app.reset()
                size_hint: 0.1, 1
                pos_hint: {'top': 1, 'x': 1}
        FloatLayout:
            size_hint: 1, 0.9 
            BoxLayout:
                pos_hint: {'bottom': 1, 'x': 0}
                orientation: 'vertical'
                padding: dp(5), dp(5)
                RecycleView:
                    id: rv
                    data: app.messages
                    viewclass: 'Message'
                    do_scroll_x: False

                    RecycleBoxLayout:
                        id: box
                        orientation: 'vertical'
                        size_hint_y: None
                        size: self.minimum_size
                        default_size_hint: 1, None
                        # magic value for the default height of the message
                        default_size: 0, 38
                        key_size: '_size'

                FloatLayout:
                    size_hint_y: None
                    height: 0
                    Button:
                        size_hint_y: None
                        height: self.texture_size[1]
                        opacity: 0 if not self.height else 1
                        text:
                            (
                            'go to last message'
                            if rv.height < box.height and rv.scroll_y > 0 else
                            ''
                            )
                        pos_hint: {'pos': (0, 0)}
                        on_release: app.scroll_bottom()
        BoxLayout:
            id: camera_module
            orientation: 'vertical'
            Label:
                text: "Press start once positioned in frame"
                size_hint_y: 0.2
                font_size: '30sp'
                color: 'green'
            Camera:
                id: camera
                resolution: (640, 480)
                play: True
        BoxLayout:
            size_hint: 1, 0.05
            pos_hint: {'bottom': 1, 'x': 0}
            Button:
                text: str(len(app.messages))
                size_hint: 0.7, 1
                pos_hint: {'top': 1, 'x': 0}
            Button:
                text: 'Delete'
                size_hint: 0.1, 1
                pos_hint: {'top': 1, 'x': 1}
                on_press: app.delete()
            ToggleButton:
                text: 'Text'
                group: 'model'
                size_hint: 0.1, 1
                pos_hint: {'top': 1, 'x': 1}
                on_press: app.modeloff()
            ToggleButton:
                text: 'Letters'
                group: 'model'
                size_hint: 0.1, 1
                pos_hint: {'top': 1, 'x': 1}
                on_press: app.modelon()

<Message@FloatLayout>:
    message_id: -1
    bg_color: '#223344'
    side: 'right'
    text: '...'
    size_hint_y: None
    _size: 38, 38
    size: self._size
    text_size: None, None
    opacity: min(1, self._size[0])

    Label:
        text: root.text
        padding: 10, 10
        size_hint: None, 1
        size: self.texture_size
        text_size: root.text_size

        on_texture_size:
            app.update_message_size(
            root.message_id,
            self.texture_size,
            root.width,
            )

        pos_hint:
            (
            {'x': 0, 'center_y': .5}
            if root.side == 'left' else
            {'right': 1, 'center_y': .5}
            )

        canvas.before:
            Color:
                rgba: RGBA(root.bg_color)
            RoundedRectangle:
                size: self.texture_size
                radius: dp(5), dp(5), dp(5), dp(5)
                pos: self.pos

        canvas.after:
            Color:
            Line:
                rounded_rectangle: self.pos + self.texture_size + [dp(5)]
                width: 1.01
''')

class Object(object):
    pass

class GUI(BoxLayout):
    pass

class MessengerApp(App):
    messages = ListProperty([])
    thread = Thread()
    stop_event = True

    def build(self):
        # self.configure_position()
        self.thread = Thread(target=self.word_builder)
        return GUI()

    def create_obj(self, value):
        a = Object()
        a.text = value
        return a

    def word_builder(self):
        while(1):
            if not self.stop_event:
                if len(self.messages) and self.messages[-1]['side'] == 'left' and self.messages[-1]['text'] == '...':
                    if not self.messages[-2]['text'] in ['...', '', ' ']:
                        tts(self.messages[-2]['text'])
                    spoken = stt()
                    if not self.stop_event:
                        if spoken != "I_DIDNT_CATCH_THAT":
                            self.messages[-1] = {
                                        **self.messages[-1],
                                        'text': spoken,
                                        'last_word': spoken,
                                    }
                        self.send_message(self.create_obj('-'), '')
                else:
                    word = rasp_translation()
                    if not self.stop_event:
                        if word == "STOP_RECORDING":
                            self.response('-')
                        else:
                            if len(self.messages):
                                message = self.messages[-1]
                                if message['last_word'] != word: 
                                    self.messages[-1] = {
                                        **self.messages[-1],
                                        'text': (message['text'] if message['text'] != '...' else '') + ' ' + word,
                                        'last_word': word,
                                    }
                            else:
                                self.send_message(self.create_obj(word + ' '), word)

    def delete(self):
        print('delete')
        if len(self.messages) and self.messages[-1]['side'] == 'right' and self.messages[-1]['last_word'] != '':
            message = self.messages[-1]
            sentence_arr = self.messages[-1]['text'].split(' ')
            last_word = sentence_arr[-1]
            text = ' '.join(sentence_arr[:-1]) if message['text'] != '...' else '...'
            if text == '':
                self.messages[-1] = {
                    **self.messages[-1],
                    'text': '...',
                    'last_word': '...',
                }
            else:
                self.messages[-1] = {
                    **self.messages[-1],
                    'text': text,
                    'last_word': last_word,
                }


    def reset(self):
        print('reset')
        self.messages = []
        self.stop_event = True

    def pause(self):
        print('pause')
        self.stop_event = True

    def resume(self):
        print('resume')
        self.stop_event = False

    def start(self):
        print('start')
        self.stop_event = False
        self.send_message(self.create_obj('...'), '...')
        if not self.thread.is_alive():
            self.thread.start()
        print(self.thread.is_alive())

    def modeloff(self):
        print('modeloff')

    def modelon(self):
        print('modelon')

    def configure_position(self):
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, image = cap.read()
            cv2.imshow('OpenCV Feed', image)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()


    def add_message(self, text, side, color, last_word):
        self.messages.append({
            'message_id': len(self.messages),
            'text': '...' if text == '-' else text,
            'side': side,
            'bg_color': color,
            'text_size': [None, None],
            'last_word': last_word,
        })

    def update_message_size(self, message_id, texture_size, max_width):
        if max_width == 0:
            return

        one_line = dp(50)

        if texture_size[0] >= max_width * 2 / 3:
            self.messages[message_id] = {
                **self.messages[message_id],
                'text_size': (max_width * 2 / 3, None),
            }
        elif texture_size[0] < max_width * 2 / 3 and texture_size[1] > one_line:
            self.messages[message_id] = {
                **self.messages[message_id],
                'text_size': (max_width * 2 / 3, None),
                '_size': texture_size,
            }
        else:
            self.messages[message_id] = {
                **self.messages[message_id],
                '_size': texture_size,
            }

    def send_message(self, textinput, last_word):
        text = textinput.text
        if text != '':
            self.add_message(text, 'right', '#223344', last_word)

    def response(self, text):
        self.add_message(text, 'left', '#332211', '')


if __name__ == '__main__':
    MessengerApp().run()
    os._exit(1)