from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.properties import StringProperty


root = Builder.load_string('''
<GUI>:
    BoxLayout:
        orientation: 'vertical'

        Image:
            source: 'trad-icon.ico'
            halign: 'left'

        Label:
            text: '[b]Your ASL to Text Translation[/b]'
            font_size: '26sp'
            markup: True

        Label:
            text_size: self.width, None
            halign: 'center'
            valign: 'top'
            font_size: '16sp'
            text: app.asl_to_english

        Label:
            text: '[b]Employee Speech to Text Translation[/b]'
            font_size: '26sp'
            markup: True

        Label:
            text_size: self.width, None
            halign: 'center'
            valign: 'top'
            font_size: '16sp'
            text: app.speech_to_english

''')

class GUI(BoxLayout):
    pass

class MainApp(App):
    asl_to_english = StringProperty("")
    speech_to_english = StringProperty("")

    def build(self):
        self.asl_to_english_text()
        self.speech_to_english_text()
        return GUI()

    def asl_to_english_text(self):
        self.asl_to_english = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' \
                    'Etiam vestibulum quis sem et congue. Etiam nec congue ' \
                    'elit, ac consectetur felis. Maecenas sit amet vulputate mi.' \
                    'Donec sit amet luctus lectus. Duis arcu odio, dictum quis ' \
                    'arcu non, lacinia commodo ipsum. Sed dapibus, massa ac ' \
                    'lobortis auctor, est libero pretium est, id elementum magna ' \
                    'arcu in tellus. '

    def speech_to_english_text(self):
        self.speech_to_english = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' \
                    'Etiam vestibulum quis sem et congue. Etiam nec congue ' \
                    'elit, ac consectetur felis. Maecenas sit amet vulputate mi.' \
                    'Donec sit amet luctus lectus. Duis arcu odio, dictum quis ' \
                    'arcu non, lacinia commodo ipsum. Sed dapibus, massa ac ' \
                    'lobortis auctor, est libero pretium est, id elementum magna ' \
                    'arcu in tellus. '

if __name__ == '__main__':
    MainApp().run()