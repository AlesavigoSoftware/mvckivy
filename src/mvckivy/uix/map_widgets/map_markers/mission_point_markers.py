from kivy.core.window import Window

from utility import ProjectPathManager
from mvckivy import (
    InteractiveMapMarkerPopup,
    StaticMapMarkerPopup,
)


class InteractiveMissionPointMapMarkerPopup(InteractiveMapMarkerPopup):
    def __init__(self, feature_num: int, polygon_num: int, point_num: int, **kwargs):
        super().__init__(
            feature_num,
            polygon_num,
            point_num,
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    "images", "map", "markers", "mission_marker.png"
                )
            ),
            **kwargs,
        )


class StaticMissionPointMapMarkerPopup(StaticMapMarkerPopup):
    def __init__(
        self,
        feature_num: int,
        polygon_num: int,
        point_num: int,
        custom_text: str = None,
        **kwargs,
    ):
        super().__init__(
            feature_num,
            polygon_num,
            point_num,
            custom_text,
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    "images", "map", "markers", "mission_marker.png"
                )
            ),
            **kwargs,
        )


class InteractiveCenterAddNewMapMarkerPopup(InteractiveMapMarkerPopup):
    def __init__(self, feature_num: int, polygon_num: int, point_num: int, **kwargs):
        super().__init__(
            feature_num,
            polygon_num,
            point_num,  # Equals to its future MissionPointMapMarker point_num
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    "images", "map", "markers", "plus_marker.png"
                )
            ),
            **kwargs,
        )

        self.placeholder.clear_widgets()
        self.placeholder = 0

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        Window.set_system_cursor("arrow")

    def on_touch_move(self, touch):
        return
