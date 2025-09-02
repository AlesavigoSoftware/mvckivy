from kivy.metrics import sp
from kivymd.uix.scrollview import MDScrollView

from mvckivy.uix.behaviors import InputModeBehavior, MVCBehavior


class MVCScrollView(MDScrollView, InputModeBehavior, MVCBehavior):
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
