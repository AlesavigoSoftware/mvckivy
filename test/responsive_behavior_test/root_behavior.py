# main.py
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

KV = r"""
#:kivy 2.3.0
#:import BoxLayout kivy.uix.boxlayout.BoxLayout

<Parent@BoxLayout>:
    orientation: "vertical"
    padding: "8dp"
    spacing: "8dp"
    canvas.before:
        Color:
            rgba: 0.9, 0.4, 0.2, 0.12
        Rectangle:
            pos: self.pos
            size: self.size
    on_kv_post:
        # На верхнем уровне правила Parent: root is self -> True
        print("[Parent rule] root is self? ->", root is self)

<Child@BoxLayout>:
    orientation: "vertical"
    padding: "8dp"
    spacing: "6dp"
    size_hint_y: None
    height: "160dp"
    canvas.before:
        Color:
            rgba: 0.2, 0.4, 0.9, 0.12
        Rectangle:
            pos: self.pos
            size: self.size
    on_kv_post:
        # На верхнем уровне правила Child: root is self -> True
        print("[Child rule]  root is self? ->", root is self)
        print("[Child rule]  root.parent is Parent? ->", isinstance(root.parent, BoxLayout))

    Label:
        text: "Inside Label of Child:\nroot is self? -> {}".format(root is self)
        # Здесь self — это Label, а root — всё ещё Child → False
    Label:
        text: "root class: {} | self class: {}".format(root.__class__.__name__, self.__class__.__name__)
    Button:
        text: "Проверить в консоли"
        on_release:
            print("[Button] root is self? ->", root is self)
            print("[Button] root.__class__:", root.__class__.__name__)
            print("[Button] self.__class__:", self.__class__.__name__)
            print("[Button] root.parent.__class__:", root.parent.__class__.__name__)

# Корневой виджет приложения:
Parent:
    Label:
        text: "Внутри Parent:\n(root — это Parent, self — это этот Label)\nroot is self? -> {}".format(root is self)
    Child:
        id: child1
    Label:
        text: "Убедись в консоли: root.parent у Child — это Parent"
"""


class DemoApp(App):
    def build(self):
        return Builder.load_string(KV)


if __name__ == "__main__":
    DemoApp().run()
