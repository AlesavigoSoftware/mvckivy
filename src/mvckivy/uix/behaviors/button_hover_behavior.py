from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior

from .cursor_hover_behavior import CursorHoverBehavior


class ButtonHoverBehavior(ButtonBehavior, CursorHoverBehavior):
    def __init__(self, *args, animate: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.animate = animate
        self.on_enter_anim = Animation(elevation=2, d=.2)
        self.on_leave_anim = Animation(elevation=1, d=.2)

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