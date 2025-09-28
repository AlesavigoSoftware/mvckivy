from __future__ import annotations

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import (
    NumericProperty,
    VariableListProperty,
    ColorProperty,
    BooleanProperty,
    ObjectProperty,
)
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.anchorlayout import MDAnchorLayout

from kivymd.uix.behaviors import MotionDialogBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDIcon, MDLabel

from mvckivy.uix.behaviors import MKVAdaptiveBehavior
from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty
from mvckivy.properties.null_dispatcher import create_null_dispatcher


class MKVDialog(MotionDialogBehavior, MKVAdaptiveBehavior, MDCard):
    __events__ = ("on_pre_open", "on_open", "on_pre_dismiss", "on_dismiss")

    width_offset = NumericProperty(dp(48))

    radius: VariableListProperty[list[float]] = VariableListProperty(dp(28), lenght=4)
    scrim_color: ColorProperty = ColorProperty([0, 0, 0, 0.3])
    auto_dismiss = BooleanProperty(True)
    opacity: NumericProperty[float] = NumericProperty(0)  # creates invisible
    dismiss_on_device_type = BooleanProperty(True)

    _scrim: ObjectProperty[MKVDialogScrim | None] = ObjectProperty(None, allownone=True)
    _is_open = False

    icon_container: ObjectProperty[MDAnchorLayout | None] = ObjectProperty(
        None, allownone=True
    )
    headline_container: ObjectProperty[MDBoxLayout | None] = ObjectProperty(
        None, allownone=True
    )
    supporting_text_container: ObjectProperty[MDBoxLayout | None] = ObjectProperty(
        None, allownone=True
    )
    content_container: ObjectProperty[MDBoxLayout | None] = ObjectProperty(
        None, allownone=True
    )
    button_container: ObjectProperty[MDBoxLayout | None] = ObjectProperty(
        None, allownone=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Window.bind(on_resize=self.update_size)

    def update_size(self, *args):
        window_width = args[1]
        window_height = args[2]

        self.size_hint_max_x = max(
            self.width_offset,
            min(
                dp(560) if self._last_profile.device_type != "mobile" else dp(420),
                window_width - self.width_offset,
            ),
        )

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, MKVDialogIcon):
            if self.icon_container:
                self.icon_container.add_widget(widget)
        elif isinstance(widget, MKVDialogHeadlineText):
            if self.headline_container:
                self.headline_container.add_widget(widget)
        elif isinstance(widget, MKVDialogSupportingText):
            if self.supporting_text_container:
                self.supporting_text_container.add_widget(widget)
        elif isinstance(widget, MKVDialogContentContainer):
            if self.content_container:
                self.content_container.add_widget(widget)
        elif isinstance(widget, MKVDialogButtonContainer):
            if self.button_container:
                self.button_container.add_widget(widget)
        else:
            return super().add_widget(widget)

    def open(self) -> None:
        """Show the dialog."""

        if self._is_open:
            return

        self.dispatch("on_pre_open")
        self._is_open = True

        if not self._scrim:
            self._scrim = MKVDialogScrim(color=self.scrim_color)

        Window.add_widget(self._scrim)
        Window.add_widget(self)
        super().on_open()
        self.dispatch("on_open")

    def on_pre_open(self, *args) -> None:
        if self.icon_container:
            self.icon_container.height = self.icon_container.children[
                0
            ].height  # bugfix

    def on_open(self, *args) -> None:
        pass

    def on_dismiss(self, *args) -> None:
        pass

    def on_pre_dismiss(self, *args) -> None:
        pass

    def on_press(self, *args) -> None:
        pass

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) and self.auto_dismiss:
            self.dismiss()
            return True
        super().on_touch_down(touch)
        return True

    def dismiss(self, *args) -> None:
        """Closes the dialog."""

        self.dispatch("on_pre_dismiss")
        super().on_dismiss()
        self._is_open = False
        self.dispatch("on_dismiss")


class MKVDialogIcon(AliasDedupeMixin, MDIcon):
    theme_cls = ObjectProperty(
        cache=True,
        rebind=True,
    )

    def _get_alias_icon_color(self, prop: ExtendedAliasProperty) -> list[float]:
        return self._calc_alias_icon_color(prop)

    def _calc_alias_icon_color(self, prop: ExtendedAliasProperty) -> list[float]:
        if self.theme_icon_color == "Primary":
            return self.theme_cls.secondaryColor
        if self.icon_color:
            return self.icon_color
        return self.theme_cls.transparentColor

    alias_icon_color = ExtendedAliasProperty(
        _get_alias_icon_color,
        None,
        bind=(
            "theme_icon_color",
            "icon_color",
            "theme_cls.secondaryColor",
            "theme_cls.transparentColor",
        ),
        cache=True,
        watch_before_use=True,
    )


class MKVDialogHeadlineText(AliasDedupeMixin, MDLabel):
    theme_cls = ObjectProperty(
        cache=True,
        rebind=True,
    )

    def _get_alias_color(self, prop: ExtendedAliasProperty) -> list[float]:
        return self._calc_alias_color(prop)

    def _calc_alias_color(self, prop: ExtendedAliasProperty) -> list[float]:
        if self.theme_text_color == "Primary":
            return self.theme_cls.onSurfaceColor
        if self.text_color and self.text_color != self.theme_cls.transparentColor:
            return self.text_color
        return self.theme_cls.onSurfaceColor

    alias_color = ExtendedAliasProperty(
        _get_alias_color,
        None,
        bind=(
            "theme_text_color",
            "text_color",
            "color",
            "theme_cls.onSurfaceColor",
            "theme_cls.transparentColor",
        ),
        cache=True,
        watch_before_use=True,
    )


class MKVDialogSupportingText(AliasDedupeMixin, MDLabel):
    theme_cls = ObjectProperty(
        cache=True,
        rebind=True,
    )

    def _get_alias_text_color(self, prop: ExtendedAliasProperty) -> list[float]:
        return self._calc_alias_text_color(prop)

    def _calc_alias_text_color(self, prop: ExtendedAliasProperty) -> list[float]:
        if self.theme_text_color == "Primary":
            return self.theme_cls.onSurfaceVariantColor
        if self.text_color and self.text_color != self.theme_cls.transparentColor:
            return self.text_color
        return self.theme_cls.onSurfaceVariantColor

    alias_text_color = ExtendedAliasProperty(
        _get_alias_text_color,
        None,
        bind=(
            "theme_text_color",
            "text_color",
            "theme_cls.onSurfaceVariantColor",
            "theme_cls.transparentColor",
        ),
        cache=True,
        watch_before_use=True,
    )


class MKVDialogContentContainer(MDBoxLayout):
    pass


class MKVDialogButtonContainer(MDBoxLayout):
    pass


class MKVDialogScrim(Widget):
    color = ColorProperty(None)
    alpha = NumericProperty(0)
