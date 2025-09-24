from __future__ import annotations

from typing import Self

from kivy.logger import Logger
from kivy.clock import Clock
from kivy.properties import (
    NumericProperty,
    ObjectProperty,
    BooleanProperty,
    ColorProperty,
    AliasProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

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

from mvckivy.properties.dedupe_mixin import KVDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty
from mvckivy.properties.null_dispatcher import create_null_dispatcher
from mvckivy.utils.constants import DENSITY


class MKVList(MDGridLayout):
    density = NumericProperty(0)

    def _get_alias_padding(self) -> list:
        return self._calc_alias_padding()

    def _calc_alias_padding(self) -> list[float]:
        return [
            0,
            dp(8) + DENSITY.get(self.density, dp(0)),
        ]

    alias_padding = AliasProperty(
        _get_alias_padding, None, bind=["density"], cache=True, rebind=False
    )


class MKVBaseListItem(
    DeclarativeBehavior,
    BackgroundColorBehavior,
    RectangularRippleBehavior,
    ButtonBehavior,
    ThemableBehavior,
    StateLayerBehavior,
):
    __kv_dedupe_targets__ = ("spacing", "padding", "md_bg_color", "height")

    density = NumericProperty(0)
    use_divider = BooleanProperty(False)
    divider_color = ColorProperty(None)
    md_bg_color_disabled = ColorProperty(None)

    def _get_alias_spacing(self) -> float:
        return self._calc_alias_spacing()

    def _calc_alias_spacing(self) -> float:
        return dp(16) + DENSITY.get(self.density, dp(0))

    alias_spacing = AliasProperty(
        _get_alias_spacing, None, bind=["density"], cache=True, rebind=False
    )

    def _get_md_bg_color(self) -> list:
        return self._calc_md_bg_color()

    def _calc_md_bg_color(self) -> list[float]:
        if self.theme_bg_color == "Primary":
            return self.theme_cls.surfaceColor
        else:
            return self.md_bg_color

    alias_md_bg_color = ExtendedAliasProperty(
        _get_md_bg_color,
        None,
        bind=["md_bg_color", "theme_bg_color", "theme_cls.surfaceColor"],
        cache=True,
        rebind=False,
    )


class MKVListItem(KVDedupeMixin, MKVBaseListItem, BoxLayout):
    def _get_alias_padding(self) -> list:
        return self._calc_alias_padding()

    def _calc_alias_padding(self) -> list[float]:

        if len(self.text_container.children) == 3:
            v_pad = dp(12)
        else:
            v_pad = dp(8)

        return [
            dp(16) + DENSITY.get(self.density, dp(0)),
            v_pad + DENSITY.get(self.density, dp(0)),
            dp(24) + DENSITY.get(self.density, dp(0)),
            v_pad + DENSITY.get(self.density, dp(0)),
        ]

    alias_padding = ExtendedAliasProperty(
        _get_alias_padding,
        None,
        bind=["density", "text_container.children"],
        cache=True,
        rebind=False,
    )

    leading_container: ObjectProperty[MDBoxLayout] = ObjectProperty(
        rebind=True, cache=True
    )
    text_container: ObjectProperty[MDBoxLayout] = ObjectProperty(
        create_null_dispatcher(children=[]), rebind=True, cache=True
    )
    trailing_container: ObjectProperty[MDBoxLayout] = ObjectProperty(
        rebind=True, cache=True
    )

    def on_disabled(self, instance: Self, value: bool) -> None:
        if self.leading_container.children:
            self.leading_container.children[0].disabled = value

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
    _list_item = ObjectProperty()


class MKVListItemTrailingIcon(MKVBaseListItemIcon):
    pass


class MKVListItemTrailingCheckbox(MDCheckbox):
    pass
