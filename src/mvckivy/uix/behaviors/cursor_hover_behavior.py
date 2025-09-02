from kivy.core.window import Window
from kivymd.uix.behaviors import HoverBehavior


class CursorHoverBehavior(HoverBehavior):
    disabled = False

    def on_enter(self, *args):
        super().on_enter()

        if not self.disabled:
            Window.set_system_cursor("hand")

    def on_leave(self, *args):
        super().on_leave()

        if not self.disabled:
            Window.set_system_cursor("arrow")
