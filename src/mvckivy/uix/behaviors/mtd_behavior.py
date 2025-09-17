from __future__ import annotations

import logging
from typing import Callable, Any, TYPE_CHECKING
from kivy.core.window import Window
from kivy.properties import ObjectProperty, AliasProperty
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.event import EventDispatcher
from kivy.app import App


if TYPE_CHECKING:
    from mvckivy.app import MVCApp


logger = logging.getLogger("mvckivy")


class MTDWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app: MVCApp = App.get_running_app()

    def _get_rendered(self) -> bool:
        return bool(self.parent)

    rendered = AliasProperty(_get_rendered, None, bind=["parent"], cache=True)

    def on_rendered(self, instance, value: bool):
        pass

    def sbind(self, **kwargs: Callable[..., None]):
        """
        Single bind to the widget event.
        Checks whether callback is already bound, in this case does nothing,
        otherwise binds the new callback to the specified event type.
        :return:
        :rtype:
        """
        for cb_name, cb in kwargs.items():
            if cb not in self.get_property_observers(cb_name):
                self.bind(**{cb_name: cb})


def render_only(func: Callable[..., Any]):
    def wrapper(self: MTDWidget, *args, **kwargs):
        if self.rendered:
            res = func(self, *args, **kwargs)
            return res

        return wrapper


class TooManyChildrenException(Exception):
    pass


class SingleInterfaceWidget(Widget):
    __events__ = ("on_add_interface", "on_remove_interface")
    _interface: ObjectProperty[MTDWidget | None] = ObjectProperty(None, allownone=True)

    def add_widget(self, widget: MTDWidget, *args, **kwargs) -> None:
        if len(self.children) > 1:
            raise TooManyChildrenException(
                f"{self.__class__}: SingleInterfaceWidget can only have one interface per time."
            )

        if widget in self.children:
            return

        self.clear_widgets()
        self._interface = widget
        super().add_widget(self._interface, *args, **kwargs)
        self.dispatch("on_add_interface", self._interface)

    def on_add_interface(self, interface: MTDWidget) -> None:
        """
        Calls from Clock.schedule_once on "widget.parent" setting.
        A single difference from calling this method without using Clock
        appears on app initialization (on the first call).
        Other times these ways are equal.

        Replaces _init_all method from MVCBehavior
        because has completely same functionality and even calls the same way on app start.
        :return: None
        """

    def on_remove_interface(self, interface: MTDWidget) -> None:
        """

        :return:
        :rtype:
        """

    def clear_widgets(self, children: list | None = None) -> None:
        self._interface = None
        return super().clear_widgets()

    def remove_widget(self, widget: MTDWidget) -> None:
        super().remove_widget(widget)
        if widget is self._interface:
            self.dispatch("on_remove_interface", self._interface)
            self._interface = None

    def on__interface(self, instance, value) -> None:
        pass


class MTDBehavior(EventDispatcher):
    __events__ = ("on_mobile", "on_tablet", "on_desktop", "on_portrait", "on_landscape")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app: MVCApp = App.get_running_app()
        self._initialize_dispatchers()

    def _initialize_dispatchers(self) -> None:
        self.app.model.bind(
            device_type=self.on_device_type
        )  # on_device_type calls on app start by AppController
        self.app.model.bind(device_orientation=self.on_device_type)
        Window.bind(on_resize=self.on_window_resize)

    def on_window_resize(self, window, width, height) -> None:
        pass

    def on_device_orientation(self, widget, device_orientation: str) -> None:
        if device_orientation not in ["portrait", "landscape"]:
            raise ValueError("Invalid device orientation: %s" % device_orientation)

        self.dispatch(f"on_{device_orientation}")

    def on_device_type(self, widget, device_type: str) -> None:
        if device_type not in ["mobile", "tablet", "desktop"]:
            raise ValueError("Invalid device type: %s" % device_type)

        self.dispatch(f"on_{device_type}")

    def on_portrait(self) -> None:
        pass

    def on_landscape(self) -> None:
        pass

    def on_mobile(self) -> None:
        pass

    def on_tablet(self) -> None:
        pass

    def on_desktop(self) -> None:
        pass


class MTDBuilder(MTDBehavior, SingleInterfaceWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widgets: dict[str, dict[str, MTDWidget | None]] = {
            "mobile": {
                "portrait": None,
                "landscape": None,
            },
            "tablet": {
                "portrait": None,
                "landscape": None,
            },
            "desktop": {
                "portrait": None,
                "landscape": None,
            },
        }

    def add_widget(self, widget: MTDWidget, *args, render=False, **kwargs):
        if not isinstance(widget, MTDWidget):
            raise ValueError("Widget must be the instance of MTDWidget class.")

        if render:
            super().add_widget(widget, *args, **kwargs)
        else:
            self._distribute_widget(widget)

    def _distribute_widget(self, widget: MTDWidget) -> None:
        platforms = list(widget.destination_device_platform)
        orientations = list(widget.destination_device_orientation)
        device_types = list(widget.destination_device_type)

        if self.app.model.platform not in platforms:
            return

        for device_type in device_types:
            for orientation in orientations:
                self._register_widget(device_type, orientation, widget)

    def _register_widget(self, device_type, orientation, widget) -> None:
        try:
            dtype = self._widgets[device_type]
        except KeyError:
            logger.error(
                ValueError(
                    f"{self.__class__}: Device type {device_type} not in {MTDWidget.destination_device_type}."
                )
            )
            return

        try:
            dtype[orientation] = widget
        except KeyError:
            logger.error(
                ValueError(
                    f"{self.__class__}: Device orientation {orientation} not in {MTDWidget.destination_device_orientation}."
                )
            )
            return

    def on_device_orientation(self, widget, device_orientation: str) -> None:
        super().on_device_orientation(widget, device_orientation)
        self._add_widget(
            device_type=self.app.model.device_type,
            device_orientation=device_orientation,
        )

    def on_device_type(self, widget, device_type: str) -> None:
        super().on_device_type(widget, device_type)
        self._add_widget(
            device_type=device_type,
            device_orientation=self.app.model.device_orientation,
        )

    def _add_widget(self, device_type: str, device_orientation: str):
        widget = self._widgets[device_type][device_orientation]
        if widget is None:
            logger.debug(
                f"{self.__class__}: MTDWidget not implemented, {device_type} {device_orientation}."
            )
            widget = MTDWidget()
            self._widgets[device_type][device_orientation] = widget

        Clock.schedule_once(lambda dt: self.add_widget(widget, render=True), 0)
