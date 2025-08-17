from __future__ import annotations

from typing import List, Type, Union

from kivy.properties import ListProperty, NumericProperty
from kivy_garden.mapview.clustered_marker_layer import Marker

from mvckivy import MultiVehicleContainerMixin
from mvckivy import MVCBehavior
from mvckivy import (
    InteractiveMissionPointMapMarkerPopup,
    InteractiveMissionAvoidancePointMapMarkerPopup,
    InteractiveSprayingPointMapMarkerPopup,
    InteractiveCenterAddNewMapMarkerPopup,
    StaticMissionPointMapMarkerPopup,
    StaticSprayingPointMapMarkerPopup,
    StaticMissionAvoidancePointMapMarkerPopup,
    DynamicMarker,
    StaticMarker,
)
from mvckivy import (
    InteractiveMapMarkerPopup,
    StaticMapMarkerPopup,
)
from mvckivy import (
    PolygonGeoJsonMapLayer,
    ExtendedMarkerMapLayer,
    ClusteredMarkerMapLayer,
)
from views.app_screen.children.main_screen.children import InputSprayingParamsContainer


class InteractiveInputWidget(MultiVehicleContainerMixin, MVCBehavior):
    feature_num = NumericProperty(
        0
    )  # Allows to set the unique color and other attributes
    polygon_num = NumericProperty(0)  # Separates polygons inside single feature

    markers = ListProperty([])

    def __init__(
        self,
        dynamic_marker_cls: Type[DynamicMarker],
        static_marker_cls: Type[StaticMarker],
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.is_read_mode = False
        self.is_disabled = False
        self.is_unloaded = False

        self.markers: List[List[List[List[Union[DynamicMarker, StaticMarker]]]]] = [
            [
                [
                    #  Markers list
                ],
            ],
        ]
        # Structure: feature [0] -> polygon [0][0] -> markers_list [0][0][0] =: [dynamic_marker, static_marker]
        # Основной управляющий механизм. Линии и полигоны (а также, очевидно, статические
        # маркеры) не являются интерактивными и необходимы исключительно в иллюстративных целях
        # Вся логика взаимодействия с маркерами происходит через динамические маркеры,
        self._dynamic_marker_menu_items: List[dict] = []
        self._static_marker_menu_items: List[dict] = []

        self._dynamic_marker_cls = dynamic_marker_cls
        self._static_marker_cls = static_marker_cls

        self._dynamic_marker_layer: ExtendedMarkerMapLayer = ExtendedMarkerMapLayer()
        self._dynamic_marker_layer.bind(on_marker_move=self.on_marker_move)
        self._dynamic_marker_layer.bind(
            on_marker_double_touch=self.on_marker_double_touch
        )

        self._static_marker_layer: ClusteredMarkerMapLayer = ClusteredMarkerMapLayer()
        self._static_marker_layer.build_cluster()
        # to build the first (empty) cluster and make sure that there is nothing on the screen
        self._static_marker_layer.bind(
            on_marker_double_touch=self.on_marker_double_touch
        )
        self._polygon_layer: PolygonGeoJsonMapLayer = PolygonGeoJsonMapLayer()

    def on_parent(self, input_widget: InteractiveInputWidget, parent_mapview):
        super().on_parent(input_widget, parent_mapview)

        if parent_mapview is not None:
            parent_mapview.add_layer(self._polygon_layer)
            parent_mapview.add_layer(self._static_marker_layer)
            parent_mapview.add_layer(self._dynamic_marker_layer)
        else:
            self._last_parent.remove_layer(self._polygon_layer)
            self._last_parent.remove_layer(self._static_marker_layer)
            self._last_parent.remove_layer(self._dynamic_marker_layer)

    def redraw_polygon(self):
        self._polygon_layer.markers = self.markers  # Triggers polygon redraw

    def add_marker(
        self,
        lat: float,
        lon: float,
        parent_marker: InteractiveCenterAddNewMapMarkerPopup = None,
    ):
        if parent_marker:

            new_dynamic_marker = self._dynamic_marker_cls(
                lat=lat,
                lon=lon,
                feature_num=parent_marker.feature_num,
                polygon_num=parent_marker.polygon_num,
                point_num=parent_marker.point_num,
            )
            new_static_marker = self._static_marker_layer.add_marker(
                lat=lat,
                lon=lon,
                cls=self._static_marker_cls,
                options={
                    "feature_num": parent_marker.feature_num,
                    "polygon_num": parent_marker.polygon_num,
                    "point_num": parent_marker.point_num,
                },
                redraw=False,
            )
            self.markers[self.feature_num][self.polygon_num].insert(
                parent_marker.point_num, [new_dynamic_marker, new_static_marker]
            )

            for point_num in range(
                parent_marker.point_num + 1,
                len(self.markers[self.feature_num][self.polygon_num]),
            ):
                dynamic_marker, static_marker = self.markers[self.feature_num][
                    self.polygon_num
                ][point_num]
                dynamic_marker.point_num += 1
                dynamic_marker.on_point_num(
                    widget=None, point_num=point_num + 1
                )  # Trigger doesn't work
                static_marker.options["point_num"] += 1

            self._dynamic_marker_layer.add_widget(
                new_dynamic_marker
            )  # Triggers dynamic markers redraw

            self.redraw_polygon()

        else:

            new_dynamic_marker = self._dynamic_marker_cls(
                lat=lat,
                lon=lon,
                feature_num=self.feature_num,
                polygon_num=self.polygon_num,
                point_num=len(self.markers[self.feature_num][self.polygon_num]),
            )
            new_static_marker = self._static_marker_layer.add_marker(
                lat=lat,
                lon=lon,
                cls=self._static_marker_cls,
                options={
                    "feature_num": self.feature_num,
                    "polygon_num": self.polygon_num,
                    "point_num": len(self.markers[self.feature_num][self.polygon_num]),
                },
                redraw=False,
            )
            self.markers[self.feature_num][self.polygon_num].append(
                [new_dynamic_marker, new_static_marker]
            )
            self._dynamic_marker_layer.add_widget(new_dynamic_marker)  # Triggers redraw

            self.redraw_polygon()

    def start_new_polygon(self):
        pass

    def next_polygon(self):
        if len(self.markers[self.feature_num][self.polygon_num]) > 0:
            self.polygon_num += 1
            self.markers[self.feature_num].append([])

    def next_feature(self):
        if len(self.markers[self.feature_num][self.polygon_num]) > 0:
            self.markers.append([])  # New feature
            self.feature_num += 1
            self.markers[self.feature_num].append([])  # New polygon
            self.polygon_num = 0  # New polygon inside the new feature

    def redraw_central_markers(
        self, caller: Union[DynamicMarker, StaticMarker]
    ) -> None:
        print(f"INFO: Central marker draw for [{caller}]")

    def change_open_status_of_all_static_markers_popup(self) -> None:
        self._static_marker_layer.global_popup_open_status = (
            not self._static_marker_layer.global_popup_open_status
        )

        for marker in self._static_marker_layer.cluster_markers:
            if marker.widget:
                marker.widget.is_open = (
                    self._static_marker_layer.global_popup_open_status
                )

    def remove_marker(
        self,
        marker_map_layer: ExtendedMarkerMapLayer,
        marker: Union[DynamicMarker, StaticMarker],
    ) -> None:
        to_remove_markers = self.markers[marker.feature_num][marker.polygon_num][
            marker.point_num
        ]
        to_remove_dynamic_marker, to_remove_static_marker = to_remove_markers

        for point_num in range(
            marker.point_num + 1,
            len(self.markers[marker.feature_num][marker.polygon_num]),
        ):
            dynamic_marker, static_marker = self.markers[self.feature_num][
                self.polygon_num
            ][point_num]
            dynamic_marker.on_point_num(
                widget=None, point_num=point_num - 1
            )  # Trigger doesn't work
            dynamic_marker.point_num = point_num - 1
            static_marker.options["point_num"] -= 1
            # options проверяется только при создании нового экземпляра static_marker.widget,
            # так что если не добавлять здесь изменение point_num через marker.widget,
            # то нужно изменить _clear_cluster_info внутри ClusterMarkerLayer,
            # чтобы widget очищался со всей остальной служебной информацией, тогда reposition создаст его с нуля

        self.markers[self.feature_num][self.polygon_num].remove(to_remove_markers)
        self._dynamic_marker_layer.remove_widget(
            to_remove_dynamic_marker
        )  # Triggers redraw
        self._static_marker_layer.remove_marker(to_remove_static_marker)

        self.redraw_polygon()

    def on_marker_move(
        self,
        marker_map_layer: ExtendedMarkerMapLayer,
        marker: DynamicMarker,
        marker_coords: List[float],
    ) -> None:
        moved_markers = self.markers[marker.feature_num][marker.polygon_num][
            marker.point_num
        ]
        moved_dynamic_marker, moved_static_marker = moved_markers
        moved_static_marker.lat, moved_static_marker.lon = marker_coords
        # lat, lon используются внутри reposition, так что можно не задавать их отдельно для widget'а

        # if moved_static_marker.widget:
        #     moved_static_marker.widget.lat, moved_static_marker.widget.lon = marker_coords
        # TODO: Занести в заметки! Нашел способ взаимодействовать
        #  с cluster-маркерами точно так же, как и с обычными динамическими,
        #  однако при слишком большом перемещении маркера кластеры будут обрабатываться некорректно

        self.redraw_polygon()

    def _extend_marker_menu_items(
        self, marker: Union[DynamicMarker, StaticMarker], *args
    ) -> None:
        if isinstance(marker, InteractiveMapMarkerPopup):

            self._dynamic_marker_menu_items.extend(
                [
                    {
                        "text": "Удалить маркер",
                        "leading_icon": "vector-square-remove",
                        "on_release": lambda *_: self.remove_marker(
                            marker_map_layer=self._dynamic_marker_layer, marker=marker
                        ),
                    },
                    {
                        "text": "Центральные маркеры",
                        "leading_icon": "map-marker-radius",
                        "on_release": lambda *_: self.redraw_central_markers(
                            caller=marker
                        ),
                    },
                ]
            )

        elif isinstance(marker, StaticMapMarkerPopup):

            self._static_marker_menu_items.extend(
                [
                    {
                        "text": "Скрыть/показать №",
                        "leading_icon": "eye-outline",
                        "on_release": lambda *_: self.change_open_status_of_all_static_markers_popup(),
                    },
                ]
            )

    def on_marker_double_touch(
        self,
        marker_map_layer: ExtendedMarkerMapLayer,
        marker: Union[DynamicMarker, StaticMarker],
    ) -> None:

        if isinstance(marker, InteractiveCenterAddNewMapMarkerPopup):
            self._dynamic_marker_layer.remove_widget(marker)
            self.add_marker(lat=marker.lat, lon=marker.lon, parent_marker=marker)

        elif isinstance(
            marker,
            (
                InteractiveMissionPointMapMarkerPopup,
                InteractiveMissionAvoidancePointMapMarkerPopup,
                InteractiveSprayingPointMapMarkerPopup,
            ),
        ):
            self._extend_marker_menu_items(marker=marker)
            self.view.create_and_open_dropdown_menu(
                content=self._dynamic_marker_menu_items,
                caller=marker,
                position="center",
            )

        elif isinstance(
            marker,
            (
                StaticMissionPointMapMarkerPopup,
                StaticMissionAvoidancePointMapMarkerPopup,
                StaticSprayingPointMapMarkerPopup,
            ),
        ):
            self._extend_marker_menu_items(marker=marker)
            self.view.create_and_open_dropdown_menu(
                content=self._static_marker_menu_items, caller=marker, position="center"
            )

    def remove_polygon(self, feature_num: int, polygon_num: int) -> None:
        to_remove_polygon = self.markers[feature_num][polygon_num]

        for polygon_index in range(polygon_num + 1, len(self.markers[feature_num])):
            for markers_list in self.markers[feature_num][polygon_index]:
                dynamic_marker, static_marker = markers_list
                dynamic_marker.polygon_num -= 1
                static_marker.options["polygon_num"] -= 1

        for markers_list in to_remove_polygon:
            dynamic_marker, static_marker = markers_list
            self._dynamic_marker_layer.remove_widget(dynamic_marker)
            self._static_marker_layer.remove_marker(static_marker)

        self.markers[self.feature_num].remove(to_remove_polygon)

        if len(self.markers[self.feature_num]) == 0:
            self.markers[self.feature_num].append([])

        self.polygon_num = max(self.polygon_num - 1, 0)
        self.redraw_polygon()

    def remove_feature(self, feature_num: int) -> None:
        to_remove_feature = self.markers[feature_num]

        for feature_index in range(feature_num + 1, len(self.markers)):
            for polygon in self.markers[feature_index]:
                for markers_list in polygon:
                    dynamic_marker, static_marker = markers_list
                    dynamic_marker.feature_num -= 1
                    static_marker.options["feature_num"] -= 1

        for polygon in to_remove_feature:
            for markers_list in polygon:
                dynamic_marker, static_marker = markers_list
                self._dynamic_marker_layer.remove_widget(dynamic_marker)
                self._static_marker_layer.remove_marker(static_marker)

        self.markers.remove(to_remove_feature)

        if len(self.markers) == 0:
            self.markers.append(
                [
                    [],
                ]
            )

        self.feature_num = max(
            self.feature_num - 1, 0
        )  # Always points to the last feature index
        self.polygon_num = max(len(self.markers[self.feature_num]) - 1, 0)

        self.redraw_polygon()

    def dump_mission_data(self) -> List[List[List[float]]]:
        # TODO: Иметь в виду!
        #  This implementation doesn't save any information in case when feature has more than one polygon

        polygons = []
        for feature in self.markers:

            for polygon in feature:
                polygon_points = []

                for markers in polygon:
                    static_marker: Marker = markers[1]
                    polygon_points.append([static_marker.lat, static_marker.lon])

                polygons.append(polygon_points)

        return polygons

    def disable(self):
        if self.is_unloaded:
            return

        self._static_marker_layer.clear(animate_clear=True)
        self._dynamic_marker_layer.unload()
        self._polygon_layer.disable()

        self.is_disabled = True

    def enable(self, read_mode: bool = None):
        if self.is_unloaded:
            return

        self.read_mode() if read_mode else self.edit_mode()
        self._polygon_layer.enable()

        self.is_disabled = False

    def read_mode(self):
        if (
            self.is_unloaded or self.is_read_mode
        ) and not self.is_disabled:  # Optimization
            return

        self._dynamic_marker_layer.unload()
        self._static_marker_layer.redraw_markers(animate_draw=True)

        self.is_read_mode = True

        # In case if static markers were unloaded and lost some data.
        # Example: read_mode -> edit_mode (unloaded static_markers) -> add_marker
        # (adds new marker to cluster_markers where is nothing at this moment) -> read_mode
        # (from _last_markers were loaded all markers except for the last one)

        # TODO: Занести в заметки!
        #  Conclusion: unload is not applicable to static markers layer according to described reason.
        #  Using "clear - redraw" instead "unload - upload" is a way to solve this problem

        # TODO: Несмотря на найденное решение по вопросу создания маркеров, всплыла еще одна проблема,
        #  связанная с динамической перерисовкой. Теперь слой статических маркеров создается не единожды,
        #  с зафиксированным значением mapview.zoom, а каждый раз с нуля,
        #  сохраняя в качестве опорного зум в момент создания. Это приводит к ошибкам при кластеризации.
        #  Нужно попробовать задавать значение mapview.zoom
        #  при очистке данных кластера внутри маркера перед его отрисовкой.
        #  Теоретически, так можно симулировать единовременное создание всех маркеров

    def edit_mode(self):
        if (self.is_unloaded or not self.is_read_mode) and not self.is_disabled:
            return

        self._static_marker_layer.clear()
        self._dynamic_marker_layer.upload()

        self.is_read_mode = False

    def unload(self):
        self._static_marker_layer.clear()
        self._dynamic_marker_layer.unload()
        self._polygon_layer.unload()

        self.is_unloaded = True

    def upload(self, read_mode: bool = None, disabled: bool = None):
        self.is_unloaded = False

        self._polygon_layer.upload()

        if disabled:
            self.disable()
        else:
            self.enable(read_mode=read_mode)


class CreationPointInputWidget(InteractiveInputWidget):
    def __init__(
        self,
        dynamic_marker_cls: Type[DynamicMarker] = InteractiveMissionPointMapMarkerPopup,
        static_marker_cls: Type[StaticMarker] = StaticMissionPointMapMarkerPopup,
        **kwargs,
    ):
        super().__init__(dynamic_marker_cls, static_marker_cls, **kwargs)

    # def start_new_polygon(self):
    #     self.next_feature()

    def redraw_polygon(self):
        # Метод не может быть вызван из состояния полигона "disabled",
        # потому как в этом состоянии нет маркеров, которые могли бы вызвать перерисовку.
        # Учитывать при внесении изменений в логику взаимодействия с полигоном в будущем.
        # Сейчас основной и единственный управляющий слой - слой с динамическими маркерами
        self._polygon_layer.color_features = [
            [self._polygon_layer.POLYGON_COLORS.get("green")] * len(self.markers),
            [90] * len(self.markers),
        ]
        super().redraw_polygon()

    def _extend_marker_menu_items(
        self, marker: Union[DynamicMarker, StaticMarker], *args
    ) -> None:
        if isinstance(marker, InteractiveMapMarkerPopup):

            self._dynamic_marker_menu_items = [
                {
                    "text": "Удалить полигон",
                    "leading_icon": "delete-outline",
                    "on_release": lambda *_: self.remove_feature(
                        feature_num=marker.feature_num
                    ),
                },
            ]

        elif isinstance(marker, StaticMapMarkerPopup):

            self._static_marker_menu_items = [
                {
                    "text": "Выбрать грань",
                    "leading_icon": "map-marker-radius",
                    "on_release": lambda *_: self.redraw_central_markers(caller=marker),
                },
            ]

        super()._extend_marker_menu_items(marker, *args)


class AvoidancePointInputWidget(InteractiveInputWidget):
    def __init__(
        self,
        dynamic_marker_cls: Type[
            DynamicMarker
        ] = InteractiveMissionAvoidancePointMapMarkerPopup,
        static_marker_cls: Type[
            StaticMarker
        ] = StaticMissionAvoidancePointMapMarkerPopup,
        **kwargs,
    ):
        super().__init__(dynamic_marker_cls, static_marker_cls, **kwargs)

    def start_new_polygon(self):
        self.next_polygon()

    def redraw_polygon(self):
        self._polygon_layer.color_features = [
            [self._polygon_layer.POLYGON_COLORS.get("blue")] * len(self.markers),
            [80] * len(self.markers),
        ]
        super().redraw_polygon()

    def _extend_marker_menu_items(
        self, marker: Union[DynamicMarker, StaticMarker], *args
    ) -> None:
        if isinstance(marker, InteractiveMapMarkerPopup):

            self._dynamic_marker_menu_items = [
                {
                    "text": "Новый полигон",
                    "leading_icon": "vector-square-plus",
                    "on_release": lambda *_: self.start_new_polygon(),
                },
                {
                    "text": "Удалить полигон",
                    "leading_icon": "delete-outline",
                    "on_release": lambda *_: self.remove_polygon(
                        feature_num=marker.feature_num, polygon_num=marker.polygon_num
                    ),
                },
            ]

        elif isinstance(marker, StaticMapMarkerPopup):
            self._static_marker_menu_items = []

        super()._extend_marker_menu_items(marker, *args)


class SprayingPointInputWidget(InteractiveInputWidget):
    def __init__(
        self,
        dynamic_marker_cls: Type[
            DynamicMarker
        ] = InteractiveSprayingPointMapMarkerPopup,
        static_marker_cls: Type[StaticMarker] = StaticSprayingPointMapMarkerPopup,
        **kwargs,
    ):
        super().__init__(dynamic_marker_cls, static_marker_cls, **kwargs)

    def start_new_polygon(self):
        self.next_feature()

    def redraw_polygon(self):
        self._polygon_layer.color_features = [
            [self._polygon_layer.POLYGON_COLORS.get("orange")] * len(self.markers),
            [70] * len(self.markers),
        ]
        super().redraw_polygon()

    def _extend_marker_menu_items(
        self, marker: Union[DynamicMarker, StaticMarker], *args
    ) -> None:
        if isinstance(marker, InteractiveMapMarkerPopup):

            self._dynamic_marker_menu_items = [
                {
                    "text": "Новый полигон",
                    "leading_icon": "vector-square-plus",
                    "on_release": lambda *_: self.start_new_polygon(),
                },
                {
                    "text": "Удалить полигон",
                    "leading_icon": "delete-outline",
                    "on_release": lambda *_: self.remove_feature(
                        feature_num=marker.feature_num
                    ),
                },
                {
                    "text": "Задать параметры",
                    "leading_icon": "format-list-checkbox",
                    "on_release": lambda *_: self.view.refill_and_open_side_menu(
                        lambda: InputSprayingParamsContainer(
                            editable=True,
                            polygon_num=marker.feature_num,
                            uav_id=self.parent.active_uav,
                            last_params=self.parent.spraying_params,
                        )
                    ),
                },
            ]

        elif isinstance(marker, StaticMapMarkerPopup):
            self._static_marker_menu_items = [
                {
                    "text": "Открыть параметры",
                    "leading_icon": "format-list-checkbox",
                    "on_release": lambda *_: self.view.refill_and_open_side_menu(
                        lambda: InputSprayingParamsContainer(
                            editable=False,
                            polygon_num=marker.feature_num,
                            uav_id=self.parent.active_uav,
                            last_params=self.parent.spraying_params,
                        )
                    ),
                },
            ]

        super()._extend_marker_menu_items(marker, *args)
