from typing import Optional

from kivy._clock import ClockEvent
from kivy.clock import Clock
from kivy_garden.mapview import MapView
from kivy_garden.mapview.utils import clamp


class CustomMapView(MapView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_map_clock_event: Optional[ClockEvent] = None

    def on_transform(self, *args):
        self._invalid_scale = True
        if self._transform_lock:
            return
        self._transform_lock = True
        # recalculate viewport
        map_source = self.map_source
        zoom = self._zoom
        scatter = self._scatter
        scale = scatter.scale

        rescale = False

        if round(scale, 2) >= 2.0:
            zoom += 1
            scale /= 2.0
        elif round(scale, 2) < 1.0:
            zoom -= 1
            scale *= 2.0
        elif self._scale == scale:  # Here is important not to round the value
            scale = 1.0
            rescale = True
        #  TODO: Заменить данную заплатку на нормальный способ отрисовки многоугольников при различных значениях scale

        zoom = clamp(zoom, map_source.min_zoom, map_source.max_zoom)
        if zoom != self._zoom:
            self.set_zoom_at(zoom, scatter.x, scatter.y, scale=scale)
            self.trigger_update(True)
        else:
            if zoom == map_source.min_zoom and round(scatter.scale, 2) < 1.0:
                scatter.scale = 1.0
                self.trigger_update(True)
            elif zoom == map_source.max_zoom and round(scatter.scale, 2) > 1.0:
                scatter.scale = 1.0
                self.trigger_update(True)
            else:
                if rescale:
                    self.set_zoom_at(zoom, scatter.x, scatter.y, scale=scale)
                #     TODO: Убрать заплатку. Используется для устранения проблем с масштабированием полигонов (scale=1)
                self.trigger_update(False)

        if map_source.bounds:
            self._apply_bounds()

        self._transform_lock = False
        self._scale = self._scatter.scale

    def animated_diff_scale_at(self, d, x, y):
        if (self._zoom == self.map_source.min_zoom and d < 0
                or self._zoom == self.map_source.max_zoom and d > 0):
            return  # Позволяет избежать бага с непрерывной перемоткой карты в случаях предельных значений зума

        self._scale_target_time = 1.0
        self._scale_target_pos = x, y

        if self._scale_target_anim is False:
            self._scale_target_anim = True
            self._scale_target = d

        else:
            self._scale_target += d

        Clock.unschedule(self._animate_scale)
        Clock.schedule_interval(self._animate_scale, 1 / 60.0)

    def sync_to(
            self,
            other=None,
            lat: float = 0,
            lon: float = 0,
            zoom: int = 0
    ):
        if other is not None:
            return super().sync_to(other=other)

        self.set_zoom_at(
            zoom,
            *self.center
        )
        self.center_on(lat, lon)

    def schedule_map_update(self, fps: int = 30):
        if self.update_map_clock_event is None:
            self.update_map_clock_event = Clock.schedule_interval(
                lambda dt: self.trigger_update(True), 1 / fps
            )

    def unschedule_map_update(self):
        if self.update_map_clock_event is not None:
            self.update_map_clock_event.cancel()
            self.update_map_clock_event = None

    def zoom_up(self):
        if self.zoom == self.map_source.max_zoom:
            return

        self.set_zoom_at(
            self.zoom + 1,
            *self.center,
            scale=self.scale * 2
        )

    def zoom_down(self):
        if self.zoom == self.map_source.min_zoom:
            return

        self.set_zoom_at(
            self.zoom - 1,
            *self.center,
            scale=self.scale / 2
        )

    def add_widget(self, widget, index=0, canvas=None):
        """Classic signature"""
        super().add_widget(widget)
