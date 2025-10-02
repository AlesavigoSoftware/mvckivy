from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivymd.uix.button import MDIconButton

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty


__all__ = (
    "MKVBaseSpeedDial",
    "MKVSpeedDial",
    "MKVSpeedDialAction",
    "MKVSpeedDialMainButton",
)


class MKVSpeedDialAction(MDIconButton):
    """Single action button that participates in MKVSpeedDial stack."""

    order = NumericProperty(0)
    speed_dial = ObjectProperty(None, rebind=True, allownone=True)


class MKVSpeedDialMainButton(MDIconButton):
    """Main toggle button for MKVSpeedDial."""

    speed_dial = ObjectProperty(None, rebind=True, allownone=True)


class MKVBaseSpeedDial(AliasDedupeMixin, FloatLayout):
    """Core logic for material-like speed dial widget."""

    expanded = BooleanProperty(False)
    animation_progress = NumericProperty(0.0)
    animation_duration = NumericProperty(0.22)
    animation_transition = StringProperty("out_cubic")

    main_button_size = NumericProperty(dp(56))
    action_size = NumericProperty(dp(48))
    spacing = NumericProperty(dp(12))
    stack_direction = OptionProperty("up", options=("up", "down"))
    toggle_on_main_release = BooleanProperty(True)

    root_icon = StringProperty("plus")

    actions_container = ObjectProperty(None, rebind=True, allownone=True)
    main_button = ObjectProperty(None, rebind=True, allownone=True)

    actions_count = NumericProperty(0)

    main_button_x = NumericProperty(0.0)
    main_button_y = NumericProperty(0.0)
    main_button_width = NumericProperty(0.0)
    main_button_height = NumericProperty(0.0)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._layout_trigger = Clock.create_trigger(self._update_layout, 0)
        self._refresh_actions_trigger = Clock.create_trigger(self._refresh_actions, 0)
        self._pending_actions: list[tuple[MKVSpeedDialAction, tuple, dict]] = []
        self._actions_sorted: list[MKVSpeedDialAction] = []
        self._actions_container_uid: Optional[int] = None
        self._bound_actions_container: Optional[Widget] = None
        self._bound_main_button: Optional[Widget] = None
        self._main_button_uids: dict[str, Optional[int]] = {}
        self.main_button_width = float(self.main_button_size)
        self.main_button_height = float(self.main_button_size)

    # ------------------------------------------------------------------
    # Alias helpers
    # ------------------------------------------------------------------
    def _get_alias_stack_height(self, prop: ExtendedAliasProperty) -> float:
        return self._calc_alias_stack_height(prop)

    def _calc_alias_stack_height(self, prop: ExtendedAliasProperty) -> float:
        return float(self.main_button_height) + self._calc_total_offset()

    alias_stack_height = ExtendedAliasProperty(
        _get_alias_stack_height,
        None,
        bind=(
            "main_button_height",
            "action_size",
            "spacing",
            "actions_count",
        ),
        cache=False,
        watch_before_use=True,
    )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def on_kv_post(self, base_widget) -> None:
        super().on_kv_post(base_widget)
        self._rebind_main_button(self.main_button)
        self._rebind_actions_container(self.actions_container)
        self.animation_progress = 1.0 if self.expanded else 0.0
        self._layout_trigger()

    def on_main_button(self, _instance: AliasDedupeMixin, value: Widget) -> None:
        self._rebind_main_button(value)

    def on_actions_container(self, _instance: AliasDedupeMixin, value: Widget) -> None:
        self._rebind_actions_container(value)

    def on_toggle_on_main_release(self, *_: Any) -> None:
        self._rebind_main_button(self.main_button)

    def on_main_button_size(self, *_: Any) -> None:
        if self._bound_main_button is None:
            size = float(self.main_button_size)
            self.main_button_width = size
            self.main_button_height = size
            self._layout_trigger()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def toggle(self) -> None:
        self.expanded = not self.expanded

    def open(self) -> None:
        self.expanded = True

    def close(self) -> None:
        self.expanded = False

    # ------------------------------------------------------------------
    # Property hooks
    # ------------------------------------------------------------------
    def on_expanded(self, *_: Any) -> None:
        Animation.cancel_all(self, "animation_progress")
        target = 1.0 if self.expanded else 0.0
        Animation(
            animation_progress=target,
            d=float(self.animation_duration),
            t=self.animation_transition,
        ).start(self)

    def on_animation_progress(self, *_: Any) -> None:
        self._layout_trigger()

    def on_spacing(self, *_: Any) -> None:
        self._layout_trigger()

    def on_action_size(self, *_: Any) -> None:
        self._layout_trigger()

    def on_stack_direction(self, *_: Any) -> None:
        self._layout_trigger()

    def on_actions_count(self, *_: Any) -> None:
        self._layout_trigger()

    def on_root_icon(self, *_: Any) -> None:
        button = self._bound_main_button
        if isinstance(button, MDIconButton):
            button.icon = self.root_icon

    # ------------------------------------------------------------------
    # Widget management
    # ------------------------------------------------------------------
    def add_widget(self, widget: Widget, *args: Any, **kwargs: Any) -> None:
        if isinstance(widget, MKVSpeedDialAction):
            container = self._bound_actions_container
            if container is None:
                self._pending_actions.append((widget, args, kwargs))
            else:
                container.add_widget(widget, *args, **kwargs)
                self._refresh_actions_trigger()
            return
        super().add_widget(widget, *args, **kwargs)
        if isinstance(widget, MKVSpeedDialMainButton) and self.main_button is None:
            self.main_button = widget

    def remove_widget(self, widget: Widget) -> None:
        container = self._bound_actions_container
        if isinstance(widget, MKVSpeedDialAction) and container is not None:
            if widget in container.children:
                container.remove_widget(widget)
                self._refresh_actions_trigger()
                return
        super().remove_widget(widget)
        if widget is self._bound_main_button:
            self.main_button = None
            self._layout_trigger()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _calc_total_offset(self) -> float:
        if self.actions_count <= 0:
            return 0.0
        step = float(self.action_size + self.spacing)
        return float(self.actions_count) * step

    def _rebind_main_button(self, button: Optional[Widget]) -> None:
        self._clear_main_button_bindings()
        self._bound_main_button = button

        if isinstance(button, Widget) and hasattr(button, "speed_dial"):
            button.speed_dial = self

        if button is None:
            size = float(self.main_button_size)
            self.main_button_width = size
            self.main_button_height = size
            self.main_button_x = 0.0
            self.main_button_y = 0.0
            self._layout_trigger()
            return

        pos_uid = button.fbind("pos", self._on_main_button_geometry)
        size_uid = button.fbind("size", self._on_main_button_geometry)
        self._main_button_uids = {
            "pos": pos_uid,
            "size": size_uid,
        }

        if self.toggle_on_main_release:
            release_uid = button.fbind("on_release", self._on_main_button_release)
            self._main_button_uids["on_release"] = release_uid

        self._store_main_button_geometry()
        if isinstance(button, MDIconButton):
            button.icon = self.root_icon
        self._layout_trigger()

    def _clear_main_button_bindings(self) -> None:
        button = self._bound_main_button
        if button is None or not self._main_button_uids:
            self._main_button_uids = {}
            return
        for name, uid in list(self._main_button_uids.items()):
            if uid is None:
                continue
            try:
                button.funbind_uid(name, uid)
            except AttributeError:
                button.unbind_uid(name, uid)
        self._main_button_uids = {}

    def _rebind_actions_container(self, container: Optional[Widget]) -> None:
        if (
            self._bound_actions_container is not None
            and self._actions_container_uid is not None
        ):
            try:
                self._bound_actions_container.funbind_uid(
                    "children", self._actions_container_uid
                )
            except AttributeError:
                self._bound_actions_container.unbind_uid(
                    "children", self._actions_container_uid
                )
        self._actions_container_uid = None
        self._bound_actions_container = container

        if container is None:
            return

        uid = container.fbind("children", self._on_actions_children)
        self._actions_container_uid = uid
        self._flush_pending_actions()
        self._refresh_actions()

    def _flush_pending_actions(self) -> None:
        if not self._pending_actions:
            return
        container = self._bound_actions_container
        if container is None:
            return
        for widget, args, kwargs in self._pending_actions:
            container.add_widget(widget, *args, **kwargs)
        self._pending_actions.clear()
        self._refresh_actions_trigger()

    def _on_actions_children(self, *_: Any) -> None:
        self._refresh_actions_trigger()

    def _refresh_actions(self, *_: Any) -> None:
        container = self._bound_actions_container
        if container is None:
            self._actions_sorted = []
            self.actions_count = 0
            return

        children = list(container.children)
        fallback_index = {child: idx for idx, child in enumerate(reversed(children))}
        actions: list[MKVSpeedDialAction] = [
            child for child in children if isinstance(child, MKVSpeedDialAction)
        ]
        actions.sort(key=lambda act: (act.order, fallback_index.get(act, 0)))

        for action in actions:
            if hasattr(action, "speed_dial") and action.speed_dial is not self:
                action.speed_dial = self

        self._actions_sorted = actions
        self.actions_count = len(actions)
        self._layout_trigger()

    def _on_main_button_release(self, *_: Any) -> None:
        self.toggle()

    def _on_main_button_geometry(self, *_: Any) -> None:
        self._store_main_button_geometry()
        self._layout_trigger()

    def _store_main_button_geometry(self) -> None:
        button = self._bound_main_button
        if isinstance(button, Widget):
            self.main_button_x = float(button.x)
            self.main_button_y = float(button.y)
            width, height = button.size
            if not width and not height:
                width = height = float(self.main_button_size)
            self.main_button_width = float(width)
            self.main_button_height = float(height)
        else:
            size = float(self.main_button_size)
            self.main_button_width = size
            self.main_button_height = size
            self.main_button_x = 0.0
            self.main_button_y = 0.0

    def _update_layout(self, *_: Any) -> None:
        actions = list(self._actions_sorted)

        if not actions:
            return

        action_size = float(self.action_size)
        base_x = (
            float(self.main_button_x)
            + (float(self.main_button_width) - action_size) / 2.0
        )
        anchor_y = (
            float(self.main_button_y)
            + (float(self.main_button_height) - action_size) / 2.0
        )
        step = float(self.action_size + self.spacing)
        progress = max(0.0, min(1.0, float(self.animation_progress)))
        direction = 1.0 if self.stack_direction == "up" else -1.0

        for index, action in enumerate(actions):
            offset = step * float(index + 1)
            target_y = anchor_y + direction * offset
            current_y = anchor_y + (target_y - anchor_y) * progress
            if getattr(action, "size_hint", None) is not None:
                action.size_hint = (None, None)
            action.size = (action_size, action_size)
            action.pos = (base_x, current_y)
            action.opacity = progress
            action.disabled = progress < 0.01


class MKVSpeedDial(MKVBaseSpeedDial):
    """Concrete MKVSpeedDial with default KV layout."""

    pass
