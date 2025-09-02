from __future__ import annotations

import logging

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import (
    ColorProperty,
    NumericProperty,
    VariableListProperty,
    StringProperty,
    ObjectProperty,
    BooleanProperty,
    AliasProperty,
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton
from kivymd.uix.divider import MDDivider
from kivymd.uix.relativelayout import MDRelativeLayout


class MDSegmentedControlItem(MDButton):
    disable_hover_behavior = BooleanProperty(True)

    def on_enter(self, *_):
        if self.disable_hover_behavior:
            return
        else:
            super().on_enter()

    def on_leave(self, *_) -> None:
        if self.disable_hover_behavior:
            return
        else:
            super().on_leave()


class MDSegmentSwitch(MDButton):
    """Implements a switch for the :class:`~ModifiedMDSegmentedControl` class."""

    _no_ripple_effect = BooleanProperty(True)


class MDSegmentPanel(MDBoxLayout):
    """
    Implements a panel for placing items - :class:`~ModifiedMDSegmentedControlItem`
    for the :class:`~ModifiedMDSegmentedControl` class.
    """

    def _get_items_count(self):
        return sum(
            1 for item in self.children if isinstance(item, MDSegmentedControlItem)
        )

    items_count = AliasProperty(_get_items_count, None, bind=["children"], cache=True)


class MDSegmentedControl(MDRelativeLayout):
    md_bg_color = ColorProperty([0, 0, 0, 0])
    """
    Background color of the segment panel in (r, g, b, a) or string format.

    .. code-block:: kv

        ModifiedMDSegmentedControl:
            md_bg_color: 'brown'

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/md-segmented-control-md-bg-color.png
        :align: center

    :attr:`md_bg_color` is an :class:`~kivy.properties.ColorProperty`
    and defaults to `[0, 0, 0, 0]`.
    """

    segment_color = ColorProperty([0, 0, 0, 0])
    """
    Color of the active segment in (r, g, b, a) or string format.

    .. code-block:: kv

        ModifiedMDSegmentedControl:
            md_bg_color: 'brown'
            segment_color: 'red'

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/md-segmented-control-segment-color.png
        :align: center

    .. code-block:: kv

        ModifiedMDSegmentedControl:
            md_bg_color: 'brown'
            segment_color: 'red'

            ModifiedMDSegmentedControlItem:
                text: '[color=fff]Male[/color]'

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/md-segmented-control-text-color.png
        :align: center

    :attr:`segment_color` is an :class:`~kivy.properties.ColorProperty`
    and defaults to `[0, 0, 0, 0]`.
    """

    segment_panel_width = NumericProperty(dp(320))
    segment_panel_height = NumericProperty(dp(42))
    """
    Height of the segment panel.

    .. code-block:: kv

        ModifiedMDSegmentedControl:
            segment_panel_height: '56dp'

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/md-segmented-control-segment-panel-height.png
        :align: center

    :attr:`segment_panel_height` is an :class:`~kivy.properties.NumericProperty`
    and defaults to `'42dp'`.
    """

    separator_color = ColorProperty(None)
    """
    The color of the separator between the segments in (r, g, b, a) or string
    format.

    .. code-block:: kv

        ModifiedMDSegmentedControl:
            md_bg_color: 'brown'
            segment_color: 'red'
            separator_color: 'white'

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/md-segmented-control-separator-color.png
        :align: center

    :attr:`separator_color` is an :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    radius = VariableListProperty([16], length=4)
    """
    Radius of the segment panel.

    .. code-block:: kv

        ModifiedMDSegmentedControl:
            radius: 0

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/md-segmented-control-segment-radius.png
        :align: center

    :attr:`radius` is an :class:`~kivy.properties.VariableListProperty`
    and defaults to `[16, 16, 16, 16]`.
    """

    segment_switching_transition = StringProperty("in_cubic")
    """
    Name of the animation type for the switch segment.

    :attr:`segment_switching_transition` is a :class:`~kivy.properties.StringProperty`
    and defaults to `'in_cubic'`.
    """

    segment_switching_duration = NumericProperty(0.2)
    """
    Name of the animation type for the switch segment.

    :attr:`segment_switching_duration` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `0.2`.
    """

    current_active_segment = ObjectProperty()
    """
    The current active element of the :class:`~ModifiedMDSegmentedControlItem` class.

    :attr:`current_active_segment` is a :class:`~kivy.properties.ObjectProperty`
    and defaults to `None`.
    """

    _segment_switch_x = NumericProperty(dp(4))

    _segment_panel = ObjectProperty(baseclass=MDSegmentPanel)
    _segment_switch = ObjectProperty(baseclass=MDSegmentSwitch)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type("on_active")

        self.segment_panel = None

        Clock.schedule_once(self.set_default_colors)

    def set_default_colors(self, *_) -> None:
        """
        Sets the colors of the panel and the switch if the colors are not set
        by the user.
        """

        if self.md_bg_color == [0, 0, 0, 0]:
            self.md_bg_color = self.theme_cls.primaryContainerColor
        if self.segment_color == [0, 0, 0, 0]:
            self.segment_color = self.theme_cls.secondaryContainerColor

    def animation_segment_switch(self, widget: MDSegmentedControlItem) -> None:
        """Animates the movement of the switch."""

        Animation(
            # _segment_switch_x=widget.x,
            _segment_switch_x=widget.x - dp(6),
            t=self.segment_switching_transition,
            d=self.segment_switching_duration,
        ).start(self)

    def update_segment_panel_width(self, widget: MDSegmentedControlItem) -> None:
        """
        Sets the width of the panel for the elements of the
        :class:`~ModifiedMDSegmentedControlItem` class.
        """

        widget.text_size = (None, None)
        widget.texture_update()
        self._segment_panel.width += (
            widget.texture_size[0] + self._segment_panel.spacing
        )

    def update_separator_color(self, widget: MDDivider) -> None:
        """Updates the color of the separators between segments."""

        widget.color = (
            self.separator_color
            if self.separator_color
            else self.theme_cls.outlineColor
        )

    def add_widget(self, widget, *args, **kwargs):

        if isinstance(widget, (MDSegmentPanel, MDSegmentSwitch)):
            return super().add_widget(widget)

        if isinstance(widget, MDSegmentedControlItem):
            Clock.schedule_once(lambda dt: self.update_segment_panel_width(widget))
            widget.bind(on_press=self.on_press_segment)
            widget.bind(on_release=self.on_release_segment)

            if self._segment_panel.items_count > 0:
                separator = MDDivider(orientation="vertical")
                self._segment_panel.add_widget(separator)
                Clock.schedule_once(lambda dt: self.update_separator_color(separator))

            self._segment_panel.add_widget(widget)

    def on_active(self, item: MDSegmentedControlItem) -> None:
        """Called when the segment is activated."""
        pass

    def on_width(self, widget: MDSegmentedControl, new_width: float) -> None:
        """
        :param widget: ModifiedMDSegmentedControl
        :param new_width: float
        :return: None
        """
        if self.current_active_segment:
            Clock.schedule_once(
                lambda dt: self.animation_segment_switch(self.current_active_segment)
            )

    def on_press_segment(self, widget: MDSegmentedControlItem):
        pass

    def on_release_segment(self, widget: MDSegmentedControlItem):
        self._set_active_segment(widget)

    def _set_active_segment(self, widget: MDSegmentedControlItem):
        if self.current_active_segment is not widget:
            self.animation_segment_switch(widget)
            self.current_active_segment = widget
            self.dispatch("on_active", widget)

    def set_active_segment_by_index(self, index: int) -> None:
        """
        Sets the active segment on segmented panel by its index.
        :param index: int
        :return: None
        """
        try:
            self._set_active_segment(widget=self._segment_panel.children[index])
        except IndexError as ex:
            logging.error(ex)
