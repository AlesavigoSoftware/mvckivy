from typing import Callable

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import NumericProperty, BooleanProperty

from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.menu.menu import (
    MDDropdownLeadingIconItem,
    MDDropdownTextItem,
    MDDropdownTrailingIconItem,
    MDDropdownTrailingIconTextItem,
    MDDropdownTrailingTextItem,
    MDDropdownLeadingIconTrailingTextItem,
    MDDropdownLeadingTrailingIconTextItem,
    MDDropdownLeadingTrailingIconItem,
)

from mvckivy.uix.behaviors.hover_behavior import MenuItemHoverBehavior


class MKVDropdownTextItem(MDDropdownTextItem, MenuItemHoverBehavior):
    pass


class MKVDropdownLeadingIconItem(MDDropdownLeadingIconItem, MenuItemHoverBehavior):
    pass


class MKVDropdownTrailingIconItem(MDDropdownTrailingIconItem, MenuItemHoverBehavior):
    pass


class MKVDropdownTrailingIconTextItem(
    MDDropdownTrailingIconTextItem, MenuItemHoverBehavior
):
    pass


class MKVDropdownTrailingTextItem(MDDropdownTrailingTextItem, MenuItemHoverBehavior):
    pass


class MKVDropdownLeadingIconTrailingTextItem(
    MDDropdownLeadingIconTrailingTextItem, MenuItemHoverBehavior
):
    pass


class MKVDropdownLeadingTrailingIconTextItem(
    MDDropdownLeadingTrailingIconTextItem, MenuItemHoverBehavior
):
    pass


class MKVDropdownLeadingTrailingIconItem(
    MDDropdownLeadingTrailingIconItem, MenuItemHoverBehavior
):
    pass


class MKVDropdownMenu(MDDropdownMenu):
    target_width = NumericProperty(dp(240))
    item_height = NumericProperty(dp(48))
    dismiss_after_release = BooleanProperty(True)

    def __init__(self, item_height: float, **kwargs):
        self.item_height = item_height  # on_items bugfix
        super().__init__(item_height=item_height, **kwargs)

    def on_device_type(self, widget, device_type: str):
        super().on_device_type(widget, device_type)
        self.dismiss()

    def on_header_cls(self, instance_dropdown_menu, instance_user_menu_header) -> None:
        """Called when a value is set to the :attr:`header_cls` parameter."""

        def add_content_header_cls(interval):
            self.ids.content_header.clear_widgets()
            self.ids.content_header.add_widget(instance_user_menu_header)

        Clock.schedule_once(add_content_header_cls, 0)

    def set_target_height(self) -> None:
        """
        Set the target height of the menu depending on the size of each item.
        """

        self.target_height = 0
        for item in self.menu.data:
            self.target_height += item.get("height", self.min_height)

        if self.header_cls:
            self.target_height += self.header_cls.height

        if 0 < self.max_height < self.target_height:
            self.target_height = self.max_height

        if self._start_coords[1] >= Window.height / 2:
            if self.target_height > self._start_coords[1]:
                self.target_height = (
                    self._start_coords[1]
                    - self.border_margin
                    - (
                        (self.caller.height / 2 + self.border_margin)
                        if self.position in ["top", "bottom"]
                        else 0
                    )
                )
        else:
            if Window.height - self._start_coords[1] < self.target_height:
                self.target_height = (
                    Window.height - self._start_coords[1] - self.border_margin
                )

    def open(self) -> None:
        self.set_menu_properties()
        # self._resize_leading_icons()
        Window.add_widget(self)
        self.position = self.adjust_position()

        if self.width <= dp(100):
            self.width = self.target_width

        self.height = self.target_height
        self._tar_x, self._tar_y = self.get_target_pos()
        self.x = self._tar_x
        self.y = self._tar_y - self.target_height
        self.scale_value_center = self.caller.center
        self.set_menu_pos()
        self.on_open()

    def _resize_leading_icons(self):  # bugfix
        for item in self.menu.children:
            icon = item.ids.container.ids.leading_icon
            if icon:
                icon.size = [self.item_height, self.item_height]

    def on_items(self, instance, value: list) -> None:
        items = []
        viewclass = "CoverageMDDropdownTextItem"

        for data in value:
            if "viewclass" not in data:
                if (
                    "leading_icon" not in data
                    and "trailing_icon" not in data
                    and "trailing_text" not in data
                ):
                    viewclass = "CoverageMDDropdownTextItem"
                elif (
                    "leading_icon" in data
                    and "trailing_icon" not in data
                    and "trailing_text" not in data
                ):
                    viewclass = "CoverageMDDropdownLeadingIconItem"
                elif (
                    "leading_icon" not in data
                    and "trailing_icon" in data
                    and "trailing_text" not in data
                ):
                    viewclass = "CoverageMDDropdownTrailingIconItem"
                elif (
                    "leading_icon" not in data
                    and "trailing_icon" in data
                    and "trailing_text" in data
                ):
                    viewclass = "CoverageMDDropdownTrailingIconTextItem"
                elif (
                    "leading_icon" in data
                    and "trailing_icon" in data
                    and "trailing_text" in data
                ):
                    viewclass = "CoverageMDDropdownLeadingTrailingIconTextItem"
                elif (
                    "leading_icon" in data
                    and "trailing_icon" in data
                    and "trailing_text" not in data
                ):
                    viewclass = "CoverageMDDropdownLeadingTrailingIconItem"
                elif (
                    "leading_icon" not in data
                    and "trailing_icon" not in data
                    and "trailing_text" in data
                ):
                    viewclass = "CoverageMDDropdownTrailingTextItem"
                elif (
                    "leading_icon" in data
                    and "trailing_icon" not in data
                    and "trailing_text" in data
                ):
                    viewclass = "CoverageMDDropdownLeadingIconTrailingTextItem"

                data["viewclass"] = viewclass

            if "height" not in data:
                data["height"] = self.item_height

            if "on_release" in data:
                data["on_release"] = self._modify_cb(data["on_release"])

            items.append(data)

        self._items = items
        # Update items in view
        if hasattr(self, "menu"):
            self.menu.data = self._items

    def _modify_cb(self, cb: Callable[..., None]):

        def wrapper(*args, **kwargs):
            cb()
            if self.dismiss_after_release:
                self.dismiss()

        return wrapper


class MKVDropdownMenuItems(list):
    def __init__(self, *args, model=None, controller=None, screen=None, **kwargs):
        super().__init__(*args)
        self.model = model
        self.controller = controller
        self.screen = screen
        self.app = App.get_running_app()
