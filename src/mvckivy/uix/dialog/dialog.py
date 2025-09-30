from __future__ import annotations

from kivy.core.window import Window
from kivy.properties import (
    VariableListProperty,
    ColorProperty,
    BooleanProperty,
    ObjectProperty,
)
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDIcon, MDLabel

from mvckivy.uix.behaviors import MKVAdaptiveBehavior
from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty
from mvckivy.properties.null_dispatcher import create_null_dispatcher


from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, OptionProperty

from kivymd.uix.behaviors import ScaleBehavior
from kivymd.uix.behaviors.motion_behavior import MotionBase  # как и было


class MotionDialogBehavior(ScaleBehavior, MotionBase):
    manage_window = BooleanProperty(True)
    is_open = BooleanProperty(False)

    scrim = ObjectProperty(None, allownone=True, rebind=True)
    scrim_alpha = NumericProperty(0.4)
    scrim_color: ColorProperty = ColorProperty([0, 0, 0, scrim_alpha.defaultvalue])

    show_transition = StringProperty("out_expo")
    hide_transition = StringProperty("in_cubic")
    show_duration = NumericProperty(0.40)
    hide_duration = NumericProperty(0.30)
    start_scale = NumericProperty(0.5)

    scale_anchor = OptionProperty("center", options=("center", "top"))

    def motion_open(self) -> None:
        """Полный цикл: смонтировать scrim и диалог, запустить show-анимацию."""
        if self.is_open or not self.manage_window:
            return

        # Событие жизненного цикла (если объявлено хостом)
        self.dispatch("on_pre_open")

        # Готовим scrim, если не задан
        self.scrim = self._create_scrim()

        # Порядок важен: сначала scrim, потом диалог (над ним)
        if self.scrim is not None:
            Window.add_widget(self.scrim)
        Window.add_widget(self)

        self.is_open = True

        # Дадим лэйауту стабилизироваться, затем сыграем анимацию
        Clock.schedule_once(self._play_show, 0)

        if self.is_event_type("on_open"):
            self.dispatch("on_open")

    def _create_scrim(self) -> MKVDialogScrim:
        """Создание scrim с нулевой прозрачностью для анимации."""
        if self.scrim is not None:
            return self.scrim

        return MKVDialogScrim(color=self.scrim_color[:3] + [0])

    def motion_dismiss(self) -> None:
        """Полный цикл: запустить hide-анимацию и по завершении демонтировать."""
        if not self.is_open:
            return

        self.dispatch("on_pre_dismiss")
        self._play_hide()
        self.dispatch("on_dismiss")

    def _set_scale_center(self) -> None:
        cy = self.top if self.scale_anchor == "top" else self.center_y
        self.scale_value_center = (self.center_x, cy)

    def _play_show(self, *_):
        # Контейнер
        self.opacity = 0
        self.scale_value_x = self.start_scale
        self.scale_value_y = self.start_scale
        self._set_scale_center()

        anim = Animation(
            opacity=1,
            scale_value_x=1,
            scale_value_y=1,
            t=self.show_transition,
            d=self.show_duration,
        )
        anim.start(self)

        # Scrim
        if self.scrim is not None:
            Animation(alpha=float(self.scrim_alpha), d=self.show_duration).start(
                self.scrim
            )

    def _play_hide(self) -> None:
        # Контейнер
        anim = Animation(
            opacity=0,
            scale_value_x=self.start_scale,
            scale_value_y=self.start_scale,
            t=self.hide_transition,
            d=self.hide_duration,
        )

        def _finish(*_):
            self._unmount_from_window()

        anim.bind(on_complete=_finish)
        anim.start(self)

        # Scrim
        if self.scrim is not None:
            Animation(alpha=0, d=self.hide_duration).start(self.scrim)

    def _unmount_from_window(self) -> None:
        """Удаление из Window после завершения hide-анимации."""
        if not self.manage_window:
            return
        if self.parent is not None:
            Window.remove_widget(self)
        if self.scrim is not None and self.scrim.parent is not None:
            Window.remove_widget(self.scrim)
        self.scrim = None
        self.is_open = False


class MKVBaseDialog(
    AliasDedupeMixin, MotionDialogBehavior, MKVAdaptiveBehavior, MDCard
):
    __events__ = ("on_pre_open", "on_open", "on_pre_dismiss", "on_dismiss")

    radius: VariableListProperty[list[float]] = VariableListProperty(dp(28), lenght=4)
    auto_dismiss = BooleanProperty(True)
    opacity: NumericProperty[float] = NumericProperty(0)

    content_stack = ObjectProperty(
        create_null_dispatcher(children=[], height=0),
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
        self._layout_trigger = Clock.create_trigger(self._refresh_layout, 0)
        self._update_size_trigger = Clock.create_trigger(self._update_size, 0)
        Window.bind(on_resize=lambda *_: self._update_size_trigger())
        super().__init__(*args, **kwargs)

    def _refresh_layout(self, *args) -> None:
        pass

    def _update_size(self, *args) -> None:
        pass

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
        self.motion_open()

    def dismiss(self, *args) -> None:
        self.motion_dismiss()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) and self.auto_dismiss and self.is_open:
            self.motion_dismiss()
            return True
        return super().on_touch_down(touch)

    def on_pre_open(self, *args) -> None:
        pass

    def on_open(self, *args) -> None:
        pass

    def on_dismiss(self, *args) -> None:
        pass

    def on_pre_dismiss(self, *args) -> None:
        pass

    def on_press(self, *args) -> None:
        pass


class MKVDialog(MKVBaseDialog):
    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self._bind_containers()
        self._layout_trigger()

    def _bind_containers(self):
        self.icon_container.bind(
            children=lambda *args: self._layout_trigger(),
            height=lambda *args: self._layout_trigger(),
        )

    def _refresh_layout(self, *_):
        self.icon_container.height = max(
            (child.height for child in self.icon_container.children), default=0
        )

    def _update_size(self, *_):
        window_width = Window.width
        width_offset = dp(48)

        self.size_hint_max_x = max(
            width_offset,
            min(
                dp(560) if self._last_profile.device_type != "mobile" else dp(420),
                window_width - width_offset,
            ),
        )


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
