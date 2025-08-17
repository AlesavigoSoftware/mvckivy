from __future__ import annotations

from datetime import datetime
from kivy.clock import Clock

from typing import Any, Optional

from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivymd.uix.snackbar import (
    MDSnackbar,
    MDSnackbarButtonContainer,
    MDSnackbarCloseButton,
)

from mvckivy import MTDBehavior


class WrongWidgetTypeException(Exception):
    pass


class NotificationManager(Widget, MTDBehavior):
    max_opened_notifications = NumericProperty(3)
    y_shift = NumericProperty(dp(20))
    y_shift_duration = NumericProperty(0.5)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.add_widget(self)
        self.notifications_data: list[dict[str, Any]] = []
        self.__y_shift_positions = {}

    def on_device_type(self, widget, device_type: str):
        super().on_device_type(widget, device_type)
        self.dismiss_all()

    def _save_notification_data(self, notification: Notification):
        self.notifications_data.append(
            {
                "creation_time": datetime.now().strftime("%H:%M:%S"),
                "text": notification.text,
                "supporting_text": notification.supporting_text,
                "notification_type": notification.notification_type,
                "button_name": notification.button_name,
                "button_cb": notification.button_cb,
            }
        )

    def add_widget(self, widget, index=0, canvas=None):
        if isinstance(widget, Notification):
            for index, notification in enumerate(self.children[::-1], start=1):
                if index >= self.max_opened_notifications:
                    notification.dismiss()
                else:
                    purpose_pos: Optional[float] = self.__y_shift_positions.get(
                        widget, None
                    )
                    cur_pos: float = notification.y

                    if purpose_pos is not None:
                        self.__y_shift_positions[widget] = (
                            purpose_pos - notification._height - self.y_shift
                        )
                    else:
                        self.__y_shift_positions[widget] = (
                            cur_pos - notification._height - self.y_shift
                        )

                    Animation(
                        y=self.__y_shift_positions[widget],
                        t="out_bounce",
                        d=self.y_shift_duration,
                    ).start(notification)

        else:
            raise WrongWidgetTypeException(
                f"NotificationManager must contain {Notification.__class__} instances only"
            )

        self.children.append(widget)
        self._save_notification_data(widget)

    def remove_widget(self, widget):
        for notification in self.children[::1]:
            if notification is widget:
                self.children.remove(widget)
                return
            else:
                Animation(
                    y=notification.y + notification._height + self.y_shift,
                    t="out_bounce",
                    d=self.y_shift_duration,
                ).start(notification)

    def dismiss_all(self):
        for notification in self.children[::1]:
            notification.dismiss()


class Notification(MDSnackbar):
    def __init__(
        self,
        *args,
        text=None,
        supporting_text=None,
        notification_type=None,
        button_name=None,
        button_cb=None,
        **kwargs,
    ):
        self.text = text
        self.supporting_text = supporting_text
        self.notification_type = notification_type
        self.button_name = button_name
        self.button_cb = button_cb
        self._manager: NotificationManager = self.__get_notification_manager()
        super().__init__(*args, **kwargs)

    @staticmethod
    def __get_notification_manager():
        for widget in Window.children:
            if isinstance(widget, NotificationManager):
                return widget

    def open(self) -> None:
        Window.add_widget(self)

        def __open(*_):
            self._height = self.height
            self.height = 0
            self._manager.add_widget(self)
            anim = Animation(
                opacity=1,
                height=self._height,
                t=self.show_transition,
                d=self.show_duration,
            )
            anim.bind(
                on_complete=lambda *args: Clock.schedule_interval(
                    self._wait_interval, 1
                )
            )
            anim.start(self)
            self.dispatch("on_open")

        Clock.schedule_once(__open, 0)

    def dismiss(self, *args) -> None:
        def remove_snackbar(*_):
            Window.parent.remove_widget(self)
            self.height = self._height
            self.dispatch("on_dismiss")

        self._manager.remove_widget(self)

        Clock.unschedule(self._wait_interval)
        anim = Animation(
            opacity=0,
            height=0,
            t=self.hide_transition,
            d=self.hide_duration,
        )
        anim.bind(on_complete=remove_snackbar)
        anim.start(self)

    def on_dismiss(self, *args):
        pass

    def on_open(self, *args) -> None:
        pass

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, MDSnackbarButtonContainer):
            for child in widget.children:
                if isinstance(child, MDSnackbarCloseButton):
                    child.bind(on_release=self.dismiss)
                    return super().add_widget(widget)

        return super().add_widget(widget, *args, **kwargs)


class InfoNotification(Notification):
    pass


class FailureNotification(Notification):
    pass


class ErrorNotification(Notification):
    pass


class SuccessNotification(Notification):
    pass
