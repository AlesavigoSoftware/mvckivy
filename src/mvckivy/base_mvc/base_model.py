from kivy.event import EventDispatcher
from kivymd.app import MDApp


class BaseModel(EventDispatcher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app: MDApp = MDApp.get_running_app()
