from __future__ import annotations

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.graphics import Color, SmoothRoundedRectangle

from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    ObjectProperty,
    StringProperty,
    VariableListProperty,
    OptionProperty,
)
from kivy.uix.label import Label

from kivymd.theming import ThemableBehavior
from kivymd.uix import MDAdaptiveWidget
from kivymd.uix.behaviors import (
    DeclarativeBehavior,
    TouchBehavior,
    BackgroundColorBehavior,
)
from kivymd.uix.behaviors.state_layer_behavior import StateLayerBehavior


class MKVLabel(
    DeclarativeBehavior,
    ThemableBehavior,
    BackgroundColorBehavior,
    Label,
    MDAdaptiveWidget,
    TouchBehavior,
    StateLayerBehavior,
):
    font_style = StringProperty("Body")
    role = OptionProperty("large", options=["large", "medium", "small"])
    text = StringProperty()
    text_color = ColorProperty(None)
    allow_copy = BooleanProperty(False)
    allow_selection = BooleanProperty(False)
    color_selection = ColorProperty(None)
    color_deselection = ColorProperty(None)
    is_selected = BooleanProperty(False)
    radius = VariableListProperty([0], length=4)
    _canvas_bg = ObjectProperty(allownone=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type("on_copy")
        self.register_event_type("on_selection")
        self.register_event_type("on_cancel_selection")

    def do_selection(self) -> None:
        if not self.is_selected:
            self.md_bg_color = (
                self.theme_cls.secondaryContainerColor
                if not self.color_selection
                else self.color_selection
            )

    def cancel_selection(self) -> None:
        if self.is_selected:
            self.canvas.before.remove_group("md-label-selection-color")
            self.canvas.before.remove_group("md-label-selection-color-rectangle")
            self.md_bg_color = (
                self.parent.md_bg_color
                if not self.color_deselection
                else self.color_deselection
            )
            self.dispatch("on_cancel_selection")
            self.is_selected = False
            self._canvas_bg = None

    def on_double_tap(self, touch, *args) -> None:
        """Fired by double-clicking on the widget."""

        if self.allow_copy and self.collide_point(*touch.pos):
            Clipboard.copy(self.text)
            self.dispatch("on_copy")
        if self.allow_selection and self.collide_point(*touch.pos):
            self.do_selection()
            self.dispatch("on_selection")
            self.is_selected = True

    def on_window_touch(self, *args) -> None:
        """Fired at the on_touch_down event."""

        if self.is_selected:
            self.cancel_selection()

    def on_copy(self, *args) -> None:
        """
        Fired when double-tapping on the label.

        .. versionadded:: 1.2.0
        """

    def on_selection(self, *args) -> None:
        """
        Fired when double-tapping on the label.

        .. versionadded:: 1.2.0
        """

    def on_cancel_selection(self, *args) -> None:
        """
        Fired when the highlighting is removed from the label text.

        .. versionadded:: 1.2.0
        """

    def on_allow_selection(self, instance_label, selection: bool) -> None:
        """Fired when the :attr:`allow_selection` value changes."""

        if selection:
            Window.bind(on_touch_down=self.on_window_touch)
        else:
            Window.unbind(on_touch_down=self.on_window_touch)

    def on_text_color(self, instance_label, color: list | str) -> None:
        """Fired when the :attr:`text_color` value changes."""

        if self.theme_text_color == "Custom":
            if self.theme_cls.theme_style_switch_animation:
                Animation(
                    color=self.text_color,
                    d=self.theme_cls.theme_style_switch_animation_duration,
                    t="linear",
                ).start(self)
            else:
                self.color = self.text_color

    def on_md_bg_color(self, instance_label, color: list | str) -> None:
        """Fired when the :attr:`md_bg_color` value changes."""

        def on_md_bg_color(*args) -> None:
            from kivymd.uix.selectioncontrol import MDCheckbox
            from kivymd.uix.tooltip import MDTooltipPlain

            if not issubclass(self.__class__, (MDCheckbox, MDIcon, MDTooltipPlain)):
                self.canvas.remove_group("Background_instruction")

                # FIXME: IndexError
                # try:
                #     self.canvas.before.clear()
                # except IndexError:
                #     pass

                with self.canvas.before:
                    Color(rgba=color, group="md-label-selection-color")
                    self._canvas_bg = SmoothRoundedRectangle(
                        pos=self.pos,
                        size=self.size,
                        radius=self.radius,
                        group="md-label-selection-color-rectangle",
                    )
                    self.bind(pos=self.update_canvas_bg_pos)

        Clock.schedule_once(on_md_bg_color)

    def on_size(self, instance_label, size: list) -> None:
        """Fired when the parent window of the application is resized."""

        if self._canvas_bg:
            self._canvas_bg.size = size

    def update_canvas_bg_pos(self, instance_label, pos: list) -> None:
        if self._canvas_bg:
            self._canvas_bg.pos = pos


from kivymd.uix.badge.badge import MDBadge


class MKVIcon(MKVLabel):
    icon = StringProperty("blank")
    source = StringProperty(None, allownone=True)
    icon_color = ColorProperty(None)
    icon_color_disabled = ColorProperty(None)
    # kivymd.uix.badge.badge.MDBadge object.
    _badge: ObjectProperty[MDBadge] = ObjectProperty()

    def add_widget(self, widget, index=0, canvas=None):
        from kivymd.uix.badge import MDBadge

        if isinstance(widget, MDBadge):
            self._badge = widget
            return super().add_widget(widget)
