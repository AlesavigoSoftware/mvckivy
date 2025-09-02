from kivymd.uix.behaviors import HoverBehavior


class MenuItemHoverBehavior(HoverBehavior):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_bg_color = None

    def on_enter(self):
        super().on_enter()
        self.default_bg_color = self.md_bg_color
        self.md_bg_color = '#e4e4e4'

    def on_leave(self):
        super().on_leave()
        self.md_bg_color = self.default_bg_color
