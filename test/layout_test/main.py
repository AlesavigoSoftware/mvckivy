import os

from kivymd.app import MDApp
from kivy.lang import Builder


class DemoApp(MDApp):
    def build(self):
        return Builder.load_file(os.path.join(os.path.dirname(__file__), "demo.kv"))


if __name__ == "__main__":
    DemoApp().run()
