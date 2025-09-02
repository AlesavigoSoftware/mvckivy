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

from kivymd.uix.behaviors import MotionDialogBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDIcon, MDLabel

from mvckivy.uix.behaviors import MVCBehavior, MTDBehavior


class MDAdaptiveDialog(MDCard, MotionDialogBehavior, MVCBehavior, MTDBehavior):
    __events__ = ("on_pre_open", "on_open", "on_pre_dismiss", "on_dismiss")

    width_offset = NumericProperty(dp(48))

    radius = VariableListProperty(dp(28), lenght=4)
    scrim_color = ColorProperty([0, 0, 0, 0.3])
    auto_dismiss = BooleanProperty(True)
    dismiss_on_device_type = BooleanProperty(True)

    _scrim: ObjectProperty[MDAdaptiveDialogScrim] = ObjectProperty()
    _is_open = False

    def __init__(self, *args, ignore_parent_mvc=True, **kwargs):
        super().__init__(*args, ignore_parent_mvc=ignore_parent_mvc, **kwargs)
        self.register_event_type("on_open")
        self.register_event_type("on_pre_open")
        self.register_event_type("on_dismiss")
        self.register_event_type("on_pre_dismiss")
        self.opacity = 0
        Window.bind(on_resize=self.update_size)

    def on_device_type(self, widget, device_type: str):
        super().on_device_type(widget, device_type)
        if self.dismiss_on_device_type:
            self.dismiss()

    def update_size(self, *args):
        window_width = args[1]
        window_height = args[2]

        self.size_hint_max_x = max(
            self.width_offset,
            min(
                dp(560) if self.app.model.device_type != "mobile" else dp(420),
                window_width - self.width_offset,
            ),
        )

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, MDAdaptiveDialogIcon):
            self.ids.icon_container.add_widget(widget)
        elif isinstance(widget, MDAdaptiveDialogHeadlineText):
            self.ids.headline_container.add_widget(widget)
        elif isinstance(widget, MDAdaptiveDialogSupportingText):
            self.ids.supporting_text_container.add_widget(widget)
        elif isinstance(widget, MDAdaptiveDialogContentContainer):
            self.ids.content_container.add_widget(widget)
        elif isinstance(widget, MDAdaptiveDialogButtonContainer):
            self.ids.button_container.add_widget(widget)
        else:
            return super().add_widget(widget)

    def open(self) -> None:
        """Show the dialog."""

        if self._is_open:
            return

        self.dispatch("on_pre_open")
        self._is_open = True

        if not self._scrim:
            self._scrim = MDAdaptiveDialogScrim(color=self.scrim_color)

        Window.add_widget(self._scrim)
        Window.add_widget(self)
        super().on_open()
        self.dispatch("on_open")

    def on_pre_open(self, *args) -> None:
        self.ids.icon_container.height = self.ids.icon_container.children[
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


class MDAdaptiveDialogIcon(MDIcon):
    pass


class MDAdaptiveDialogHeadlineText(MDLabel):
    pass


class MDAdaptiveDialogSupportingText(MDLabel):
    pass


class MDAdaptiveDialogContentContainer(MDBoxLayout):
    pass


class MDAdaptiveDialogButtonContainer(MDBoxLayout):
    pass


class MDAdaptiveDialogScrim(Widget):
    color = ColorProperty(None)
    alpha = NumericProperty(0)
