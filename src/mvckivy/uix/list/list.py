from __future__ import annotations

__all__ = (
    "BaseListItemText",
    "BaseListItem",
    "BaseListItemIcon",
    "MDList",
    "MDListItem",
    "MDListItemHeadlineText",
    "MDListItemSupportingText",
    "MDListItemTrailingSupportingText",
    "MDListItemLeadingIcon",
    "MDListItemTrailingIcon",
    "MDListItemTrailingCheckbox",
    "MDListItemLeadingAvatar",
    "MDListItemTertiaryText",
)

from kivy.logger import Logger
from kivy.clock import Clock
from kivy.properties import (
    NumericProperty,
    ObjectProperty,
    BooleanProperty,
    ColorProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import (
    CircularRippleBehavior,
    DeclarativeBehavior,
    RectangularRippleBehavior,
    BackgroundColorBehavior,
)
from kivymd.uix.behaviors.state_layer_behavior import StateLayerBehavior
from kivymd.uix.fitimage import FitImage
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon


class MDList(MDGridLayout):
    _list_vertical_padding = NumericProperty("8dp")


class BaseListItem(
    DeclarativeBehavior,
    BackgroundColorBehavior,
    RectangularRippleBehavior,
    ButtonBehavior,
    ThemableBehavior,
    StateLayerBehavior,
):

    use_divider = BooleanProperty(False)
    divider_color = ColorProperty(None)
    md_bg_color_disabled = ColorProperty(None)


class BaseListItemText(MDLabel):
    pass


class BaseListItemIcon(MDIcon):
    icon_color = ColorProperty(None)
    icon_color_disabled = ColorProperty(None)


class MDListItemHeadlineText(BaseListItemText):
    pass


class MDListItemSupportingText(BaseListItemText):
    pass


class MDListItemTertiaryText(BaseListItemText):
    pass


class MDListItemTrailingSupportingText(BaseListItemText):
    pass


class MDListItemLeadingIcon(BaseListItemIcon):
    pass


class MDListItemLeadingAvatar(
    ThemableBehavior, CircularRippleBehavior, ButtonBehavior, FitImage
):
    pass
    _list_item = ObjectProperty()


class MDListItemTrailingIcon(BaseListItemIcon):
    pass


class MDListItemTrailingCheckbox(MDCheckbox):
    pass


class MDListItem(BaseListItem, BoxLayout):
    leading_container: ObjectProperty[MDBoxLayout] = ObjectProperty()
    text_container: ObjectProperty[MDBoxLayout] = ObjectProperty()
    trailing_container: ObjectProperty[MDBoxLayout] = ObjectProperty()
    
    def add_widget(self, widget, *args, **kwargs):
        if isinstance(
            widget,
            (
                MDListItemHeadlineText,
                MDListItemSupportingText,
                MDListItemTertiaryText,
            ),
        ):
            if len(self.text_container.children) < 3:
                self.text_container.add_widget(widget)
            elif len(self.text_container.children) > 3:
                self._set_warnings(widget)
        elif isinstance(widget, (MDListItemLeadingIcon, MDListItemLeadingAvatar)):
            if not self.leading_container.children:
                widget._list_item = self
                self.leading_container.add_widget(widget)
                Clock.schedule_once(
                    lambda x: self._set_with_container(
                        self.leading_container, widget
                    )
                )
            else:
                self._set_warnings(widget)
        elif isinstance(
            widget,
            (
                MDListItemTrailingIcon,
                MDListItemTrailingCheckbox,
                MDListItemTrailingSupportingText,
            ),
        ):
            if not self.trailing_container.children:
                self.trailing_container.add_widget(widget)
                Clock.schedule_once(
                    lambda x: self._set_with_container(
                        self.trailing_container, widget
                    )
                )
            else:
                self._set_warnings(widget)
        else:
            return super().add_widget(widget)

    def _set_warnings(self, widget):
        Logger.warning(
            f"KivyMD: "
            f"Do not use more than one <{widget.__class__.__name__}> "
            f"widget. This is contrary to the material design rules "
            f"of version 3"
        )

    def _set_with_container(self, container, widget):
        container.width = widget.width
