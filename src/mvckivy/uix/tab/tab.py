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
    _tabs = ObjectProperty()  # MKVTabsPrimary/MKVTabsSecondary object
    _tab_content = ObjectProperty()  # Carousel slide (related content) object

    def on_release(self, *args) -> None:
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
    label_only = BooleanProperty(False)
    allow_stretch = BooleanProperty(True)
    lock_swiping = BooleanProperty(False)
    anim_duration = NumericProperty(0.2)
    indicator_anim = BooleanProperty(True)
    indicator_radius = VariableListProperty([dp(2), dp(2), 0, 0], lenght=4)
    indicator_height = NumericProperty("4dp")
    indicator_duration = NumericProperty(0.5)
    indicator_transition = StringProperty("out_expo")

    def get_last_scroll_x(self):
        return self.ids.tab_scroll.scroll_x

    last_scroll_x = AliasProperty(get_last_scroll_x, bind=("target",), cache=True)
    target = ObjectProperty(None, allownone=True)

    def get_rect_instruction(self):
        canvas_instructions = self.ids.container.canvas.before.get_group(
            "md-tabs-rounded-rectangle"
        )
        return canvas_instructions[0]

    indicator = AliasProperty(get_rect_instruction, cache=True)

    _tabs_carousel = ObjectProperty()  # MKVTabsCarousel object
    _current_tab = None  # MKVTabsItem object
    _current_related_content = None  # Carousel slide (related content) object
    _do_releasing = True

    def _is_secondary(self) -> bool:
        return False

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
                if self._is_secondary():
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

                w_step = tab_text_width - (dp(8) if not self._is_secondary() else 0)
                self.update_indicator(x_step, w_step)

    def update_indicator(
        self, x: float = 0.0, w: float = 0.0, instance: MKVTabsItem = None
    ) -> None:
        def update_indicator(*args):
            indicator_pos = (0, 0)
            indicator_size = (0, 0)

            if not self._is_secondary():
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
            else:
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
        return self.ids.container.children

    def get_slides_list(self) -> list:
        if self._tabs_carousel:
            return self._tabs_carousel.slides

    def get_current_tab(self) -> MKVTabsItem:
        return self._current_tab

    def get_current_related_content(self) -> Widget:
        return self._current_related_content

    def on_tab_switch(self, *args) -> None:
        pass

    def on_slide_progress(self, *args) -> None:
        pass

    def on_carousel_index(self, instance: MKVTabsCarousel, value: int) -> None:
        # When the index of the carousel change, update tab indicator,
        # select the current tab and reset threshold data.
        current_slide = instance.current_slide
        if not current_slide:
            return

        try:
            tab_item = current_slide.tab_item
        except AttributeError:
            return

        Clock.schedule_once(lambda _: tab_item.dispatch("on_release"))

    def on_size(self, instance, size) -> None:
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
        if instance and isinstance(instance, MKVTabsItem):
            instance.dispatch("on_release")
            return

        if text:
            self._switch_tab_by_text(text)
            return

        if icon:
            self._switch_tab_by_icon(icon)

    def _switch_tab_by_text(self, target_text: str) -> None:
        for tab_item in self.ids.container.children:
            if self._tab_contains_text(tab_item, target_text):
                tab_item.dispatch("on_release")
                break

    def _switch_tab_by_icon(self, target_icon: str) -> None:
        for tab_item in self.ids.container.children:
            if self._tab_contains_icon(tab_item, target_icon):
                tab_item.dispatch("on_release")
                break

    def _tab_contains_text(self, tab_item: MKVTabsItem, target_text: str) -> bool:
        for child in tab_item.children:
            if isinstance(child, MKVTabsItemSecondaryContainer):
                for widget in child.children:
                    if isinstance(widget, MKVTabsItemText) and widget.text == target_text:
                        return True
            elif isinstance(child, MKVTabsItemText) and child.text == target_text:
                return True
        return False

    def _tab_contains_icon(self, tab_item: MKVTabsItem, target_icon: str) -> bool:
        for child in tab_item.children:
            if isinstance(child, MKVTabsItemSecondaryContainer):
                for widget in child.children:
                    if isinstance(widget, MKVTabsItemIcon) and widget.icon == target_icon:
                        return True
            elif isinstance(child, MKVTabsItemIcon) and child.icon == target_icon:
                return True
        return False

    def _set_slides_attributes(self, *args):
        if self._tabs_carousel:
            tabs_item_list = self.ids.container.children.copy()
            tabs_item_list.reverse()

            for i, tab_item in enumerate(tabs_item_list):
                tab_item._tab_content = self._tabs_carousel.slides[i]
                self._tabs_carousel.slides[i].tab_item = tab_item

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
    indicator_height = NumericProperty("2dp")

    def _is_secondary(self) -> bool:
        return True

    def _check_panel_height(self, *args):
        self.ids.tab_scroll.height = dp(48)
