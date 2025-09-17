# main.py
from kivy.app import App
from kivy.lang import Builder
from kivy.event import EventDispatcher
from kivy.properties import (
    ObjectProperty,
    NumericProperty,
    StringProperty,
    BooleanProperty,
    ListProperty,
    DictProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp


def _prop_for(value):
    if isinstance(value, bool):
        return BooleanProperty(value)
    if isinstance(value, (int, float)):
        return NumericProperty(value)
    if isinstance(value, str):
        return StringProperty(value)
    if isinstance(value, (list, tuple)):
        return ListProperty(list(value))
    if isinstance(value, dict):
        return DictProperty(value)
    return ObjectProperty(value, allownone=True)


def create_null_dispatcher(**defaults):
    # Динамически создаём подкласс EventDispatcher с Kivy-свойствами на классе
    attrs = {name: _prop_for(val) for name, val in defaults.items()}
    cls = type(f"NullDispatcher_{id(defaults)}", (EventDispatcher,), attrs)
    return cls()


class RealController(EventDispatcher):
    ui_scale = NumericProperty(1.5)
    title = StringProperty("Real")


class MyWidget(BoxLayout):
    controller = ObjectProperty(None, rebind=True, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.null_controller = create_null_dispatcher(ui_scale=1.0, title="Null")
        self.real_controller = RealController()
        self.controller = self.null_controller  # стартуем с «нуля»

    def toggle_controller(self):
        self.controller = (
            self.real_controller
            if self.controller is self.null_controller
            else self.null_controller
        )
        print("Controller switched to:", type(self.controller).__name__)


KV = r"""
#:kivy 2.3.0

<MyWidget>:
    orientation: "vertical"
    padding: dp(12)
    spacing: dp(12)

    # Блок, зависящий от controller.ui_scale (живой биндинг)
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
            text: "Высота х ui_scale = {:.2f}".format(root.controller.ui_scale)

    # ВАЖНО: всё в ОДНУ строку, чтобы не ловить ParserException по отступам
    Label:
        text: "Текущий контроллер: {} | ui_scale={:.2f} | title='{}'".format(root.controller.__class__.__name__, root.controller.ui_scale, getattr(root.controller, "title", ""))

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
            text: "Toggle controller (Null <-> Real)"
            on_release: root.toggle_controller()
        Button:
            text: "Set title on current"
            on_release: setattr(root.controller, "title", "Null" if root.controller.__class__.__name__.startswith("NullController_") else "Real")

# Корень дерева:
MyWidget:
"""


class DemoApp(App):
    def build(self):
        return Builder.load_string(KV)


if __name__ == "__main__":
    DemoApp().run()
