from kivy.animation import Animation
from kivy.uix.behaviors import ButtonBehavior

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


class ButtonHoverBehavior(ButtonBehavior, CursorHoverBehavior):
    def __init__(self, *args, animate: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.animate = animate
        self.on_enter_anim = Animation(elevation=2, d=0.2)
        self.on_leave_anim = Animation(elevation=1, d=0.2)

    def on_enter(self, *args):
        super().on_enter()
        if self.animate:
            self.on_enter_anim.start(self)

    def on_release(self, *args):
        super().on_release()
        Window.set_system_cursor("arrow")
        if self.animate:
            self.on_enter_anim.stop(self)
            self.on_leave_anim.start(self)

    def on_leave(self, *args):
        super().on_leave()
        if self.animate:
            self.on_enter_anim.stop(self)
            self.on_leave_anim.start(self)


class MenuItemHoverBehavior(HoverBehavior):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_bg_color = None

    def on_enter(self):
        super().on_enter()
        self.default_bg_color = self.md_bg_color
        self.md_bg_color = "#e4e4e4"

    def on_leave(self):
        super().on_leave()
        self.md_bg_color = self.default_bg_color
