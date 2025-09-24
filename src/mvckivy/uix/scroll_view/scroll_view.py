from kivy.metrics import sp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.behaviors import BackgroundColorBehavior

from mvckivy.uix.behaviors import MVCBehavior, MKVAdaptiveBehavior
from mvckivy.uix.behaviors.declarative_behavior import DeclarativeBehavior


class MKVScrollView(
    DeclarativeBehavior, BackgroundColorBehavior, MKVAdaptiveBehavior, ScrollView
):
    def __init__(
        self, *args, scroll_wheel_distance=sp(60), do_scroll_x=False, **kwargs
    ):
        super().__init__(
            *args,
            scroll_wheel_distance=scroll_wheel_distance,
            do_scroll_x=do_scroll_x,
            **kwargs,
        )

    def on_touch_input(self):
        self.scroll_type = ["content"]

    def on_mouse_input(self):
        self.scroll_type = ["bars"]


class MVCScrollView(MVCBehavior, MKVScrollView):
    pass
