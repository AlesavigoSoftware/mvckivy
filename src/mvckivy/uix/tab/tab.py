from __future__ import annotations

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.carousel import Carousel
from kivy.uix.widget import Widget
from kivy.utils import boundary
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import (
    ObjectProperty,
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    AliasProperty,
    StringProperty,
    VariableListProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

from kivymd.theming import ThemableBehavior
from kivymd.uix.badge import MDBadge
from kivymd.uix.behaviors import (
    DeclarativeBehavior,
    RectangularRippleBehavior,
    BackgroundColorBehavior,
)
from kivymd.uix.behaviors.state_layer_behavior import StateLayerBehavior
from kivymd.uix.label import MDLabel, MDIcon


class MKVTabsBadge(MDBadge):
    pass


class MKVTabsCarousel(Carousel):
    lock_swiping = BooleanProperty(False)
    """
    If True - disable switching tabs by swipe.

    :attr:`lock_swiping` is an :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    _tabs = ObjectProperty()  # MKVTabsPrimary/MKVTabsSecondary object

    def on_touch_move(self, touch) -> str | bool | None:
        if self.lock_swiping:  # lock a swiping
            return
        if not self.touch_mode_change:
            if self.ignore_perpendicular_swipes and self.direction in (
                "top",
                "bottom",
            ):
                if abs(touch.oy - touch.y) < self.scroll_distance:
                    if abs(touch.ox - touch.x) > self.scroll_distance:
                        self._change_touch_mode()
                        self.touch_mode_change = True
            elif self.ignore_perpendicular_swipes and self.direction in (
                "right",
                "left",
            ):
                if abs(touch.ox - touch.x) < self.scroll_distance:
                    if abs(touch.oy - touch.y) > self.scroll_distance:
                        self._change_touch_mode()
                        self.touch_mode_change = True

        if self._get_uid("cavoid") in touch.ud:
            return
        if self._touch is not touch:
            super().on_touch_move(touch)
            return self._get_uid() in touch.ud
        if touch.grab_current is not self:
            return True

        ud = touch.ud[self._get_uid()]
        direction = self.direction[0]

        if ud["mode"] == "unknown":
            if direction in "rl":
                distance = abs(touch.ox - touch.x)
            else:
                distance = abs(touch.oy - touch.y)
            if distance > self.scroll_distance:
                ev = self._change_touch_mode_ev
                if ev is not None:
                    ev.cancel()
                ud["mode"] = "scroll"
        else:
            if direction in "rl":
                self._offset += touch.dx
            if direction in "tb":
                self._offset += touch.dy
        return True


class MKVTabsScrollView(BackgroundColorBehavior, ScrollView):
    def goto(self, scroll_x: float | None, scroll_y: float | None) -> None:
        """Update event value along with scroll_*."""

        def _update(e, x):
            if e:
                e.value = (e.max + e.min) * x

        if not (scroll_x is None):
            self.scroll_x = scroll_x
            _update(self.effect_x, scroll_x)

        if not (scroll_y is None):
            self.scroll_y = scroll_y
            _update(self.effect_y, scroll_y)


class MKVTabsItemText(MDLabel):
    _active = BooleanProperty(False)


class MKVTabsItemIcon(MDIcon):
    pass


class MKVTabsItemBase(
    DeclarativeBehavior,
    BackgroundColorBehavior,
    RectangularRippleBehavior,
    ButtonBehavior,
    ThemableBehavior,
    StateLayerBehavior,
):
    active = BooleanProperty(False)
    """
    Is the tab active.

    :attr:`active` is an :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    _tabs = ObjectProperty()  # MKVTabsPrimary/MKVTabsSecondary object
    _tab_content = ObjectProperty()  # Carousel slide (related content) object

    def on_release(self, *args) -> None:
        """
        Fired when the button is released
        (i.e. the touch/click that pressed the button goes away).
        """

        if self._tab_content:
            self._tabs._tabs_carousel.load_slide(self._tab_content)

        self._tabs.update_indicator(instance=self)
        self._tabs.dispatch("on_tab_switch", self, self._tab_content)
        self._tabs._current_tab = self
        self._tabs._current_related_content = self._tab_content


class MKVTabsItem(MKVTabsItemBase, BoxLayout):
    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, (MKVTabsItemText, MKVTabsItemIcon)):
            if len(self.children) <= 1:
                Clock.schedule_once(lambda x: self._set_width(widget))

    def _set_width(self, widget):
        def set_width(*args):
            self.width = widget.texture_size[0] + widget.padding_x + 2

        if not self._tabs.allow_stretch and isinstance(widget, MKVTabsItemText):
            Clock.schedule_once(set_width)

        super().add_widget(widget)


class MKVTabsPrimary(DeclarativeBehavior, ThemableBehavior, BoxLayout):
    md_bg_color = ColorProperty(None)
    """
    The background color of the widget.

    :attr:`md_bg_color` is an :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    label_only = BooleanProperty(False)
    """
    Tabs with a label only or with an icon and a label.

    .. versionadded:: 2.0.0

    :attr:`label_only` is an :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    allow_stretch = BooleanProperty(True)
    """
    Whether to stretch tabs to the width of the panel.

    :attr:`allow_stretch` is an :class:`~kivy.properties.BooleanProperty`
    and defaults to `True`.
    """

    lock_swiping = BooleanProperty(False)
    """
    If True - disable switching tabs by swipe.

    :attr:`lock_swiping` is an :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    anim_duration = NumericProperty(0.2)
    """
    Duration of the slide animation.

    :attr:`anim_duration` is an :class:`~kivy.properties.NumericProperty`
    and defaults to `0.2`.
    """

    indicator_anim = BooleanProperty(True)
    """
    Tab indicator animation. If you want use animation set it to ``True``.

    .. versionchanged:: 2.0.0

        Rename from `tab_indicator_anim` to `indicator_anim` attribute.

    :attr:`indicator_anim` is an :class:`~kivy.properties.BooleanProperty`
    and defaults to `True`.
    """

    indicator_radius = VariableListProperty([dp(2), dp(2), 0, 0], lenght=4)
    """
    Radius of the tab indicator.

    .. versionadded:: 2.0.0

    :attr:`indicator_radius` is an :class:`~kivy.properties.VariableListProperty`
    and defaults to `[dp(2), dp(2), 0, 0]`.
    """

    indicator_height = NumericProperty("4dp")
    """
    Height of the tab indicator.

    .. versionchanged:: 2.0.0

        Rename from `tab_indicator_height` to `indicator_height` attribute.

    :attr:`indicator_height` is an :class:`~kivy.properties.NumericProperty`
    and defaults to `'4dp'`.
    """

    indicator_duration = NumericProperty(0.5)
    """
    The duration of the animation of the indicator movement when switching
    tabs.

    .. versionadded:: 2.0.0

    :attr:`indicator_duration` is an :class:`~kivy.properties.NumericProperty`
    and defaults to `0.5`.
    """

    indicator_transition = StringProperty("out_expo")
    """
    The transition name of animation of the indicator movement when switching
    tabs.

    .. versionadded:: 2.0.0

    :attr:`indicator_transition` is an :class:`~kivy.properties.StringProperty`
    and defaults to `'out_expo'.
    """

    def get_last_scroll_x(self):
        return self.ids.tab_scroll.scroll_x

    last_scroll_x = AliasProperty(get_last_scroll_x, bind=("target",), cache=True)
    """
    Is the carousel reference of the next tab/slide.
    When you go from `'Tab A'` to `'Tab B'`, `'Tab B'` will be the
    target tab/slide of the carousel.

    :attr:`last_scroll_x` is an :class:`~kivy.properties.AliasProperty`.
    """

    target = ObjectProperty(None, allownone=True)
    """
    It is the carousel reference of the next tab / slide.
    When you go from `'Tab A'` to `'Tab B'`, `'Tab B'` will be the
    target tab / slide of the carousel.

    :attr:`target` is an :class:`~kivy.properties.ObjectProperty`
    and default to `None`.
    """

    def get_rect_instruction(self):
        canvas_instructions = self.ids.container.canvas.before.get_group(
            "md-tabs-rounded-rectangle"
        )
        return canvas_instructions[0]

    indicator = AliasProperty(get_rect_instruction, cache=True)
    """
    It is the :class:`~kivy.graphics.vertex_instructions.SmoothRoundedRectangle`
    instruction reference of the tab indicator.

    :attr:`indicator` is an :class:`~kivy.properties.AliasProperty`.
    """

    _tabs_carousel = ObjectProperty()  # MKVTabsCarousel object
    _current_tab = None  # MKVTabsItem object
    _current_related_content = None  # Carousel slide (related content) object
    _do_releasing = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type("on_tab_switch")
        self.register_event_type("on_slide_progress")
        Clock.schedule_once(self._check_panel_height)
        Clock.schedule_once(self._set_slides_attributes)

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, MKVTabsCarousel):
            self._tabs_carousel = widget
            widget._tabs = self
            widget.bind(_offset=self.android_animation, index=self.on_carousel_index)
            return super().add_widget(widget)
        elif isinstance(widget, MKVTabsItem) or (
            isinstance(self, MKVTabsSecondary)
            and isinstance(widget, MKVTabsItemSecondary)
        ):
            widget._tabs = self
            widget.bind(on_release=self.set_active_item)
            self.ids.container.add_widget(widget)
        else:
            return super().add_widget(widget)

    def do_autoscroll_tabs(self, instance: MKVTabsItem, value: float) -> None:
        """
        Automatically scrolls the list of tabs when swiping the carousel
        slide (related content).

        .. versionchanged:: 2.0.0

            Rename from `tab_bar_autoscroll` to `do_autoscroll_tabs` method.
        """

        bound_left = self.center_x - self.x
        bound_right = self.ids.container.width - bound_left
        dt = instance.center_x - bound_left
        sx, sy = self.ids.tab_scroll.convert_distance_to_scroll(dt, 0)
        lsx = self.last_scroll_x  # ast scroll x of the tab bar
        scroll_is_late = lsx < sx  # determine scroll direction
        dst = abs(lsx - sx) * value  # distance to run)

        if not dst:
            return
        if scroll_is_late and instance.center_x > bound_left:
            x = lsx + dst
        elif not scroll_is_late and instance.center_x < bound_right:
            x = lsx - dst
        else:
            return

        x = boundary(x, 0.0, 1.0)
        self.ids.tab_scroll.goto(x, None)

    def android_animation(self, instance: MKVTabsCarousel, offset: float) -> None:
        """Fired when swiping a carousel slide (related content)."""

        self.dispatch("on_slide_progress", instance, offset)

        # Try to reproduce the android animation effect.
        if offset != 0 and abs(offset) < instance.width:
            forward = offset < 0
            offset = abs(offset)
            step = offset / float(instance.width)

            skip_slide = (
                instance.slides[instance._skip_slide]
                if instance._skip_slide is not None
                else None
            )
            next_slide = instance.next_slide if forward else instance.previous_slide
            self.target = skip_slide if skip_slide else next_slide

            if not self.target:
                return

            a = instance.current_slide.tab_item
            b = self.target.tab_item
            self.do_autoscroll_tabs(b, step)
            item_text_object = self._get_tab_item_text_icon_object()

            if item_text_object:
                if self.__class__.__name__ == "MKVTabsSecondary":
                    tab_text_width = a.width
                else:
                    tab_text_width = item_text_object.texture_size[0]

                if self.indicator_anim is False:
                    return

                gap_x = abs(a.x - b.x)
                if forward:
                    x_step = (
                        a.x
                        + (a.width / 2 - tab_text_width / 2)
                        + dp(4)
                        + (gap_x * step)
                    )
                else:
                    x_step = (
                        a.x + (a.width / 2 - tab_text_width / 2) + dp(4) - gap_x * step
                    )

                w_step = tab_text_width - (
                    dp(8) if self.__class__.__name__ == "MKVTabsPrimary" else 0
                )
                self.update_indicator(x_step, w_step)

    def update_indicator(
        self, x: float = 0.0, w: float = 0.0, instance: MKVTabsItem = None
    ) -> None:
        """Update position and size of the indicator."""

        def update_indicator(*args):
            indicator_pos = (0, 0)
            indicator_size = (0, 0)

            if self.__class__.__name__ == "MKVTabsPrimary":
                item_text_object = self._get_tab_item_text_icon_object()

                if item_text_object:
                    tab_text_width = item_text_object.texture_size[0]
                    indicator_pos = (
                        instance.x + (instance.width / 2 - tab_text_width / 2) + dp(4),
                        (
                            self.indicator.pos[1]
                            if not self._tabs_carousel
                            else self._tabs_carousel.height
                        ),
                    )
                    indicator_size = (
                        tab_text_width - dp(8),
                        self.indicator_height,
                    )
            elif self.__class__.__name__ == "MKVTabsSecondary":
                indicator_pos = (instance.x, self.indicator.pos[1])
                indicator_size = (instance.width, self.indicator_height)

            Animation(
                pos=indicator_pos,
                size=indicator_size,
                d=0 if not self.indicator_anim else self.indicator_duration,
                t=self.indicator_transition,
            ).start(self.indicator)

        if not instance:
            self.indicator.pos = (x, self.indicator.pos[1])
            self.indicator.size = (w, self.indicator_height)
        else:
            Clock.schedule_once(update_indicator)

    def switch_tab(
        self, instance: MKVTabsItem = None, text: str = "", icon: str = ""
    ) -> None:
        """Switches tabs by tab object/tab text/tab icon name."""

        Clock.schedule_once(lambda x: self._switch_tab(instance, text, icon), 0.8)

    def set_active_item(self, item: MKVTabsItem) -> None:
        """Sets the active tab item."""

        for widget in self.ids.container.children:
            if item is widget:
                # Trying to switch an already active tab.
                if widget.active and item.active:
                    break

                widget.active = not widget.active

                for widget_item in item.children:
                    if isinstance(widget_item, MKVTabsItemText):
                        widget_item._active = widget.active
                        Animation(
                            text_color=(
                                self.theme_cls.primaryColor
                                if widget.active
                                else self.theme_cls.onSurfaceVariantColor
                            ),
                            d=0.2,
                        ).start(widget_item)
                    if isinstance(widget_item, MKVTabsItemIcon):
                        widget_item._active = widget.active
                        Animation(
                            icon_color=(
                                self.theme_cls.primaryColor
                                if widget.active
                                else self.theme_cls.onSurfaceVariantColor
                            ),
                            d=0.2,
                        ).start(widget_item)
            else:
                widget.active = False
                for widget_item in widget.children:
                    widget_item._active = widget.active
                    if isinstance(widget_item, MKVTabsItemText):
                        Animation(
                            text_color=self.theme_cls.onSurfaceVariantColor,
                            d=0.2,
                        ).start(widget_item)
                    if isinstance(widget_item, MKVTabsItemIcon):
                        Animation(
                            icon_color=self.theme_cls.onSurfaceVariantColor,
                            d=0.2,
                        ).start(widget_item)

    def get_tabs_list(self) -> list:
        """
        Returns a list of :class:`~MKVTabsItem` objects.

        .. versionchanged:: 2.0.0

            Rename from `get_tab_list` to `get_tabs_list` method.
        """

        return self.ids.container.children

    def get_slides_list(self) -> list:
        """
        Returns a list of user tab objects.

        .. versionchanged:: 2.0.0

            Rename from `get_slides` to `get_slides_list` method.
        """

        if self._tabs_carousel:
            return self._tabs_carousel.slides

    def get_current_tab(self) -> MKVTabsItem:
        """
        Returns current tab object.

        .. versionadded:: 1.0.0
        """

        return self._current_tab

    def get_current_related_content(self) -> Widget:
        """
        Returns the carousel slide object (related content).

        .. versionadded:: 2.0.0
        """

        return self._current_related_content

    def on_tab_switch(self, *args) -> None:
        """This event is launched every time the current tab is changed."""

    def on_slide_progress(self, *args) -> None:
        """
        This event is deployed every available frame while the tab is
        scrolling.
        """

    def on_carousel_index(self, instance: MKVTabsCarousel, value: int) -> None:
        """
        Fired when the Tab index have changed.
        This event is deployed by the builtin carousel of the class.
        """

        # When the index of the carousel change, update tab indicator,
        # select the current tab and reset threshold data.
        if instance.current_slide and hasattr(instance.current_slide, "tab_item"):
            Clock.schedule_once(
                lambda x: instance.current_slide.tab_item.dispatch("on_release")
            )

    def on_size(self, instance, size) -> None:
        """Fired when the application screen size changes."""

        width, height = size
        number_tabs = len(self.ids.container.children)

        if self.allow_stretch:
            for tab in self.ids.container.children:
                tab.width = width / number_tabs

        if self._tabs_carousel:
            Clock.schedule_once(
                lambda x: self._tabs_carousel.current_slide.tab_item.dispatch(
                    "on_release"
                )
            )

    def _switch_tab(self, instance: MKVTabsItem = None, text: str = "", icon: str = ""):
        def get_match(widget_to_compare, widget_to_compare_with, value, attr):
            if isinstance(widget_to_compare, widget_to_compare_with):
                if getattr(widget_to_compare, attr) == value:
                    return True

        def switch_by(by_attr, attr):
            for tab_item in self.ids.container.children:
                for child in tab_item.children:
                    if isinstance(child, MKVTabsItemSecondaryContainer):
                        for w in child.children:
                            if get_match(
                                w,
                                (
                                    MKVTabsItemText
                                    if by_attr == "text"
                                    else MKVTabsItemIcon
                                ),
                                attr,
                                by_attr,
                            ):
                                tab_item.dispatch("on_release")
                                break
                    else:
                        if get_match(
                            child,
                            MKVTabsItemText if by_attr == "text" else MKVTabsItemIcon,
                            attr,
                            by_attr,
                        ):
                            tab_item.dispatch("on_release")
                            break

        if instance and isinstance(instance, MKVTabsItem):
            instance.dispatch("on_release")
        elif text:
            switch_by("text", text)
        elif icon:
            switch_by("icon", icon)

    def _set_slides_attributes(self, *args):
        if self._tabs_carousel:
            tabs_item_list = self.ids.container.children.copy()
            tabs_item_list.reverse()

            for i, tab_item in enumerate(tabs_item_list):
                setattr(tab_item, "_tab_content", self._tabs_carousel.slides[i])
                setattr(self._tabs_carousel.slides[i], "tab_item", tab_item)

    def _get_tab_item_text_icon_object(
        self, get_type="text"
    ) -> MKVTabsItemText | MKVTabsItemIcon | None:
        item_text_object = None

        for tab_item in self.ids.container.children:
            if tab_item.active:
                for child in tab_item.children:
                    if isinstance(child, MKVTabsItemSecondaryContainer):
                        for w in child.children:
                            if isinstance(
                                w,
                                (
                                    MKVTabsItemText
                                    if get_type == "text"
                                    else MKVTabsItemIcon
                                ),
                            ):
                                item_text_object = w
                                break
                    else:
                        if isinstance(
                            child,
                            MKVTabsItemText if get_type == "text" else MKVTabsItemIcon,
                        ):
                            item_text_object = child
                            break
        return item_text_object

    def _check_panel_height(self, *args):
        if self.label_only:
            self.ids.tab_scroll.height = dp(48)
        else:
            self.ids.tab_scroll.height = dp(64)


class MKVTabsItemSecondaryContainer(BoxLayout):
    pass


class MKVTabsItemSecondary(MKVTabsItemBase, AnchorLayout):
    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, (MKVTabsItemText, MKVTabsItemIcon, MKVTabsBadge)):
            Clock.schedule_once(lambda x: self.ids.box_container.add_widget(widget))
        else:
            return super().add_widget(widget)


class MKVTabsSecondary(MKVTabsPrimary):
    indicator_radius = VariableListProperty(0, lenght=4)
    """
    Radius of the tab indicator.

    :attr:`indicator_radius` is an :class:`~kivy.properties.VariableListProperty`
    and defaults to `[0, 0, 0, 0]`.
    """

    indicator_height = NumericProperty("2dp")
    """
    Height of the tab indicator.

    :attr:`indicator_height` is an :class:`~kivy.properties.NumericProperty`
    and defaults to `'2dp'`.
    """

    def _check_panel_height(self, *args):
        self.ids.tab_scroll.height = dp(48)
