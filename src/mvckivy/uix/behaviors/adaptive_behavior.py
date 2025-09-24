from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Any, TYPE_CHECKING, Literal
from kivy.properties import ObjectProperty, AliasProperty, ListProperty
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.event import EventDispatcher
from kivy.app import App


if TYPE_CHECKING:
    from mvckivy.app import MKVApp


logger = logging.getLogger("mvckivy")

DeviceType = Literal["mobile", "tablet", "desktop"]
DeviceOrientation = Literal["portrait", "landscape"]
InputMode = Literal["touch", "mouse"]


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    device_type: DeviceType
    device_orientation: DeviceOrientation


class MKVAdaptiveBehavior(EventDispatcher):
    __events__ = (
        "on_profile",
        "on_mobile",
        "on_tablet",
        "on_desktop",
        "on_portrait",
        "on_landscape",
        "on_input_mode",
        "on_touch",
        "on_mouse",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app: MKVApp = App.get_running_app()
        self._last_profile: DeviceProfile | None = None
        self._app.bind(on_device_profile_changed=self._on_device_profile_changed)
        self._app.bind(input_mode=self._on_input_mode)

        Clock.schedule_once(
            lambda dt: self._on_device_profile_changed(
                self._app, self._app.device_type, self._app.device_orientation
            ),
            0,
        )
        Clock.schedule_once(
            lambda dt: self._on_input_mode(self._app, self._app.input_mode), 0
        )

    def _on_input_mode(self, app: MKVApp, mode: InputMode) -> None:
        self.dispatch("on_input_mode", self._app, mode)
        if mode == "touch":
            self.dispatch("on_touch")
        elif mode == "mouse":
            self.dispatch("on_mouse")

    def on_input_mode(self, app: MKVApp, mode: InputMode) -> None:
        pass

    def on_touch(self) -> None:
        pass

    def on_mouse(self) -> None:
        pass

    def on_profile(self, profile: DeviceProfile) -> None:
        pass

    def on_mobile(self) -> None:
        pass

    def on_tablet(self) -> None:
        pass

    def on_desktop(self) -> None:
        pass

    def on_portrait(self) -> None:
        pass

    def on_landscape(self) -> None:
        pass

    def on_parent(self, instance, parent) -> None:
        if parent is None and self._app is not None:
            try:
                self._app.funbind(
                    "on_device_profile_changed", self._on_device_profile_changed
                )
            finally:
                self._app = None

    def _on_device_profile_changed(
        self, _app, device_type: DeviceType, device_orientation: DeviceOrientation
    ) -> None:
        new_profile = DeviceProfile(device_type, device_orientation)
        old = self._last_profile
        if new_profile == old:
            return

        self._last_profile = new_profile

        # общий снапшот
        self.dispatch("on_profile", new_profile)

        # частичные — только по изменившимся полям
        if old is None or new_profile.device_type != old.device_type:
            t = new_profile.device_type
            if t == "mobile":
                self.dispatch("on_mobile")
            elif t == "tablet":
                self.dispatch("on_tablet")
            else:  # "desktop"
                self.dispatch("on_desktop")

        if old is None or new_profile.device_orientation != old.device_orientation:
            o = new_profile.device_orientation
            if o == "portrait":
                self.dispatch("on_portrait")
            else:  # "landscape"
                self.dispatch("on_landscape")
