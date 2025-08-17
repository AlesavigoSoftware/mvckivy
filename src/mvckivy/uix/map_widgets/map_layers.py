import copy
import json
from typing import List, Optional, Union

from kivy import Logger
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import (
    ListProperty,
    BooleanProperty,
    ReferenceListProperty,
    NumericProperty,
    StringProperty,
)
from kivy_garden.mapview.clustered_marker_layer import ClusteredMarkerLayer, Marker
from math import radians, log, tan, cos, pi

from kivy.graphics import Color, Line
from kivy.graphics.context_instructions import Translate, Scale, PushMatrix, PopMatrix

from kivy_garden.mapview import MapLayer, MarkerMapLayer, MapMarker
from kivy_garden.mapview.geojson import GeoJsonMapLayer, COLORS
from kivy_garden.mapview.utils import clamp
from kivy_garden.mapview.constants import (
    MIN_LONGITUDE,
    MAX_LONGITUDE,
    MIN_LATITUDE,
    MAX_LATITUDE,
)

from mvckivy import DynamicMarker, StaticMarker


class LineMapLayer(MapLayer):
    color: ListProperty = ListProperty([])

    disabled_status = BooleanProperty(False)

    draw_line_anim_transition = StringProperty("in_sine")
    draw_line_anim_duration = NumericProperty(1.2)

    def __init__(
        self,
        coordinates: List[List[float]] = None,
        color: List[float] = None,
        width: float = None,
        animate_drawing: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if color is None:
            color = [0 / 255, 0 / 255, 255 / 255, 1]  # Blue by default

        if coordinates is None:
            coordinates = [[0, 0], [0, 0]]

        if width is None:
            width = 2

        self._coordinates = coordinates
        self._color = color

        self._width = width
        self._animate_drawing = animate_drawing

        self._line_points = None
        self._line_points_offset = (0, 0)
        self.zoom = 0
        self.lon = 0
        self.lat = 0
        self.ms = 0

        self._last_color: List[float] = []
        self._last_coordinates: List[List[float]] = []

    def on_color(self, instance, value):
        self._color = value
        self.redraw_line(animate=self._animate_drawing)

    @property
    def coordinates(self):
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates):
        self._coordinates = coordinates
        self.invalidate_line_points()
        self.redraw_line(animate=self._animate_drawing)

    def on_disabled_status(self, instance, disabled_status: bool):
        if disabled_status:
            self._last_color = self._color.copy()
            self.color = [150 / 255, 150 / 255, 150 / 255, 0.7]
        else:
            self.color = self._last_color.copy()

    @property
    def line_points(self):
        if self._line_points is None:
            self.calc_line_points()
        return self._line_points

    @property
    def line_points_offset(self):
        if self._line_points is None:
            self.calc_line_points()
        return self._line_points_offset

    def calc_line_points(self):
        # Offset all points by the coordinates of the first point,
        # to keep coordinates closer to zero.
        # (and therefore avoid some float precision issues when drawing lines)
        self._line_points_offset = (
            self.get_x(self._coordinates[0][1]),
            self.get_y(self._coordinates[0][0]),
        )
        # Since lat is not a linear transform we must compute manually
        self._line_points = [
            (
                self.get_x(lon) - self._line_points_offset[0],
                self.get_y(lat) - self._line_points_offset[1],
            )
            for lat, lon in self._coordinates
        ]

    def invalidate_line_points(self):
        self._line_points = None
        self._line_points_offset = (0, 0)

    def get_x(self, lon):
        """Get the x position on the map using this map source's projection
        (0, 0) is located at the top left.
        """
        return clamp(lon, MIN_LONGITUDE, MAX_LONGITUDE) * self.ms / 360.0

    def get_y(self, lat):
        """Get the y position on the map using this map source's projection
        (0, 0) is located at the top left.
        """
        lat = radians(clamp(-lat, MIN_LATITUDE, MAX_LATITUDE))
        return (1.0 - log(tan(lat) + 1.0 / cos(lat)) / pi) * self.ms / 2.0

    def reposition(self):
        map_view = self.parent

        # Must redraw when the zoom changes
        # as the scatter transform resets for the new tiles
        if (
            self.zoom != map_view.zoom
            or self.lon != round(map_view.lon, 7)
            or self.lat != round(map_view.lat, 7)
        ):
            map_source = map_view.map_source
            self.ms = pow(2.0, map_view.zoom) * map_source.dp_tile_size
            self.invalidate_line_points()
            self.redraw_line()

    def redraw_line(self, animate=False) -> None:
        self.clear()
        self._draw_line(animate=animate)

    def clear(self, animate=False) -> None:
        with self.canvas:

            if animate:
                Animation(
                    opacity=0,
                    d=self.draw_line_anim_duration,
                    t=self.draw_line_anim_transition,
                ).start(self.canvas)

            self.canvas.clear()
            self.canvas.opacity = 1

        self.clear_widgets()

    def unload(self) -> None:
        self.clear()
        self._last_coordinates = (
            self._coordinates.copy() if self._coordinates else self._last_coordinates
        )
        self._coordinates = [
            [0, 0],
        ]

    def upload(self) -> None:
        self._coordinates = self._last_coordinates
        self.reposition()

    def disable(self):
        self.disabled_status = True

    def enable(self):
        self.disabled_status = False

    def _draw_line(self, *args, animate=False):
        map_view = self.parent
        self.zoom = map_view.zoom
        self.lon = map_view.lon
        self.lat = map_view.lat

        # When zooming we must undo the current scatter transform
        # or the animation distorts it
        scatter = map_view._scatter
        sx, sy, ss = scatter.x, scatter.y, scatter.scale

        # Account for map source tile size and map screen zoom
        vx, vy, vs = map_view.viewport_pos[0], map_view.viewport_pos[1], map_view.scale

        end_points = []
        for point in self.line_points:
            end_points.extend(point)

        with self.canvas:
            PushMatrix()
            Translate(*map_view.pos)
            Scale(1 / ss, 1 / ss, 1)
            Translate(-sx, -sy)
            Scale(vs, vs, 1)
            Translate(-vx, -vy)
            Translate(self.ms / 2, 0)
            Translate(*self.line_points_offset)
            Color(*self._color)

        if animate:
            end_points_list = [
                (*self.line_points[i - 1], *self.line_points[i])
                for i in range(1, len(self.line_points))
            ]
            lines = [
                Line(points=point[:2] * 2, width=self._width)
                for point in end_points_list
            ]

            for line in lines:
                self.canvas.add(line)

            self.canvas.add(PopMatrix())

            for index, line in enumerate(lines):
                Animation(
                    points=end_points_list[index],
                    d=self.draw_line_anim_duration,
                    t=self.draw_line_anim_transition,
                ).start(line)

        else:

            self.canvas.add(Line(points=end_points, width=self._width))
            self.canvas.add(PopMatrix())


class GeoJsonGenerator:
    BUILT_IN_COLORS = COLORS
    DEFAULT_COLOR_FEATURE = [[BUILT_IN_COLORS.get("cyan")], [90]]
    DEFAULT_GEOJSON = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "color": f"{DEFAULT_COLOR_FEATURE[0][0]}{DEFAULT_COLOR_FEATURE[1][0]}",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [0.0, 0.0],  # Polygon needs at least couple of vertices
                            [0.0, 0.0],
                        ],
                    ],
                },
            }
        ],
    }

    def __init__(
        self,
        color_features: List[List[Union[str, int]]] = None,
        markers: List[Marker] = None,
    ):

        if markers is None:
            markers = []

        if color_features is None:
            color_features = GeoJsonGenerator.DEFAULT_COLOR_FEATURE

        self._markers = markers
        self._color_features: List[List[Union[str, int]]] = color_features
        self._geojson: dict = copy.deepcopy(GeoJsonGenerator.DEFAULT_GEOJSON)

    @property
    def markers(self) -> Optional[List[List[List[List[Marker]]]]]:
        return self._markers

    @markers.setter
    def markers(self, markers: Optional[List[List[List[List[Marker]]]]]):
        self._markers = markers
        self._check_and_fix_color_features()
        self._update_geojson(markers=True)

    @property
    def color_features(self) -> List[List[Union[str, int]]]:
        return self._color_features

    @color_features.setter
    def color_features(self, color_features: List[List[Union[str, int]]]):
        self._color_features = color_features
        self._check_and_fix_color_features()
        self._update_geojson(color_features=True)

    @property
    def geojson(self) -> dict:
        return self._geojson

    @staticmethod
    def _get_gps_coordinates_from_markers(
        markers: List[List[Marker]],
    ) -> List[List[float]]:
        return [[marker[0].lon, marker[0].lat] for marker in markers]

    def _check_and_fix_color_features(self):
        if len(self._color_features[0]) < len(self._markers) or len(
            self._color_features[1]
        ) < len(self._markers):
            Logger.warning(
                f"Polygon color: color features ({len(self._color_features)}) < "
                f"marker features ({len(self._markers)}), so the first ones replaced with "
                f"default color features: {GeoJsonGenerator.DEFAULT_COLOR_FEATURE}"
            )
            self._fill_color_features_with_defaults()

    def _fill_color_features_with_defaults(self):
        self._color_features = [
            [
                GeoJsonGenerator.DEFAULT_COLOR_FEATURE[0].copy()
                for _ in range(len(self._markers))
            ],
            [
                GeoJsonGenerator.DEFAULT_COLOR_FEATURE[1].copy()
                for _ in range(len(self._markers))
            ],
        ]

    def _generate_geojson(self) -> None:
        if self._markers:

            self._check_and_fix_color_features()

            self._geojson = {"type": "FeatureCollection", "features": []}

            for feature_index, feature in enumerate(self.markers):
                new_feature = {
                    "type": "Feature",
                    "properties": {
                        "color": f"{self._color_features[0][feature_index]}"
                        f"{self._color_features[1][feature_index]}",
                    },
                    "geometry": {"type": "Polygon", "coordinates": []},
                }

                for polygon_index, polygon_markers in enumerate(feature):
                    point_coords = self._get_gps_coordinates_from_markers(
                        polygon_markers
                    )

                    if point_coords:
                        new_feature["geometry"]["coordinates"].append(point_coords)

                if new_feature["geometry"]["coordinates"]:
                    self._geojson["features"].append(new_feature)

            if self._geojson["features"]:
                return

        self._geojson = copy.deepcopy(GeoJsonGenerator.DEFAULT_GEOJSON)

    def _update_geojson(self, markers=False, color_features=False):

        if markers:

            self._geojson = None
            self._generate_geojson()

        elif color_features:

            for feature_index, feature in enumerate(self._geojson["features"]):
                feature["properties"]["color"] = (
                    f"{self._color_features[0][feature_index]}"
                    f"{self._color_features[1][feature_index]}"
                )


class PolygonGeoJsonMapLayer(GeoJsonMapLayer):
    """
    Класс предназначен для отрисовки небольшого числа (до 100) *динамических* полигонов на основе GEOJSON.
    Не оптимизирован. Для эффективной отрисовки *динамических* полигонов
    требуется реализация наподобие LineMapLayer, с пропуском конвертации в GEOJSON.
    Формат последнего годится разве что для статичной отрисовки небольшого (до 1000) числа
    статических объектов разного типа: маркеров, линий, полигонов, или до 100 динамических соответственно.
    """

    POLYGON_COLORS = GeoJsonGenerator.BUILT_IN_COLORS

    colors = ListProperty([])
    opacities = ListProperty([])
    color_features = ReferenceListProperty(colors, opacities)

    disabled_status = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._geojson_generator = GeoJsonGenerator()
        self._last_geojson: Optional[dict] = None
        self._last_color_features: Optional[List[List[Union[str, int]]]] = None
        self._markers = None

    @property
    def markers(self):
        return self._markers

    @markers.setter
    def markers(self, markers: List[List[List[List[Marker]]]]):
        self._markers = markers
        self._geojson_generator.markers = self._markers
        self.geojson = self._geojson_generator.geojson

    def on_source(self, instance, value):
        if value.startswith("{"):
            self.geojson: Optional[dict] = json.loads(value)
        else:
            super().on_source(instance, value)

    def on_geojson(self, instance, geojson, update=False, stop_recursion: bool = False):

        if stop_recursion:
            super().on_geojson(
                instance, geojson, update
            )  # Update already created layer (from reposition)
            return

        if geojson:
            self.initial_zoom = (
                None  # **Full update** of the layer needs initial_zoom clear
            )
            super().on_geojson(instance, geojson, update)
            self.reposition()  # Triggers on_geojson with flag stop_recursion

        else:
            Logger.info(f"GEOJSON: No dynamic markers added so there is no geojson")
            self._clear()

    def reposition(self):
        # TODO: Занести в заметки! При scale != 1.0 происходит смещение полигона за пределы отображаемой области карты.
        #  Баг временно купирован для десктопных решений, но масштабирование на мобильных устройствах не проверялось
        vx, vy = self.parent.delta_x, self.parent.delta_y
        pzoom = self.parent.zoom
        zoom = self.initial_zoom
        if zoom is None:
            self.initial_zoom = zoom = pzoom
        if zoom != pzoom:
            diff = 2 ** (pzoom - zoom)
            vx /= diff
            vy /= diff
            self.g_scale.x = self.g_scale.y = diff
        else:
            self.g_scale.x = self.g_scale.y = 1.0
        self.g_translate.xy = vx, vy
        self.g_matrix.matrix = self.parent._scatter.transform

        if self.geojson:
            update = not self.first_time
            self.on_geojson(self, self.geojson, update=update, stop_recursion=True)
            self.first_time = False

    def on_color_features(self, instance, color_features: List[List[Union[str, int]]]):
        self._geojson_generator.color_features = color_features
        self.geojson = self._geojson_generator.geojson
        # Doesn't trigger on_geojson because color is an internal property
        # of the geojson dict. Read docs (ListProperty on kivy.docs) to learn more
        self.on_geojson(instance=self, geojson=self._geojson_generator.geojson)

    def _clear(self):
        self.clear_widgets()
        self.canvas_line.clear()
        # self.canvas.clear()  # Removes all canvas instructions at all
        self.geojson = copy.deepcopy(self._geojson_generator.DEFAULT_GEOJSON)

    def _is_default_geojson(self) -> bool:
        if not self.geojson:
            return True
        return self.geojson["features"][0]["geometry"]["coordinates"] == [
            [[0.0, 0.0], [0.0, 0.0]]
        ]

    def unload(self) -> None:
        self._last_geojson = (
            copy.deepcopy(self.geojson)
            if not self._is_default_geojson()
            else self._last_geojson
        )
        self._clear()

    def upload(self) -> None:
        self.geojson = (
            self._last_geojson
            if self._is_default_geojson() and self._last_geojson
            else self.geojson
        )
        # Triggers on_geojson -> redraw

    #     In this case we don't need a copy because _last_geojson only reassigns,
    #     and it is not intended to change it inside

    def get_latlon_at(self, pos_x, pos_y):
        return self.parent.get_latlon_at(pos_x, pos_y)

    def on_disabled_status(self, instance, disabled_status: bool):

        if not self.markers:
            return

        if disabled_status:

            self._last_geojson = copy.deepcopy(self.geojson)
            self._last_color_features = [self.colors.copy(), self.opacities.copy()]
            # Reason: ReferenceProperty doesn't work with deepcopy

            self.color_features = [
                [self.POLYGON_COLORS.get("grey")] * len(self.markers),
                [70]
                * len(
                    self.markers
                ),  # count of features, polygons don't have its own color
            ]

        else:

            self.geojson = self._last_geojson
            self.on_geojson(instance=self, geojson=self.geojson)  # Just in case
            self.color_features = self._last_color_features

    def disable(self):
        self.disabled_status = True

    def enable(self):
        self.disabled_status = False


class ClusteredMarkerMapLayer(ClusteredMarkerLayer):
    draw_animation_duration = NumericProperty(0.1)
    draw_animation_transition = StringProperty("linear")

    clear_animation_duration = NumericProperty(0.1)
    clear_animation_transition = StringProperty("linear")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_marker_single_touch")
        self.register_event_type("on_marker_double_touch")
        self.register_event_type("on_marker_triple_touch")

        self.cluster_min_zoom = 5
        self.cluster_max_zoom = 22
        self.cluster_radius = "15dp"

        # self.reposition()  # Выполняется при инициализации экземпляра автоматически,
        # т.к. карта при отрисовке сразу же изменяет свое состояние
        self._last_markers: List[Marker] = []

        self.global_popup_open_status = True

    def on_marker_single_touch(self, marker: Union[DynamicMarker, StaticMarker]):
        pass

    def on_marker_triple_touch(self, marker: Union[DynamicMarker, StaticMarker]):
        pass

    def on_marker_double_touch(self, marker: Union[DynamicMarker, StaticMarker]):
        pass

    def clear(self, animate_clear=False):
        self.build_cluster()
        # Все маркеры получают информацию о кластере
        self.reposition(rebuild_cluster=True, animate_clear=animate_clear)
        # Очищает *уже нанесенные (!)* маркеры, то есть те, у которых задана информация о кластере.
        # Те же, у которых данные значения пусты (например, у свежедобавленных), наоборот, выводятся на экран.

    def add_marker(
        self,
        lon: float,
        lat: float,
        cls=MapMarker,
        options: dict = None,
        redraw: bool = False,
    ) -> Marker:
        marker = super().add_marker(lon, lat, cls, options)

        if redraw:
            self.redraw_markers()

        return marker

    def remove_marker(self, marker, redraw: bool = False) -> None:
        if marker in self.cluster_markers:
            super().remove_marker(marker)

        if redraw:  # Doesn't use in static layer. Added for the future releases
            self.redraw_markers()

    def marker_collision(self):
        self.parent._touch_moved = (
            True  # To prevent on_single_touch map event dispatching
        )

    def _clear_cluster_info(self):
        for marker in self.cluster_markers:
            # clear all cluster information
            marker.id = None
            marker.zoom = float("inf")
            marker.parent_id = None
            marker.widget = None

    def clear_widgets(self, children=None, animate_clear=False):
        if not animate_clear:
            return super().clear_widgets(children=children)

        for widget in self.children[:]:
            widget.opacity = 1
            anim = Animation(
                opacity=0,
                d=self.clear_animation_duration,
                t=self.clear_animation_transition,
            )
            anim.bind(on_complete=lambda *args: self.remove_widget(widget))
            anim.start(widget)

    def reposition(
        self, rebuild_cluster=False, animate_draw=False, animate_clear=False
    ):
        if self.cluster is None or rebuild_cluster:
            self.build_cluster()
        margin = dp(48)
        mapview = self.parent
        set_marker_position = self.set_marker_position
        bbox = mapview.get_bbox(margin)
        bbox = (bbox[1], bbox[0], bbox[3], bbox[2])

        self.clear_widgets(animate_clear=animate_clear)

        for point in self.cluster.get_clusters(bbox, mapview.zoom):
            widget = point.widget
            if widget is None:
                widget = self.create_widget_for(point)
            set_marker_position(mapview, widget)

            widget.is_open = self.global_popup_open_status

            if not animate_draw:

                self.add_widget(widget)

            else:

                widget.opacity = 0
                self.add_widget(widget)
                Animation(
                    opacity=1,
                    d=self.draw_animation_duration,
                    t=self.draw_animation_transition,
                ).start(widget)

    def redraw_markers(self, animate_draw=False):
        self._clear_cluster_info()
        self.reposition(rebuild_cluster=True, animate_draw=animate_draw)

    # TODO: Занести в заметки! Набор необходимых операций (API) для любого наследника MapLayer:
    #  1. clear - очищает экран от нанесенных маркеров и (при наличии) удаляет служебную информацию
    #  , например, данные о кластере у маркеров. Отличается от clear_widgets тем,
    #  что после очистки первым способом, данные не отображаются при вызове reposition
    #  2. unload - полная очистка всех данных слоя, откат его к первоначальному состоянию.
    #  Пришел к выводу о полезности наличия механизма "отката", отсюда следующих пункт
    #  3. upload (redraw: bool) - возврат значений после пред. команды с последующей отрисовкой на экран или без нее

    def unload(self) -> None:
        self._last_markers = (
            self.cluster_markers.copy() if self.cluster_markers else self._last_markers
        )
        # To avoid full clear after 2 or more unloads in line
        self.cluster_markers = []
        self.clear()

    def upload(self, redraw=True) -> None:
        self.cluster_markers = self._last_markers

        if redraw:
            self.redraw_markers()

    def get_latlon_at(self, pos_x, pos_y):
        return self.parent.get_latlon_at(pos_x, pos_y)


class ExtendedMarkerMapLayer(MarkerMapLayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.register_event_type("on_marker_move")
        self.register_event_type("on_marker_single_touch")
        self.register_event_type("on_marker_double_touch")
        self.register_event_type("on_marker_triple_touch")

        self._last_markers: List = []

    def on_marker_move(
        self, marker: Union[DynamicMarker, StaticMarker], marker_coords: List[float]
    ):
        pass

    def on_marker_single_touch(self, marker: Union[DynamicMarker, StaticMarker]):
        pass

    def on_marker_triple_touch(self, marker: Union[DynamicMarker, StaticMarker]):
        pass

    def on_marker_double_touch(self, marker: Union[DynamicMarker, StaticMarker]):
        pass

    def add_widget(self, marker):
        super().add_widget(marker)
        self.reposition()  # To fix view bug

    def remove_widget(self, marker):
        if marker in self.markers:
            super().remove_widget(marker)
        self.reposition()  # To fix view bug

    def marker_collision(self):
        self.parent._touch_moved = (
            True  # To prevent on_single_touch map event dispatching
        )

    def clear(self):
        self.unload()

    def unload(self) -> None:
        self._last_markers = self.markers.copy() if self.markers else self._last_markers
        super().unload()

    def upload(self) -> None:
        self.markers = self._last_markers
        self.reposition()

    def get_latlon_at(self, pos_x, pos_y):
        return self.parent.get_latlon_at(pos_x, pos_y)
