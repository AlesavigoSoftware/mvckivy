from __future__ import annotations

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
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
from kivymd.uix.relativelayout import MDRelativeLayout

from kivymd.uix.behaviors import MotionDialogBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDIcon, MDLabel

from mvckivy.uix.behaviors import MKVAdaptiveBehavior
from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty
from mvckivy.properties.null_dispatcher import create_null_dispatcher


class MKVBaseDialog(
    AliasDedupeMixin, MotionDialogBehavior, MKVAdaptiveBehavior, MDCard
):
    __events__ = ("on_pre_open", "on_open", "on_pre_dismiss", "on_dismiss")

    width_offset = NumericProperty(dp(48))

    radius: VariableListProperty[list[float]] = VariableListProperty(dp(28), lenght=4)
    scrim_color: ColorProperty = ColorProperty([0, 0, 0, 0.3])
    auto_dismiss = BooleanProperty(True)
    opacity: NumericProperty[float] = NumericProperty(0)
    dismiss_on_device_type = BooleanProperty(True)

    layout_container = ObjectProperty(
        create_null_dispatcher(height=0),
        rebind=True,
        cache=True,
    )
    content_stack = ObjectProperty(
        create_null_dispatcher(children=[], height=0, minimum_height=0),
        rebind=True,
        cache=True,
    )
    icon_container = ObjectProperty(
        create_null_dispatcher(children=[], height=0),
        rebind=True,
        cache=True,
    )
    headline_container = ObjectProperty(
        create_null_dispatcher(children=[]),
        rebind=True,
        cache=True,
    )
    supporting_text_container = ObjectProperty(
        create_null_dispatcher(children=[]),
        rebind=True,
        cache=True,
    )
    content_container = ObjectProperty(
        create_null_dispatcher(children=[], height=0),
        rebind=True,
        cache=True,
    )
    button_container = ObjectProperty(
        create_null_dispatcher(children=[], height=0),
        rebind=True,
        cache=True,
    )

    _scrim: ObjectProperty[MKVDialogScrim | None] = ObjectProperty(None, allownone=True)
    _is_open = False

    def __init__(self, *args, **kwargs):
        self._layout_trigger = Clock.create_trigger(self._refresh_layout, -1)
        self._update_size_trigger = Clock.create_trigger(self._update_size, -1)
        super().__init__(*args, **kwargs)
        Window.bind(on_resize=lambda *_: self._update_size_trigger())

    def on_profile(self, profile):
        super().on_profile(profile)
        self._update_size_trigger()

    def _schedule_layout(self, *_):
        self._layout_trigger()

    def _refresh_layout(self, *_args) -> None:
        icon_container = self.icon_container
        if isinstance(icon_container, Widget):
            if getattr(icon_container, "children", None):
                icon_height = max(child.height for child in icon_container.children)
            else:
                icon_height = 0
            if hasattr(icon_container, "height"):
                icon_container.height = icon_height

        for container in (
            self.content_stack,
            self.headline_container,
            self.supporting_text_container,
            self.content_container,
            self.button_container,
        ):
            if hasattr(container, "minimum_height") and hasattr(container, "height"):
                container.height = container.minimum_height

        layout_container = self.layout_container
        if hasattr(layout_container, "height"):
            layout_container.height = (
                getattr(self.content_stack, "height", 0)
                + getattr(self.button_container, "height", 0)
                + dp(24)
            )
        if hasattr(self.content_stack, "y"):
            self.content_stack.y = getattr(self.button_container, "height", 0) + dp(24)

    def _update_size(self, *_args) -> None:
        profile = self._last_profile
        device_type = profile.device_type if profile else "desktop"
        window_width = Window.width

        max_width = dp(560) if device_type != "mobile" else dp(420)
        available = max(window_width - self.width_offset, self.width_offset)
        self.size_hint_max_x = max(self.width_offset, min(max_width, available))

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
        if self._is_open:
            return

        self.dispatch("on_pre_open")
        self._is_open = True

        if not self._scrim:
            self._scrim = MKVDialogScrim(color=self.scrim_color)

        self._update_size()
        self._update_size_trigger()

        Window.add_widget(self._scrim)
        Window.add_widget(self)
        super().on_open()
        self.dispatch("on_open")

    def on_pre_open(self, *args) -> None:
        self._refresh_layout()
        self._layout_trigger()

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
        self.dispatch("on_pre_dismiss")
        super().on_dismiss()
        self._is_open = False
        self.dispatch("on_dismiss")


class MKVDialog(MKVBaseDialog):
    def __init__(self, *args, **kwargs):
        layout_container, content_stack, button_container, containers = self._create_containers()

        kwargs = {
            **kwargs,
            "layout_container": layout_container,
            "content_stack": content_stack,
            "icon_container": containers["icon"],
            "headline_container": containers["headline"],
            "supporting_text_container": containers["supporting"],
            "content_container": containers["content"],
            "button_container": button_container,
        }

        super().__init__(*args, **kwargs)

        self.ids["layout_container"] = layout_container
        self.ids["content_stack"] = content_stack
        self.ids["icon_container"] = containers["icon"]
        self.ids["headline_container"] = containers["headline"]
        self.ids["supporting_text_container"] = containers["supporting"]
        self.ids["content_container"] = containers["content"]
        self.ids["button_container"] = button_container

        super(MKVDialog, self).add_widget(layout_container)
        self._bind_container_events()
        self._refresh_layout()
        self._layout_trigger()
        self._update_size_trigger()

    def _create_containers(self):
        layout_container = MDRelativeLayout(size_hint_y=None)

        content_stack = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(16),
            padding=(dp(24), dp(24), dp(24), dp(24)),
        )

        icon_container = MDAnchorLayout(size_hint_y=None, anchor_x="center")
        headline_container = MDBoxLayout(size_hint_y=None)
        supporting_text_container = MDBoxLayout(size_hint_y=None)
        content_container = MDBoxLayout(size_hint_y=None)

        button_container = MDBoxLayout(
            size_hint_y=None,
            padding=(dp(24), 0, dp(24), 0),
        )

        content_stack.add_widget(icon_container)
        content_stack.add_widget(headline_container)
        content_stack.add_widget(supporting_text_container)
        content_stack.add_widget(content_container)

        layout_container.add_widget(content_stack)
        layout_container.add_widget(button_container)

        containers = {
            "icon": icon_container,
            "headline": headline_container,
            "supporting": supporting_text_container,
            "content": content_container,
        }
        return layout_container, content_stack, button_container, containers

    def _bind_container_events(self) -> None:
        containers = (
            self.icon_container,
            self.headline_container,
            self.supporting_text_container,
            self.content_container,
            self.button_container,
            self.content_stack,
        )

        for container in containers:
            container.bind(children=self._schedule_layout)
            if hasattr(container, "minimum_height"):
                container.bind(minimum_height=self._schedule_layout)
            if hasattr(container, "height"):
                container.bind(height=self._schedule_layout)

    def _get_alias_height(self, prop: ExtendedAliasProperty) -> float:
        return self._calc_alias_height(prop)

    def _calc_alias_height(self, prop: ExtendedAliasProperty) -> float:
        layout_container = self.layout_container
        if getattr(layout_container, "height", None) is None:
            return 0
        return layout_container.height

    alias_height = ExtendedAliasProperty(
        _get_alias_height,
        None,
        bind=(
            "layout_container.height",
        ),
        cache=True,
        watch_before_use=True,
    )

    def _update_size(self, *_):
        super()._update_size()


class MKVDialogIcon(AliasDedupeMixin, MDIcon):
    theme_cls = ObjectProperty(
        cache=True,
        rebind=True,
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(24), dp(24)))
        kwargs.setdefault("theme_font_size", "Custom")
        kwargs.setdefault("font_size", sp(24))
        super().__init__(*args, **kwargs)

        self.fbind("alias_icon_color", self._apply_icon_color)
        self._apply_icon_color(self, self.alias_icon_color)

    @staticmethod
    def _apply_icon_color(instance, value):
        if value is not None:
            instance.icon_color = value

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

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("adaptive_height", True)
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("font_style", "Headline")
        kwargs.setdefault("role", "small")
        kwargs.setdefault("markup", True)
        super().__init__(*args, **kwargs)

        self.fbind("alias_color", self._apply_color)
        self._apply_color(self, self.alias_color)

    @staticmethod
    def _apply_color(instance, value):
        if value is not None:
            instance.color = value

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

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("adaptive_height", True)
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("font_style", "Body")
        kwargs.setdefault("role", "medium")
        kwargs.setdefault("markup", True)
        super().__init__(*args, **kwargs)

        self.fbind("alias_text_color", self._apply_text_color)
        self._apply_text_color(self, self.alias_text_color)

    @staticmethod
    def _apply_text_color(instance, value):
        if value is not None:
            instance.text_color = value

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
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        super().__init__(*args, **kwargs)

        self.bind(minimum_height=self._sync_height)
        self._sync_height(self, self.minimum_height)

    @staticmethod
    def _sync_height(instance, value):
        instance.height = value


class MKVDialogButtonContainer(MDBoxLayout):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("padding", (dp(24), 0, dp(24), 0))
        super().__init__(*args, **kwargs)

        self.bind(minimum_height=self._sync_height)
        self._sync_height(self, self.minimum_height)

    @staticmethod
    def _sync_height(instance, value):
        instance.height = value


class MKVDialogScrim(Widget):
    color = ColorProperty(None)
    alpha = NumericProperty(0)
