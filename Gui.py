from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from timeit import default_timer as timer

from run_translation.SpeechToText import stt
from run_translation.RunPiModel import rasp_translation
import cv2

root = Builder.load_string('''
#:import RGBA kivy.utils.rgba

<GUI>:
    FloatLayout:
        Button:
            text: 'Traduttore'
            size_hint: 1, 0.1
            pos_hint: {'top': 1, 'x': 0}
        BoxLayout:
            pos_hint: {'bottom': 1, 'x': 0}
            size_hint: 1, 0.9
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

<Message@FloatLayout>:
    message_id: -1
    bg_color: '#223344'
    side: 'left'
    text: ''
    size_hint_y: None
    _size: 0, 0
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
    messages = ListProperty([{
                                'message_id': 0,
                                'text': '',
                                'side': 'right',
                                'bg_color': '#223344',
                                'text_size': [None, None],
                                'last_word': '',
                            }])

    def build(self):
        self.initiate_model()
        return GUI()

    def create_obj(self, value):
        a = Object()
        a.text = value
        return a

    def word_builder(self, dt):
        if Clock.frames_displayed != 0:
            if len(self.messages) and self.messages[-1]['side'] == 'left' and self.messages[-1]['text'] == '...':
                spoken = stt()
                if spoken != "I_DIDNT_CATCH_THAT":
                    self.messages[-1] = {
                                'message_id': self.messages[-1]['message_id'],
                                'text': spoken,
                                'side': self.messages[-1]['side'],
                                'bg_color': self.messages[-1]['bg_color'],
                                'text_size': self.messages[-1]['text_size'],
                                'last_word': spoken,
                            }
                self.send_message(self.create_obj('-'), '')
            else:
                word = rasp_translation()
                if word == "STOP_RECORDING":
                    self.response('-')
                else:
                    if len(self.messages):
                        message = self.messages[-1]
                        if message['last_word'] != word: 
                            self.messages[-1] = {
                                'message_id': message['message_id'],
                                'text': (message['text'] if message['text'] != '...' else '') + word + ' ',
                                'side': message['side'],
                                'bg_color': message['bg_color'],
                                'text_size': message['text_size'],
                                'last_word': word,
                            }
                    else:
                        self.send_message(self.create_obj(word + ' '), word)

    def initiate_model(self):
        # func = lambda dt: print(dt)        
        self.configure_position()
        Clock.schedule_interval(self.word_builder, 1)

    def configure_position(self):
        cap = cv2.VideoCapture(1)
        while cap.isOpened():
            ret, image = cap.read()
            cv2.imshow('OpenCV Feed', image)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()


    def add_message(self, text, side, color, last_word):
        # create a message for the recycleview
        self.messages.append({
            'message_id': len(self.messages),
            'text': '...' if text == '-' else text,
            'side': side,
            'bg_color': color,
            'text_size': [None, None],
            'last_word': last_word,
        })

    def update_message_size(self, message_id, texture_size, max_width):
        # when the label is updated, we want to make sure the displayed size is
        # proper
        if max_width == 0:
            return

        one_line = dp(50)  # a bit of  hack, YMMV

        # if the texture is too big, limit its size
        if texture_size[0] >= max_width * 2 / 3:
            self.messages[message_id] = {
                **self.messages[message_id],
                'text_size': (max_width * 2 / 3, None),
            }

        # if it was limited, but is now too small to be limited, raise the limit
        elif texture_size[0] < max_width * 2 / 3 and \
                texture_size[1] > one_line:
            self.messages[message_id] = {
                **self.messages[message_id],
                'text_size': (max_width * 2 / 3, None),
                '_size': texture_size,
            }

        # just set the size
        else:
            self.messages[message_id] = {
                **self.messages[message_id],
                '_size': texture_size,
            }

    def send_message(self, textinput, last_word):
        text = textinput.text
        if text != '':
            self.add_message(text, 'right', '#223344', last_word)

    def response(self, text, *args):
        self.add_message(text, 'left', '#332211', '')


if __name__ == '__main__':
    MessengerApp().run()