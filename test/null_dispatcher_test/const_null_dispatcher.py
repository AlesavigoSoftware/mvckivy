# main.py
from kivy.app import App
from kivy.lang import Builder
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp


class ConstNullDispatcher(EventDispatcher):
    """Универсальный контроллер: значения из __getattr__/__setattr__, без Kivy-Property."""

    def __init__(self, **defaults):
        super().__init__()
        object.__setattr__(self, "_vals", dict(defaults))

    def __getattr__(self, name):
        vals = object.__getattribute__(self, "_vals")
        if name in vals:
            return vals[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name.startswith("_") or name in type(self).__dict__:
            return object.__setattr__(self, name, value)
        vals = object.__getattribute__(self, "_vals")
        vals[name] = value
        # ВАЖНО: здесь НЕТ dispatch — KV об этом не узнает.


class RealController(EventDispatcher):
    """Нормальный контроллер: Kivy-свойства → живые события."""

    ui_scale = NumericProperty(1.5)
    title = StringProperty("Real")


class Root(BoxLayout):
    controller = ObjectProperty(
        ConstNullDispatcher(ui_scale=1.0, title="Null"), rebind=True, allownone=True
    )

    def __init__(self, **kw):
        super().__init__(**kw)
        self.null = ConstNullDispatcher(ui_scale=1.0, title="Null")
        self.real = RealController()
        self.controller = self.real

    def toggle(self):
        self.controller = self.real if self.controller is self.null else self.null
        print("Switched to:", type(self.controller).__name__)


KV = r"""
#:kivy 2.3.0

<Root>:
    orientation: "vertical"
    padding: dp(12)
    spacing: dp(12)

    Label:
        text: "Active: {} | ui_scale={:.2f} | title='{}'".format(root.controller.__class__.__name__, root.controller.ui_scale,getattr(root.controller, "title", ""))

    # Блок, высота которого зависит от controller.ui_scale
    BoxLayout:
        size_hint_y: None
        height: dp(40) * root.controller.ui_scale
        canvas.before:
            Color:
                rgba: 0.2, 0.6, 0.9, 0.25
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "Height × ui_scale = {:.2f}".format(root.controller.ui_scale)

    Label:
        text: "Двигай слайдер. В NullController высота НЕ меняется (нет Kivy-Property)."

    Slider:
        min: 0.5
        max: 3.0
        value: root.controller.ui_scale
        on_value: root.controller.ui_scale = self.value

    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)
        Button:
            text: "Toggle (Null <-> Real)"
            on_release: root.toggle()
        Button:
            text: "Set title"
            on_release: setattr(root.controller, "title", "Null" if root.controller.__class__.__name__ == "NullController" else "Real")

Root:
"""


class DemoApp(App):
    def build(self):
        Builder.load_string(KV)
        return Root()


if __name__ == "__main__":
    DemoApp().run()
