from typing import TYPE_CHECKING

from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty


if TYPE_CHECKING:
    from mvckivy.app import MVCApp


class BaseModel(EventDispatcher):
    app: ObjectProperty = ObjectProperty(None, rebind=True, allownone=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app: MVCApp = App.get_running_app()
