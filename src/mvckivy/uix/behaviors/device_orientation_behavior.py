from kivy.event import EventDispatcher
from kivymd.app import MDApp


class DeviceOrientationBehavior(EventDispatcher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type("on_portrait")
        self.register_event_type("on_landscape")
        self.__initialize_dispatchers(MDApp.get_running_app())

    def __initialize_dispatchers(self, app):
        app.model.bind(device_orientation=self.on_device_orientation)
        self.on_device_orientation(self, app.model.device_orientation)

    def on_device_orientation(self, widget, orientation: str):
        if orientation == "portrait":
            self.dispatch("on_portrait")
        elif orientation == "landscape":
            self.dispatch("on_landscape")

    def on_portrait(self, widget):
        pass

    def on_landscape(self, widget):
        pass
