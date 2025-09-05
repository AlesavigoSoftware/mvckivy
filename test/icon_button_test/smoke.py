import os
os.environ.setdefault("KIVY_WINDOW", "mock")
os.environ.setdefault("KIVY_GL_BACKEND", "mock")
from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.app import MDApp
from mvckivy.uix.buttons.icon_button import AutoResizeMDIconButton

KV = """
MDScreen:
    AutoResizeMDIconButton:
        id: b
        icon: "star"
        style: "filled"
"""

class Demo(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Olive"
        return Builder.load_string(KV)
    def on_start(self):
        b = self.root.ids.b
        _ = b.bg_rgba, b.icon_rgba, b.line_rgba, b.disabled_icon_rgba
        Clock.schedule_once(lambda *_: self.stop(), 0.1)

if __name__ == "__main__":
    Demo().run()

