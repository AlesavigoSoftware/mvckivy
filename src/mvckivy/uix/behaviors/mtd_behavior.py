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


class MTDWidget(Widget):
    d_plat = ListProperty(["*"])  # ["*"] или ["android","ios","win","linux",...]
    d_types = ListProperty(["*"])  # ["*"] или ["mobile","tablet","desktop"]
    d_orients = ListProperty(["*"])  # ["*"] или ["portrait","landscape"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # карта уникальных подписок: (event_name_normalized, callback) -> uid
        self._sbind_registry: dict[str, set[int]] = {}

    def _get_rendered(self) -> bool:
        return bool(self.parent)

    rendered = AliasProperty(_get_rendered, None, bind=["parent"], cache=True)

    def on_rendered(self, instance, value: bool):
        pass

    def sbind(self, **kwargs):
        """
        sbind(on_size=cb) — привяжет cb только если ранее не привязывали.
        """
        for ev, cb in kwargs.items():
            bucket = self._sbind_registry.setdefault(ev, set())
            key = id(cb)
            if key in bucket:
                continue
            self.bind(**{ev: cb})
            bucket.add(key)


def render_only(func: Callable[..., Any]):
    def wrapper(self: MTDWidget, *args, **kwargs):
        if self.rendered:
            res = func(self, *args, **kwargs)
            return res

        return wrapper


class TooManyChildrenException(Exception):
    pass


class SingleInterfaceWidget(FloatLayout):
    __events__ = ("on_add_interface", "on_remove_interface")
    _interface: ObjectProperty[Widget | None] = ObjectProperty(None, allownone=True)

    def add_widget(self, widget: Widget, *args, **kwargs) -> None:
        self.clear_widgets()
        self._interface = widget
        super().add_widget(widget, *args, **kwargs)
        Clock.schedule_once(lambda dt: self.dispatch("on_add_interface", widget), 0)

    def remove_widget(self, widget: Widget, *args, **kwargs) -> None:
        was_interface = widget is self._interface
        super().remove_widget(widget, *args, **kwargs)
        if was_interface:
            self._interface = None
            self.dispatch("on_remove_interface", widget)

    def clear_widgets(self, children: list | None = None) -> None:
        if self._interface is not None and self._interface in self.children:
            self.remove_widget(self._interface)
        else:
            super().clear_widgets(children)

    def on_add_interface(self, interface: Widget) -> None:
        pass

    def on_remove_interface(self, interface: Widget | None) -> None:
        pass


DeviceType = Literal["mobile", "tablet", "desktop"]
DeviceOrientation = Literal["portrait", "landscape"]


@dataclass(frozen=True, slots=True)
class MTDProfile:
    device_type: DeviceType
    device_orientation: DeviceOrientation


class MTDBehavior(EventDispatcher):
    __events__ = (
        "on_profile",
        "on_mobile",
        "on_tablet",
        "on_desktop",
        "on_portrait",
        "on_landscape",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()
        self._last_profile: MTDProfile | None = None
        self._app.bind(on_device_profile_changed=self._on_device_profile_changed)

    def on_profile(self, profile: MTDProfile) -> None:
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
        new_profile = MTDProfile(device_type, device_orientation)
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


class MTDBuilder(SingleInterfaceWidget, MTDBehavior):
    """
    Регистрирует MTDWidget-кандидаты (через add_widget(..., render=False))
    и показывает наиболее специфичный под (app.device_type, app.device_orientation).
    Если подходящего нет — подставляет пустой MTDWidget.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self._candidates: list[MTDWidget] = []

        Clock.schedule_once(
            lambda dt: self._switch_to(
                self.app.device_type, self.app.device_orientation
            ),
            0,
        )

    def add_widget(self, widget: MTDWidget, *args, render: bool = False, **kwargs):
        if not isinstance(widget, MTDWidget):
            raise ValueError("Widget must be an instance of MTDWidget.")
        if render:
            return super().add_widget(widget, *args, **kwargs)
        self._register_candidate(widget)

    def _register_candidate(self, widget: MTDWidget) -> None:
        if "*" not in widget.d_plat and self.app.platform not in widget.d_plat:
            return
        self._candidates.append(widget)

    def _type_spec(self, w: MTDWidget, dt: DeviceType) -> int | None:
        lst = w.d_types
        if "*" in lst:
            return 0
        if dt in lst:
            return 100 - len(lst)
        return None

    def _orient_spec(self, w: MTDWidget, ori: DeviceOrientation) -> int | None:
        lst = w.d_orients
        if "*" in lst:
            return 0
        if ori in lst:
            return 100 - len(lst)
        return None

    def _score(
        self, w: MTDWidget, dt: DeviceType, ori: DeviceOrientation, order: int
    ) -> tuple[int, int, int] | None:
        # платформа уже отфильтрована при регистрации
        ts = self._type_spec(w, dt)
        if ts is None:
            return None
        os = self._orient_spec(w, ori)
        if os is None:
            return None
        # при равной специфичности выигрывает более поздняя регистрация (order больше)
        return ts, os, order

    def _select_best(self, dt: DeviceType, ori: DeviceOrientation) -> MTDWidget | None:
        best: MTDWidget | None = None
        best_score: tuple[int, int, int] = (-1, -1, -1)
        for idx, w in enumerate(self._candidates):
            sc = self._score(w, dt, ori, idx)
            if sc is None:
                continue
            if sc > best_score:
                best_score = sc
                best = w
        return best

    def _switch_to(self, dt: DeviceType, ori: DeviceOrientation) -> None:
        widget = self._select_best(dt, ori) or MTDWidget()
        super().add_widget(widget)

    def on_profile(self, profile: MTDProfile) -> None:
        self._switch_to(profile.device_type, profile.device_orientation)
