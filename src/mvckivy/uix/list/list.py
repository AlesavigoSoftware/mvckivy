from __future__ import annotations

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


class MKVList(MDGridLayout):
    _list_vertical_padding = NumericProperty("8dp")


class MKVBaseListItem(
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


class MKVBaseListItemText(MDLabel):
    pass


class MKVBaseListItemIcon(MDIcon):
    icon_color = ColorProperty(None)
    icon_color_disabled = ColorProperty(None)


class MKVListItemHeadlineText(MKVBaseListItemText):
    pass


class MKVListItemSupportingText(MKVBaseListItemText):
    pass


class MKVListItemTertiaryText(MKVBaseListItemText):
    pass


class MKVListItemTrailingSupportingText(MKVBaseListItemText):
    pass


class MKVListItemLeadingIcon(MKVBaseListItemIcon):
    pass


class MKVListItemLeadingAvatar(
    ThemableBehavior, CircularRippleBehavior, ButtonBehavior, FitImage
):
    pass
    _list_item = ObjectProperty()


class MKVListItemTrailingIcon(MKVBaseListItemIcon):
    pass


class MKVListItemTrailingCheckbox(MDCheckbox):
    pass


class MKVListItem(MKVBaseListItem, BoxLayout):
    leading_container: ObjectProperty[MDBoxLayout] = ObjectProperty()
    text_container: ObjectProperty[MDBoxLayout] = ObjectProperty()
    trailing_container: ObjectProperty[MDBoxLayout] = ObjectProperty()

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(
            widget,
            (
                MKVListItemHeadlineText,
                MKVListItemSupportingText,
                MKVListItemTertiaryText,
            ),
        ):
            if len(self.text_container.children) < 3:
                self.text_container.add_widget(widget)
            elif len(self.text_container.children) > 3:
                self._set_warnings(widget)
        elif isinstance(widget, (MKVListItemLeadingIcon, MKVListItemLeadingAvatar)):
            if not self.leading_container.children:
                widget._list_item = self
                self.leading_container.add_widget(widget)
                Clock.schedule_once(
                    lambda x: self._set_with_container(self.leading_container, widget)
                )
            else:
                self._set_warnings(widget)
        elif isinstance(
            widget,
            (
                MKVListItemTrailingIcon,
                MKVListItemTrailingCheckbox,
                MKVListItemTrailingSupportingText,
            ),
        ):
            if not self.trailing_container.children:
                self.trailing_container.add_widget(widget)
                Clock.schedule_once(
                    lambda x: self._set_with_container(self.trailing_container, widget)
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
