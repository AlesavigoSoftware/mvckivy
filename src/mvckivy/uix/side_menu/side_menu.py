from kivy.metrics import sp
from kivy.properties import StringProperty, ColorProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.navigationdrawer import (
    MDNavigationDrawer,
    MDNavigationDrawerItem,
    MDNavigationDrawerItemTrailingText,
    MDNavigationDrawerHeader,
    MDNavigationDrawerDivider,
    MDNavigationDrawerMenu,
)

from mvckivy import CursorHoverBehavior, MVCBehavior, MTDBehavior
from mvckivy import InputModeBehavior


class SideMenu(MDNavigationDrawer, InputModeBehavior, MVCBehavior, MTDBehavior):
    def on_device_type(self, widget, device_type: str):
        super().on_device_type(widget, device_type)
        self.set_state("close")

    def on_touch_input(self):
        self.enable_swiping = True

    def on_mouse_input(self):
        self.enable_swiping = False


class SideMenuContentContainer(MDNavigationDrawerMenu, MVCBehavior):
    def __init__(
        self, *args, scroll_wheel_distance=sp(30), do_scroll_x=False, **kwargs
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


class SideMenuHeader(MDNavigationDrawerHeader):
    pass


class SideMenuDivider(MDNavigationDrawerDivider):
    pass


class SideMenuNavigationItem(MDNavigationDrawerItem, CursorHoverBehavior):
    icon = StringProperty()
    text = StringProperty()
    trailing_text = StringProperty()
    trailing_text_color = ColorProperty()

    external_screen_name = StringProperty()
    internal_screen_name = StringProperty()

    _trailing_text_obj = None

    def on_trailing_text(self, instance, value):
        self._trailing_text_obj = MDNavigationDrawerItemTrailingText(
            text=value,
            theme_text_color="Custom",
            text_color=self.trailing_text_color,
        )
        self.add_widget(self._trailing_text_obj)

    def on_trailing_text_color(self, instance, value):
        self._trailing_text_obj.text_color = value


class SideMenuLabel(MDBoxLayout):
    icon = StringProperty()
    text = StringProperty()
