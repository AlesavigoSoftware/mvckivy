from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.carousel import Carousel
from kivy.uix.widget import Widget

from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import (
    BackgroundColorBehavior,
    DeclarativeBehavior,
    RectangularRippleBehavior,
)
from kivymd.uix.behaviors.state_layer_behavior import StateLayerBehavior

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty

KV_PATH = Path(__file__).with_name("tab.kv")
if KV_PATH.exists():  # pragma: no branch - defensive
    Builder.load_file(str(KV_PATH))

TabContentFactory = Callable[[], Widget]


@dataclass(slots=True)
class TabDefinition:
    title: str
    icon: str | None = None
    content: Widget | None = None
    content_factory: TabContentFactory | None = None
    active_icon: str | None = None
    inactive_icon: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    item: "MKVTabItem" | None = None
    content_widget: "MKVTabContent" | None = None

    def ensure_content(self) -> Widget:
        if self.content is not None:
            return self.content
        if self.content_factory is None:
            raise ValueError("Provide `content` or `content_factory` for a tab.")
        widget = self.content_factory()
        if widget.parent is not None:
            widget.parent.remove_widget(widget)
        self.content = widget
        return widget


class MKVTabCarousel(Carousel):
    lock_swiping = BooleanProperty(False)

    def on_touch_move(self, touch):  # type: ignore[override]
        if self.lock_swiping:
            return False
        return super().on_touch_move(touch)


class MKVTabContent(AliasDedupeMixin, AnchorLayout):
    definition = ObjectProperty(None, rebind=True, allownone=True)
    lazy = BooleanProperty(True)
    is_materialized = BooleanProperty(False)

    def ensure_content(self):
        if self.definition is None:
            raise ValueError("TabContent requires TabDefinition.")
        if not self.is_materialized:
            widget = self.definition.ensure_content()
            self.clear_widgets()
            self.add_widget(widget)
            self.is_materialized = True
            return widget
        return self.children[0]


class MKVTabItem(
    AliasDedupeMixin,
    DeclarativeBehavior,
    BackgroundColorBehavior,
    RectangularRippleBehavior,
    ButtonBehavior,
    ThemableBehavior,
    StateLayerBehavior,
    BoxLayout,
):
    text = StringProperty("")
    icon = StringProperty("")
    display_icon = StringProperty("")
    active = BooleanProperty(False)

    active_text_color = ColorProperty(None)
    inactive_text_color = ColorProperty(None)
    active_icon_color = ColorProperty(None)
    inactive_icon_color = ColorProperty(None)

    definition = ObjectProperty(None, rebind=True, allownone=True)
    tabs_ref = ObjectProperty(None, rebind=True, allownone=True)

    icon_widget = ObjectProperty(None, rebind=True, allownone=True)
    text_widget = ObjectProperty(None, rebind=True, allownone=True)
    _icon_texture_size = ListProperty([0.0, 0.0])
    _text_texture_size = ListProperty([0.0, 0.0])

    def __init__(self, **kwargs):
        self._apply_active_state_trigger = Clock.create_trigger(
            self._apply_active_state, -1
        )
        self._update_display_trigger = Clock.create_trigger(
            self._update_display_icon, -1
        )
        self._bound_icon_widget: Widget | None = None
        self._bound_text_widget: Widget | None = None
        super().__init__(**kwargs)

    def _get_alias_implicit_width(self, prop: ExtendedAliasProperty) -> float:
        return self._calc_alias_implicit_width(prop)

    def _calc_alias_implicit_width(self, prop: ExtendedAliasProperty) -> float:
        width = self.padding[0] + self.padding[2]
        if self._icon_texture_size[0]:
            width += self._icon_texture_size[0]
        if self._text_texture_size[0]:
            width += self._text_texture_size[0]
        if self._icon_texture_size[0] and self._text_texture_size[0]:
            width += self.spacing
        return max(width, dp(48))

    alias_implicit_width = ExtendedAliasProperty(
        _get_alias_implicit_width,
        None,
        bind=("padding", "spacing", "_icon_texture_size", "_text_texture_size"),
        cache=True,
        watch_before_use=True,
    )

    def _get_alias_height(self, prop: ExtendedAliasProperty) -> float:
        return self._calc_alias_height(prop)

    def _calc_alias_height(self, prop: ExtendedAliasProperty) -> float:
        height = self.padding[1] + self.padding[3]
        if self._icon_texture_size[1]:
            height += self._icon_texture_size[1]
        if self._text_texture_size[1]:
            height += self._text_texture_size[1]
        if self._icon_texture_size[1] and self._text_texture_size[1]:
            height += self.spacing
        return max(height, dp(48))

    alias_height = ExtendedAliasProperty(
        _get_alias_height,
        None,
        bind=("padding", "spacing", "_icon_texture_size", "_text_texture_size"),
        cache=True,
        watch_before_use=True,
    )

    def _get_alias_text_color(self, prop: ExtendedAliasProperty) -> list[float]:
        return self._calc_alias_text_color(prop)

    def _calc_alias_text_color(self, prop: ExtendedAliasProperty) -> list[float]:
        user_value = self.active_text_color if self.active else self.inactive_text_color
        return self._resolve_color(user_value, active=self.active)

    alias_text_color = ExtendedAliasProperty(
        _get_alias_text_color,
        None,
        bind=(
            "active",
            "active_text_color",
            "inactive_text_color",
            "theme_cls.primaryColor",
            "theme_cls.onSurfaceVariantColor",
        ),
        cache=True,
        watch_before_use=True,
    )

    def _get_alias_icon_color(self, prop: ExtendedAliasProperty) -> list[float]:
        return self._calc_alias_icon_color(prop)

    def _calc_alias_icon_color(self, prop: ExtendedAliasProperty) -> list[float]:
        user_value = self.active_icon_color if self.active else self.inactive_icon_color
        return self._resolve_color(user_value, active=self.active)

    alias_icon_color = ExtendedAliasProperty(
        _get_alias_icon_color,
        None,
        bind=(
            "active",
            "active_icon_color",
            "inactive_icon_color",
            "theme_cls.primaryColor",
            "theme_cls.onSurfaceVariantColor",
        ),
        cache=True,
        watch_before_use=True,
    )

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self._apply_active_state_trigger()
        self._update_display_trigger()

    def on_definition(self, *_):
        if self.definition is None:
            return
        self.text = self.definition.title
        self.icon = self.definition.icon or ""
        self._update_display_trigger()

    def on_active(self, *_):
        self._apply_active_state_trigger()
        self._update_display_trigger()

    def on_theme_cls(self, *_):
        self._apply_active_state_trigger()

    def on_icon_widget(self, *_):
        if self._bound_icon_widget and self._bound_icon_widget is not self.icon_widget:
            self._bound_icon_widget.unbind(texture_size=self._on_icon_texture)
        if self.icon_widget:
            self.icon_widget.bind(texture_size=self._on_icon_texture)
            self._on_icon_texture(self.icon_widget, self.icon_widget.texture_size)
            self._apply_active_state_trigger()
        self._bound_icon_widget = self.icon_widget

    def on_text_widget(self, *_):
        if self._bound_text_widget and self._bound_text_widget is not self.text_widget:
            self._bound_text_widget.unbind(texture_size=self._on_text_texture)
        if self.text_widget:
            self.text_widget.bind(texture_size=self._on_text_texture)
            self._on_text_texture(self.text_widget, self.text_widget.texture_size)
            self._apply_active_state_trigger()
        self._bound_text_widget = self.text_widget

    def on_tabs_ref(self, *_):
        if self.tabs_ref is None:
            return
        tabs = self.tabs_ref
        has_active_text = hasattr(tabs, "active_text_color")
        has_inactive_text = hasattr(tabs, "inactive_text_color")
        has_active_icon = hasattr(tabs, "active_icon_color")
        has_inactive_icon = hasattr(tabs, "inactive_icon_color")

        if has_active_text and self.active_text_color is None:
            self.active_text_color = tabs.active_text_color
        if has_inactive_text and self.inactive_text_color is None:
            self.inactive_text_color = tabs.inactive_text_color
        if has_active_icon and self.active_icon_color is None:
            self.active_icon_color = tabs.active_icon_color
        if has_inactive_icon and self.inactive_icon_color is None:
            self.inactive_icon_color = tabs.inactive_icon_color
        self._apply_active_state_trigger()

    def on_release(self, *_):
        if self.tabs_ref is not None:
            self.tabs_ref.switch_to(self)

    def _resolve_color(self, user_value, *, active: bool) -> list[float]:
        if user_value is not None:
            return list(user_value)
        theme = self.theme_cls
        return list(theme.primaryColor if active else theme.onSurfaceVariantColor)

    def _apply_active_state(self, *_):
        if not self.text_widget:
            return
        text_color = list(self.alias_text_color)
        icon_color = list(self.alias_icon_color)
        self.text_widget.text_color = text_color
        if self.icon_widget:
            self.icon_widget.icon_color = icon_color

    def _update_display_icon(self, *_):
        if self.definition is None:
            self.display_icon = self.icon
            return
        icon_name = self.definition.icon or ""
        if self.active and self.definition.active_icon:
            icon_name = self.definition.active_icon
        elif not self.active and self.definition.inactive_icon:
            icon_name = self.definition.inactive_icon
        self.display_icon = icon_name

    def _on_icon_texture(self, *_):
        if self.icon_widget:
            self._icon_texture_size = list(self.icon_widget.texture_size)

    def _on_text_texture(self, *_):
        if self.text_widget:
            self._text_texture_size = list(self.text_widget.texture_size)


class MKVBottomTabItem(MKVTabItem):
    def _calc_alias_height(self, prop: ExtendedAliasProperty) -> float:  # noqa: D401
        return max(super()._calc_alias_height(prop), dp(48))
