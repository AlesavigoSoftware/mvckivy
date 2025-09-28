from __future__ import annotations

import logging
from typing import Self

from kivy.clock import Clock
from kivy.properties import (
    NumericProperty,
    ObjectProperty,
    BooleanProperty,
)
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

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
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.divider import MDDivider
from kivymd.uix.selectioncontrol import MDSwitch

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty
from mvckivy.properties.null_dispatcher import create_null_dispatcher
from mvckivy.utils.constants import DENSITY


logger = logging.getLogger("mvckivy")


class MKVList(AliasDedupeMixin, MDGridLayout):
    density = NumericProperty(0)
    use_divider = BooleanProperty(True)

    def _get_alias_padding(self, prop: ExtendedAliasProperty) -> list:
        return self._calc_alias_padding(prop)

    def _calc_alias_padding(self, prop: ExtendedAliasProperty) -> list[float]:
        v_pad = dp(8)
        return [
            0,
            v_pad + DENSITY.get(self.density, dp(0)),
        ]

    alias_padding = ExtendedAliasProperty(
        _get_alias_padding, None, bind=["density", "padding"], cache=True, rebind=False
    )

    def on_kv_post(self, base_widget: Widget) -> None:
        super().on_kv_post(base_widget)
        self.on_use_divider()

    def on_use_divider(self, *_):
        """Динамическое включение/выключение разделителей после on_kv_post."""
        if self.use_divider:
            self._insert_dividers()
        else:
            self._remove_dividers()

    @classmethod
    def _make_divider(cls) -> Widget:
        return MDDivider(size_hint_y=None, divider_width=dp(1), height=dp(1))

    def _remove_dividers(self) -> None:
        divider_type = type(self._make_divider())
        for w in list(self.children):
            if isinstance(w, divider_type):
                self.remove_widget(w)

    def _insert_dividers(self) -> None:
        self._remove_dividers()

        n = len(self.children)
        if n <= 1:
            return

        for i in range(n - 1):
            # Индекс позиции разделителя в текущем списке на i-м шаге
            idx = 2 * i + 1
            self.add_widget(self._make_divider(), index=idx)


class MKVBaseListItem(
    AliasDedupeMixin,
    DeclarativeBehavior,
    BackgroundColorBehavior,
    RectangularRippleBehavior,
    ButtonBehavior,
    ThemableBehavior,
    StateLayerBehavior,
):
    theme_cls = ObjectProperty(
        cache=True,
        rebind=True,
    )
    density = NumericProperty(0)
    HEIGHTS = {
        0: dp(100),
        1: dp(56),
        2: dp(72),
        3: dp(88),
    }

    def _get_alias_spacing(self, prop: ExtendedAliasProperty) -> float:
        return self._calc_alias_spacing(prop)

    def _calc_alias_spacing(self, prop: ExtendedAliasProperty) -> float:
        return dp(16) + DENSITY.get(self.density, dp(0))

    alias_spacing = ExtendedAliasProperty(
        _get_alias_spacing, None, bind=["density", "spacing"], cache=True, rebind=False
    )

    def _get_md_bg_color(self, prop: ExtendedAliasProperty) -> list:
        return self._calc_md_bg_color(prop)

    def _calc_md_bg_color(self, prop: ExtendedAliasProperty) -> list[float]:
        if self.theme_bg_color == "Primary":
            return self.theme_cls.surfaceColor
        else:
            return self.md_bg_color

    alias_md_bg_color = ExtendedAliasProperty(
        _get_md_bg_color,
        None,
        bind=["md_bg_color", "theme_bg_color", "theme_cls.surfaceColor"],
        cache=True,
    )

    def _get_alias_padding(self, prop: ExtendedAliasProperty) -> list:
        return self._calc_alias_padding(prop)

    def _calc_alias_padding(self, prop: ExtendedAliasProperty) -> list[float]:

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
        bind=["density", "text_container.children", "padding"],
        cache=True,
    )

    def _get_alias_height(self, prop: ExtendedAliasProperty) -> float:
        return self._calc_alias_height(prop)

    def _calc_alias_height(self, prop: ExtendedAliasProperty) -> float:
        return self.HEIGHTS[len(self.text_container.children)] + DENSITY.get(
            self.density, dp(0)
        )

    alias_height = ExtendedAliasProperty(
        _get_alias_height,
        None,
        bind=["density", "text_container.children", "height"],
        cache=True,
    )

    leading_container: ObjectProperty[BoxLayout] = ObjectProperty(
        create_null_dispatcher(children=[]), rebind=True, cache=True
    )
    text_container: ObjectProperty[BoxLayout] = ObjectProperty(
        create_null_dispatcher(children=[]), rebind=True, cache=True
    )
    trailing_container: ObjectProperty[BoxLayout] = ObjectProperty(
        create_null_dispatcher(children=[]), rebind=True, cache=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._trigger_layout = Clock.create_trigger(self._refresh_layout, 0)

    def _refresh_layout(self, _):
        pass


class MKVListItem(MKVBaseListItem, BoxLayout):
    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.leading_container.bind(children=lambda *args: self._trigger_layout())
        self.text_container.bind(children=lambda *args: self._trigger_layout())
        self.trailing_container.bind(children=lambda *args: self._trigger_layout())

    def _refresh_layout(self, *args):
        if self.leading_container.children:
            self.leading_container.children[0].pos_hint = (
                {"top": 1}
                if len(self.text_container.children) == 3
                else {"center_y": 0.5}
            )
        if self.text_container.children and self.trailing_container.children:
            self.trailing_container.children[0].pos_hint = (
                {"top": 1}
                if len(self.text_container.children) == 3
                else {"center_y": 0.5}
            )

    def on_use_divider(self, instance: Self, value: bool) -> None:
        self.h_divider.divider_width = dp(1) if value else 0

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
                    lambda x: self._set_width_container(self.leading_container, widget)
                )
            else:
                self._set_warnings(widget)
        elif isinstance(
            widget,
            (
                MKVListItemTrailingIcon,
                MKVListItemTrailingCheckbox,
                MKVListItemTrailingSupportingText,
                MKVListItemTrailingSwitch,
            ),
        ):
            if not self.trailing_container.children:
                self.trailing_container.add_widget(widget)
                Clock.schedule_once(
                    lambda x: self._set_width_container(self.trailing_container, widget)
                )
            else:
                self._set_warnings(widget)
        else:
            return super().add_widget(widget)

    def _set_warnings(self, widget):
        logger.warning(
            f"KivyMD: "
            f"Do not use more than one <{widget.__class__.__name__}> "
            f"widget. This is contrary to the material design rules "
            f"of version 3"
        )

    @staticmethod
    def _set_width_container(container, widget):
        container.width = widget.width


class MKVBaseListItemText(AliasDedupeMixin, MDLabel):
    theme_cls = ObjectProperty(
        cache=True,
        rebind=True,
    )

    def _get_alias_text_color(self, prop: ExtendedAliasProperty) -> list[float]:
        return self._calc_alias_text_color(prop)

    def _calc_alias_text_color(self, prop: ExtendedAliasProperty) -> list[float]:
        if self.theme_text_color == "Primary":
            return self.theme_cls.onSurfaceVariantColor
        if self.text_color:
            return self.text_color
        return self.theme_cls.onSurfaceVariantColor

    alias_text_color = ExtendedAliasProperty(
        _get_alias_text_color,
        None,
        bind=("theme_text_color", "text_color", "theme_cls.onSurfaceVariantColor"),
        cache=True,
        watch_before_use=True,
    )


class MKVBaseListItemIcon(AliasDedupeMixin, MDIcon):
    theme_cls = ObjectProperty(
        cache=True,
        rebind=True,
    )
    disabled = BooleanProperty(False)

    def _get_alias_disabled_color(self, prop: ExtendedAliasProperty) -> list[float]:
        return self._calc_alias_disabled_color(prop)

    def _calc_alias_disabled_color(self, prop: ExtendedAliasProperty) -> list[float]:
        if self.icon_color_disabled:
            return self.icon_color_disabled
        base_color = self.theme_cls.onSurfaceColor
        opacity = self.icon_button_standard_opacity_value_disabled_icon
        return base_color[:-1] + [opacity]

    alias_disabled_color = ExtendedAliasProperty(
        _get_alias_disabled_color,
        None,
        bind=[
            "icon_color_disabled",
            "icon_button_standard_opacity_value_disabled_icon",
            "theme_cls.onSurfaceColor",
            "disabled_color",
        ],
        cache=True,
        rebind=False,
    )

    def _get_alias_text_color(self, prop: ExtendedAliasProperty) -> list[float]:
        return self._calc_alias_text_color(prop)

    def _calc_alias_text_color(self, prop: ExtendedAliasProperty) -> list[float]:
        if self.disabled:
            return self.disabled_color
        if self.theme_icon_color == "Primary":
            return self.theme_cls.onSurfaceVariantColor
        if self.icon_color:
            return self.icon_color
        return self.theme_cls.transparentColor

    alias_text_color = ExtendedAliasProperty(
        _get_alias_text_color,
        None,
        bind=[
            "disabled",
            "disabled_color",
            "theme_icon_color",
            "icon_color",
            "theme_cls.onSurfaceVariantColor",
            "theme_cls.transparentColor",
            "text_color",
        ],
        cache=True,
        rebind=False,
    )


class MKVListItemHeadlineText(MKVBaseListItemText):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("font_style", "Body")
        kwargs.setdefault("role", "large")
        kwargs.setdefault("bold", True)
        super().__init__(*args, **kwargs)

    def _calc_alias_text_color(self, prop: ExtendedAliasProperty) -> list[float]:
        if self.theme_text_color == "Primary":
            return self.theme_cls.onSurfaceColor
        if self.text_color:
            return self.text_color
        return self.theme_cls.onSurfaceColor


class MKVListItemSupportingText(MKVBaseListItemText):
    pass


class MKVListItemTertiaryText(MKVBaseListItemText):
    pass


class MKVListItemTrailingSupportingText(MKVBaseListItemText):
    pass


class MKVListItemTrailingIcon(MKVBaseListItemIcon):
    pass


class MKVListItemLeadingAvatar(
    AliasDedupeMixin,
    ThemableBehavior,
    CircularRippleBehavior,
    ButtonBehavior,
    FitImage,
):
    _list_item = ObjectProperty(
        create_null_dispatcher(list_opacity_value_disabled_leading_avatar=0),
        cache=True,
        rebind=True,
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(40), dp(40)))
        super().__init__(*args, **kwargs)

        self.fbind("alias_radius", self._apply_radius)
        self.fbind("alias_md_bg_color", self._apply_md_bg_color)
        self._apply_radius(self, self.alias_radius)
        self._apply_md_bg_color(self, self.alias_md_bg_color)

    @staticmethod
    def _apply_radius(instance, value):
        if value is not None:
            instance.radius = value

    @staticmethod
    def _apply_md_bg_color(instance, value):
        if value is not None:
            instance.md_bg_color = value

    def _get_alias_radius(self, prop: ExtendedAliasProperty) -> float:
        return self._calc_alias_radius(prop)

    def _calc_alias_radius(self, prop: ExtendedAliasProperty) -> float:
        return self.height / 2

    alias_radius = ExtendedAliasProperty(
        _get_alias_radius,
        None,
        bind=("height", "radius"),
        cache=True,
        watch_before_use=True,
    )

    def _get_alias_md_bg_color(self, prop: ExtendedAliasProperty) -> list[float]:
        return self._calc_alias_md_bg_color(prop)

    def _calc_alias_md_bg_color(self, prop: ExtendedAliasProperty) -> list[float]:
        if not self.disabled:
            return self.theme_cls.primaryContainerColor
        base_color = self.theme_cls.onSurfaceColor
        opacity = self._list_item.list_opacity_value_disabled_leading_avatar
        return base_color[:-1] + opacity

    alias_md_bg_color = ExtendedAliasProperty(
        _get_alias_md_bg_color,
        None,
        bind=(
            "disabled",
            "md_bg_color",
            "theme_cls.primaryContainerColor",
            "theme_cls.onSurfaceColor",
            "_list_item.list_opacity_value_disabled_leading_avatar",
        ),
        cache=True,
        watch_before_use=True,
    )


class MKVListItemLeadingIcon(MKVBaseListItemIcon):
    pass


class MKVListItemTrailingCheckbox(MDCheckbox):
    pass


class MKVListItemTrailingSwitch(MDSwitch):
    pass
