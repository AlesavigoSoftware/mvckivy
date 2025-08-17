from kivy.event import EventDispatcher
from kivymd.tools.hotreload.app import MDApp


class InputModeBehavior(EventDispatcher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type("on_touch_input")
        self.register_event_type("on_mouse_input")
        self.__initialize_dispatchers(MDApp.get_running_app())

    def __initialize_dispatchers(self, app):
        app.model.bind(input_mode=self.on_input_mode)
        self.on_input_mode(self, app.model.input_mode)

    def on_input_mode(self, widget, input_method: str):
        if input_method == "mouse":
            self.dispatch("on_mouse_input")
        elif input_method == "touch":
            self.dispatch("on_touch_input")

    def on_touch_input(self):
        pass

    def on_mouse_input(self):
        pass
