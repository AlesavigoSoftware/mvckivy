from __future__ import annotations

from abc import ABC
from typing import List, Optional, Union

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty

from mvckivy import logger
from controllers.app_screen.children.utils import create_fringing_line

from mvckivy import MultiVehicleContainerMixin
from mvckivy import MVCBehavior
from mvckivy import (
    StaticMissionInterruptionPointMapMarkerPopup,
    UAVMapMarker,
    StaticHomePointMapMarkerPopup,
    StaticMissionDrawPointMapMarkerPopup,
    StaticMarker,
)
from mvckivy import CustomMapView
from mvckivy import (
    LineMapLayer,
    ExtendedMarkerMapLayer,
    ClusteredMarkerMapLayer,
)


class ProgressLineDrawWidget(MultiVehicleContainerMixin):
    next_point_index = NumericProperty(-1)
    uav_coordinates = ListProperty(None, allownone=True)
    interruption_point = ListProperty(None, allownone=True)
    mission = ListProperty(None, allownone=True)

    def __init__(self, line_color: list[float], **kwargs):
        super().__init__(**kwargs)

        self._static_part: LineMapLayer = LineMapLayer(width=1.5, color=line_color)
        self._dynamic_part: LineMapLayer = LineMapLayer(width=1.5, color=line_color)
        self._interruption_marker_layer = ClusteredMarkerMapLayer()
        self._interruption_point_marker: Optional[
            StaticMissionInterruptionPointMapMarkerPopup
        ] = None

        self.interruption_point = None
        self.uav_coordinates = None
        self.mission = None
        self.next_point_index: int = -1  # Doesn't trigger appropriate method in case
        # if value is eq to the default value of the property

    def on_parent(self, widget: ProgressLineDrawWidget, parent_mapview: CustomMapView):
        if parent_mapview is not None:
            parent_mapview.add_layer(self._static_part, mode="scatter")
            parent_mapview.add_layer(self._dynamic_part, mode="scatter")
        else:
            self._last_parent.remove_layer(self._static_part)
            self._last_parent.remove_layer(self._dynamic_part)

    def on_interruption_point(
        self, widget: ProgressLineDrawWidget, interruption_point: List[float]
    ):
        if interruption_point:
            self.uav_coordinates = interruption_point
            self._draw_interruption_marker()
        else:
            self._clear_interruption_marker()

    def _draw_interruption_marker(self):
        if self._interruption_point_marker is not None:
            self._clear_interruption_marker()

        self._interruption_point_marker = self._interruption_marker_layer.add_marker(
            cls=StaticMissionInterruptionPointMapMarkerPopup,
            lat=self.interruption_point[0],
            lon=self.interruption_point[1],
        )

    def _clear_interruption_marker(self):
        if self._interruption_point_marker is not None:
            self._interruption_marker_layer.remove_marker(
                self._interruption_point_marker
            )
            self._interruption_marker_layer.redraw_markers()

    def on_mission(self, widget: ProgressLineDrawWidget, mission: List[List[float]]):
        if not mission:
            self._dynamic_part.unload()
            self._static_part.unload()

    def on_next_point_index(self, instance: ProgressLineDrawWidget, index: int):
        if index >= 0 and self.mission:
            self._static_part.coordinates = self.mission[index:]  # Triggers redrawing
        else:
            self._static_part.unload()

    def on_uav_coordinates(
        self, instance: ProgressLineDrawWidget, uav_coordinates: List[float]
    ):
        if not uav_coordinates or not self.mission:
            return

        if not self.interruption_point:
            new_line_coordinates = [
                uav_coordinates,
                self.mission[self.next_point_index],
            ]
            anim = Animation(coordinates=new_line_coordinates, d=0.5)
            anim.start(self._dynamic_part)


class MissionDrawWidget(MultiVehicleContainerMixin):
    mission: Optional[list[list[float]]] = ListProperty(None, allownone=True)
    home_point: Optional[list[float]] = ListProperty(None, allownone=True)

    def __init__(
        self,
        animate_drawing: bool = False,
        main_line_color: list[float] = None,
        draw_fringing_line: bool = True,
        fringing_line_color: list[float] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._static_marker_menu_items: list[dict] = []
        self.draw_fringing_line: bool = draw_fringing_line
        self._last_mission = None

        self._home_point_marker: Optional[StaticHomePointMapMarkerPopup] = None
        self.animate_drawing = animate_drawing

        self._static_marker_layer = ClusteredMarkerMapLayer()
        self._static_marker_layer.bind(
            on_marker_double_touch=self.on_marker_double_touch
        )

        self._static_mission_line_layer = LineMapLayer(
            animate_drawing=animate_drawing, color=main_line_color
        )
        self._static_fringing_line_layer = LineMapLayer(
            animate_drawing=animate_drawing, color=fringing_line_color
        )

        self.is_disabled = False
        self.is_unloaded = False

    def on_parent(
        self, mission_draw_widget: MissionDrawWidget, parent_map_view: CustomMapView
    ):
        if parent_map_view is not None:
            parent_map_view.add_layer(self._static_mission_line_layer, mode="scatter")
            parent_map_view.add_layer(self._static_fringing_line_layer, mode="scatter")
            parent_map_view.add_layer(self._static_marker_layer)
        else:
            self._last_parent.remove_layer(self._static_mission_line_layer)
            self._last_parent.remove_layer(self._static_fringing_line_layer)
            self._last_parent.remove_layer(self._static_marker_layer)

    def on_mission(
        self, widget: MissionDrawWidget, mission: Optional[list[list[float]]]
    ):
        if mission:
            self._draw_mission()
        else:
            self._clear_mission()

    def draw_last_mission(self):
        self.mission = self._last_mission.copy() if self._last_mission else self.mission

    def on_marker_double_touch(
        self, marker_map_layer: ExtendedMarkerMapLayer, marker: StaticMarker
    ) -> None:

        if isinstance(marker, StaticMissionDrawPointMapMarkerPopup):
            self.create_marker_menu(marker=marker)
            self._marker_on_double_touch_menu.caller = marker
            self._marker_on_double_touch_menu._open()

    def create_marker_menu(self, marker: StaticMarker, *args) -> None:
        titles = []
        icons = []
        callbacks = []
        callback_kwargs = []

        if isinstance(marker, StaticMissionDrawPointMapMarkerPopup):
            self._static_marker_menu_items = [
                {
                    "title": "Скрыть/показать №",
                    "icon": "eye-outline",
                    "cb": self.change_open_status_of_all_static_markers_popup,
                    "cb_kwargs": {},
                },
            ]

        for items in self._static_marker_menu_items:
            titles.append(items.get("title"))
            icons.append(items.get("icon"))
            callbacks.append(items.get("cb"))
            callback_kwargs.append(items.get("cb_kwargs"))

        # self._marker_on_double_touch_menu = CustomMDDropdownMenu(
        #     titles=titles,
        #     icons=icons,
        #     callbacks=callbacks,
        #     callback_kwargs=callback_kwargs,
        #     do_capitalize=False,
        #     position='center',
        #     dismiss_after_release=True,
        # )

    def change_open_status_of_all_static_markers_popup(self) -> None:
        self._static_marker_layer.global_popup_open_status = (
            not self._static_marker_layer.global_popup_open_status
        )

        for marker in self._static_marker_layer.cluster_markers:
            if marker.widget:
                marker.widget.is_open = (
                    self._static_marker_layer.global_popup_open_status
                )

    def _draw_mission(self):

        if self.mission is None:
            logger.error("MissionDrawer: Current mission is empty")
            return

        for num, point in enumerate(self.mission):
            self._static_marker_layer.add_marker(
                lat=point[0],
                lon=point[1],
                cls=StaticMissionDrawPointMapMarkerPopup,
                options={
                    "point_num": num,
                },
            )

        self._static_marker_layer.redraw_markers(animate_draw=self.animate_drawing)
        self._static_mission_line_layer.coordinates = self.mission

        if self.draw_fringing_line:
            self._draw_fringing_line()

    def _clear_mission(self):
        self._static_marker_layer.clear(animate_clear=self.animate_drawing)
        self._static_mission_line_layer.clear(animate=self.animate_drawing)
        self._static_fringing_line_layer.clear(animate=self.animate_drawing)

        self._static_marker_layer.cluster_markers = []
        self._static_mission_line_layer._coordinates = [
            [0, 0],
        ]
        self._static_fringing_line_layer._coordinates = [
            [0, 0],
        ]

    def _draw_fringing_line(self):
        self._static_fringing_line_layer.coordinates = create_fringing_line(
            self.mission
        )

    def on_home_point(self, widget: MissionDrawWidget, home_point: List[List[float]]):
        self._draw_home_marker()

    def _draw_home_marker(self):
        if not self.home_point:
            logger.error("MissionDrawer: Set home point before draw it!")
            return

        if self._home_point_marker is not None:
            self._clear_home_marker()

        self._home_point_marker = self._static_marker_layer.add_marker(
            cls=StaticHomePointMapMarkerPopup,
            lat=self.home_point[0],
            lon=self.home_point[1],
            redraw=True,
        )

    def _clear_home_marker(self):
        if self._home_point_marker is not None:
            self._static_marker_layer.remove_marker(
                self._home_point_marker, redraw=True
            )

    def disable(self):
        if self.is_unloaded:
            return

        for marker in self._static_marker_layer.cluster_markers:
            if marker.widget:
                marker.widget.opacity = 0
        self._static_mission_line_layer.disable()
        if self.draw_fringing_line:
            self._static_fringing_line_layer.disable()

        self.is_disabled = True

    def enable(self):
        if self.is_unloaded:
            return

        for marker in self._static_marker_layer.cluster_markers:
            if marker.widget:
                marker.widget.opacity = 1
        self._static_mission_line_layer.enable()
        if self.draw_fringing_line:
            self._static_fringing_line_layer.enable()

        self.is_disabled = False

    def unload(self):
        self._last_mission = self.mission.copy() if self.mission else self._last_mission
        self.mission = None

        self.is_unloaded = True

    def upload(self, disabled: Optional[bool] = None):
        self.is_unloaded = False

        if not self.mission:
            self.draw_last_mission()

        if disabled:
            self.disable()
        else:
            self.enable()


class MVCVehicleDrawBehavior(MVCBehavior, ABC):
    pass


class UAVDrawWidget(MultiVehicleContainerMixin):
    uav_position = ListProperty(None, allownone=True)

    def __init__(self, num: int, **kwargs):
        super().__init__(**kwargs)

        self._uav_added = False
        self._reposition_event = None

        self._marker = UAVMapMarker(num=num)
        self._marker_layer = ExtendedMarkerMapLayer()

    def on_parent(self, uav_draw_widget: UAVDrawWidget, parent_map_view: CustomMapView):
        if parent_map_view is not None:
            parent_map_view.add_layer(self._marker_layer)
        else:
            self._last_parent.remove_layer(self._marker_layer)

    def on_uav_position(
        self, widget: UAVDrawWidget, uav_position: List[Union[float, int]]
    ):
        if uav_position:
            self._draw_uav(
                lat=uav_position[0], lon=uav_position[1], angle=uav_position[2]
            )
        else:
            self._clear_uav()

    def schedule_layer_update(self, fps=30):
        if self._reposition_event is None:
            self._reposition_event = Clock.schedule_interval(
                lambda dt: self._marker_layer.reposition(), 1 / fps
            )

    def unschedule_layer_update(self):
        if self._reposition_event:
            self._reposition_event.cancel()
            self._reposition_event = None

    def _draw_uav(self, lat: float, lon: float, angle: int) -> None:
        if self._marker and not self._uav_added:
            self._marker.lat = lat
            self._marker.lon = lon
            self._marker.rotate_value_angle = angle
            self._marker_layer.add_widget(marker=self._marker)

            map_view = self.parent
            map_view.set_zoom_at(
                map_view.map_source.get_max_zoom() - 3, *map_view.center
            )
            map_view.center_on(lat, lon)

            self._uav_added = True

            return

        self._marker.anim_move(new_lat=lat, new_lon=lon, angle=angle)

    def _clear_uav(self):
        self._marker_layer.remove_widget(self._marker)
        self._uav_added = False
