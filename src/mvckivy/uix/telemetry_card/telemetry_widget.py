from __future__ import annotations

import weakref
from kivy.metrics import dp
from typing import Optional

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import (
    ListProperty,
    ObjectProperty,
    StringProperty,
    NumericProperty,
)

from kivymd.uix.card import MDCard

from utility import TelemetryDispatcher
from mvckivy import MVCBehavior, CursorHoverBehavior
from mvckivy import AutoResizeLabel, AutoResizeIcon


class TelemetryWidgetHeading(MDCard):
    vehicle_name = StringProperty("БПЛА")
    vehicle_local_id = NumericProperty(-1)
    icon = StringProperty()
    text = StringProperty()


class TelemetryWidgetInfoBox(MDCard):
    telemetry_widget = ObjectProperty()

    title = ObjectProperty()
    data = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.telemetry_widget.bind(opacity=self.setter("opacity"))

    def update(self, telemetry_dispatcher: TelemetryDispatcher, prop_name: str):
        telemetry_chunk: Optional[dict] = getattr(telemetry_dispatcher, prop_name, None)

        if telemetry_chunk is None:
            self._update_data(None, None)
            self._update_title(None)
            return

        self._update_title(telemetry_chunk)
        self._rebind__update_data(telemetry_dispatcher, prop_name)
        self._update_data(None, telemetry_chunk)

    def _update_title(self, telemetry_chunk: Optional[dict]):
        """Calls a single time"""
        if isinstance(self.title, AutoResizeIcon):
            self.title.icon = (
                telemetry_chunk["icon"] if telemetry_chunk is not None else "blank"
            )
        elif isinstance(self.title, AutoResizeLabel):
            self.title.text = (
                telemetry_chunk["name"] if telemetry_chunk is not None else "Нет данных"
            )

    def _rebind__update_data(
        self, telemetry_dispatcher: TelemetryDispatcher, prop_name: str
    ):
        for callback_ref in telemetry_dispatcher.get_property_observers(prop_name):
            if (
                callback_ref.proxy in weakref.getweakrefs(self)
                and callback_ref.method_name == "_update_data"
            ):
                telemetry_dispatcher.funbind(prop_name, self._update_data)

        telemetry_dispatcher.bind(**{prop_name: self._update_data})

    def _update_data(self, instance, telemetry_chunk: Optional[dict]):
        """Should be bound to the telem_dispatcher"""
        if telemetry_chunk is not None and telemetry_chunk["format_value"] is not None:
            self.data.text = telemetry_chunk["format_value"]
        else:
            self.data.text = "Нет данных"

    def on_press(self, *args) -> None:
        super().on_press(*args)
        self.telemetry_widget.dispatch("on_info_box_press", self)

    def on_release(self, *args) -> None:
        super().on_release(*args)
        self.telemetry_widget.dispatch("on_info_box_release", self)


class TelemetryWidget(CursorHoverBehavior, MVCBehavior, MDCard):
    header = ObjectProperty(None)
    vehicle_name = StringProperty("БПЛА")
    vehicle_local_id = NumericProperty(-1)

    grid = ObjectProperty()
    grid_dimensions = ListProperty([3, 3])

    info_box_cls = ObjectProperty(TelemetryWidgetInfoBox)
    info_box_size = ListProperty([dp(80), dp(40)])
    info_boxes_bind_table = ListProperty([])

    __events__ = [
        "on_header_press",
        "on_header_release",
        "on_info_box_press",
        "on_info_box_release",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cur_anim: Optional[Animation] = None
        self._cur_anim_box: Optional[TelemetryWidgetInfoBox] = None

    def _bind_all(self):
        self.bind(grid_dimensions=self._generate_and_update_info_boxes)
        self.bind(
            vehicle_local_id=lambda *_: self._update_info_boxes(
                self, self.info_boxes_bind_table
            )
        )

        if self.header:
            self.bind(vehicle_name=self.header.setter("vehicle_name"))
            self.bind(vehicle_local_id=self.header.setter("vehicle_local_id"))
            self.header.bind(
                on_press=lambda *args: self.dispatch("on_header_press", *args)
            )
            self.header.bind(
                on_release=lambda *args: self.dispatch("on_header_release", *args)
            )
            # only this form works with .kv

    def _init_all(self):
        self._generate_and_update_info_boxes()

        if self.header:
            self.header.vehicle_name = self.vehicle_name
            self.header.vehicle_local_id = self.vehicle_local_id

    def _update_info_boxes(self, instance, bind_table: list[list[str]]):

        boxes: list[TelemetryWidgetInfoBox] = self.grid.children[::-1]
        telemetry_dispatcher: TelemetryDispatcher = (
            self.app.model.telemetry_dispatchers[self.vehicle_local_id]
        )

        for index, prop_name in enumerate(bind_table[self.vehicle_local_id]):

            if index >= len(boxes):
                return

            box = boxes[index]
            box.update(telemetry_dispatcher, prop_name)

    def _generate_and_update_info_boxes(self, *_) -> None:
        purpose = self.grid.get_max_widgets()
        current = len(self.grid.children)

        if purpose == current:
            return

        if self._cur_anim is not None:
            self._cur_anim.cancel(self._cur_anim_box)
        self.grid.clear_widgets()
        Clock.schedule_once(self._gen, 0)

    def _gen(self, *_):
        purpose = self.grid.get_max_widgets()
        current = len(self.grid.children)

        if current < purpose:
            self._cur_anim_box = self.info_box_cls(
                telemetry_widget=self, size=self.info_box_size
            )

            purpose_size = self.info_box_size
            # self._cur_anim_box.size = [0, 0]
            self.grid.add_widget(self._cur_anim_box)

            self._cur_anim = Animation(size=purpose_size, d=0.05, t="in_out_sine")
            self._cur_anim.bind(on_complete=self._gen)
            self._cur_anim.start(self._cur_anim_box)

        else:
            self._update_info_boxes(self, self.info_boxes_bind_table)

    def on_press(self, *args) -> None:
        super().on_press(*args)

    def on_release(self, *args) -> None:
        super().on_release(*args)

    def on_header_press(self, header):
        pass

    def on_header_release(self, header):
        pass

    def on_info_box_press(self, info_box):
        pass

    def on_info_box_release(self, info_box):
        pass
