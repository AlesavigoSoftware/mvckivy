from __future__ import annotations
from typing import Optional, TypeVar, Callable

from kivy import Logger
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy_garden.mapview import MapMarkerPopup
from kivymd.uix.button import MDButton


class PolygonBaseMapMarkerPopup(MapMarkerPopup):
    T = TypeVar('T', bound=MapMarkerPopup)
    point_num: NumericProperty(None, allownone=True)

    def __init__(
            self,
            feature_num: int,
            polygon_num: int,
            point_num: int,
            **kwargs
    ):
        super().__init__(**kwargs)

        self.feature_num: Optional[int] = feature_num
        self.polygon_num: Optional[int] = polygon_num
        self.point_num: Optional[int] = point_num

    def _close_popup(self, *args):
        self.is_open = False

    def on_point_num(self, widget: T, point_num: int):
        pass


class MapMarkerPopupButton(MDButton):
    def __init__(self, min_width, min_height, on_collide_point: Callable = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._min_width = min_width
        self._min_height = min_height
        self._on_point_collide = on_collide_point

    def on_touch_down(self, touch):
        """Modified to prevent mapview "on_single_touch" event dispatching"""
        if self.collide_point(*touch.pos):
            if self._on_point_collide:
                self._on_point_collide()

        return super().on_touch_down(touch)


class InteractiveMapMarkerPopup(PolygonBaseMapMarkerPopup):
    """
    Различает следующие операции: одиночное касание, двойное касание,
    перемещение, нажатие на всплывающий виджет.
    Полный набор операций перемещения реализован только для ExtendedMarkerMapLayer
    """

    def __init__(self, feature_num: int, polygon_num: int, point_num: int, **kwargs):
        super().__init__(feature_num, polygon_num, point_num, **kwargs)

        self.register_event_type('on_single_touch')  # Technically equals to "on_release without move"

        self.anchor_x = 0.5
        self.anchor_y = 0.5
        self.fit_mode = 'fill'
        self.size = [dp(25), dp(25)]
        self.popup_size = [dp(45), dp(30)]
        self.is_open = True

        self._touch_moved = False

        self.popup_button = MapMarkerPopupButton(
            text=str(self.point_num),
            on_press=self._close_popup,
            min_width=self.popup_size[0],
            min_height=self.popup_size[1],
            on_collide_point=lambda: self.parent.marker_collision()
            # lambda expression because of the self.parent which is None at initialization of marker
        )
        self.add_widget(self.popup_button)

    def on_point_num(self, widget: InteractiveMapMarkerPopup, point_num: int):
        if self.popup_button:
            self.popup_button.text = str(point_num)

    def on_coordinates(self, instance, coords: list[float]):
        if self.parent:
            self.parent.dispatch('on_marker_move', self, coords)

    def on_touch_down(self, touch):

        if self.collide_point(*touch.pos):
            self.parent.marker_collision()  # To avoid "on_single_touch" mapview event dispatching

            if touch.is_double_tap:
                self.parent.dispatch('on_marker_double_touch', self)
                return True

            if touch.is_triple_tap:
                self.parent.dispatch('on_marker_triple_touch', self)
                return True

            touch.grab(self)
            Window.set_system_cursor('size_all')
            return True

        return super().on_touch_down(touch)
        # Parent (ExtendedMarkerMapLayer) checks out the grab condition and returns True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.pos = (self.pos[0] + touch.dx, self.pos[1] + touch.dy)
            self.coordinates = self.parent.get_latlon_at(self.center_x, self.center_y)
            # Turns on_marker_moved into on_marker_move event
            self._touch_moved = True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if not self._touch_moved:
                self.dispatch('on_single_touch', touch)

            self._touch_moved = False
            touch.ungrab(self)
            Window.set_system_cursor('arrow')
            self.lat, self.lon = self.parent.get_latlon_at(self.center_x, self.center_y)

            return True

        return super().on_touch_up(touch)

    def on_single_touch(self, touch):
        self.parent.dispatch('on_marker_single_touch', self)
        Logger.info(f'On marker single touch: {self}')
        self.is_open = True


class StaticMapMarkerPopup(PolygonBaseMapMarkerPopup):
    def __init__(
            self,
            feature_num: int,
            polygon_num: int,
            point_num: int,
            custom_text: str = None,
            **kwargs
    ):
        super().__init__(feature_num, polygon_num, point_num, **kwargs)

        self.anchor_x = 0.5
        self.anchor_y = 0.5
        self.fit_mode = 'fill'
        self.size = [dp(25), dp(25)]
        self.popup_size = [dp(45), dp(30)]
        self.is_open = True

        self._custom_text = custom_text
        self.popup_button = MapMarkerPopupButton(
            text=str(self.point_num) if self._custom_text is None else self._custom_text,
            on_press=self._close_popup,
            min_width=self.popup_size[0],
            min_height=self.popup_size[1],
            on_collide_point=lambda: self.parent.marker_collision()
        )
        self.add_widget(self.popup_button)

    def on_touch_down(self, touch):

        if self.collide_point(*touch.pos):
            self.parent.marker_collision()

            if touch.is_double_tap:
                self.parent.dispatch('on_marker_double_touch', self)
                return True

            if touch.is_triple_tap:
                self.parent.dispatch('on_marker_triple_touch', self)
                return True

        return super().on_touch_down(touch)

    # There is no action like "move" in static marker class,
    # so we don't need to catch "on_single_touch" event.
    # Using "on_release" instead and sending "on_marker_single_touch" from it,
    # so parent can react the same way as it was sent by dynamic_marker

    def on_release(self, *args):
        self.parent.dispatch('on_marker_single_touch', self)
        self.is_open = True

    def on_point_num(self, widget: StaticMapMarkerPopup, point_num: int):
        if self.popup_button and self._custom_text is None:
            self.popup_button.text = str(point_num)
