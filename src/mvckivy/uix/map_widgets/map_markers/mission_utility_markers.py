from kivy.metrics import dp

from mvckivy import (
    StaticMapMarkerPopup,
    InteractiveMapMarkerPopup,
)

from utility import ProjectPathManager


class StaticChooseLineMapMarkerPopup(StaticMapMarkerPopup):
    def __init__(self, feature_num: int, polygon_num: int, point_num: int, **kwargs):
        super().__init__(
            feature_num,
            polygon_num,
            point_num,
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    "images", "map", "markers", "choose_line_marker.png"
                )
            ),
            **kwargs,
        )

        self.size = (dp(30), dp(30))


class StaticHomePointMapMarkerPopup(StaticMapMarkerPopup):
    def __init__(
        self,
        feature_num: int = -1,
        polygon_num: int = -1,
        point_num: int = -1,
        custom_text: str = "Home",
        **kwargs,
    ):
        super().__init__(
            feature_num,
            polygon_num,
            point_num,
            custom_text,
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    "images", "map", "markers", "home_marker.png"
                )
            ),
            **kwargs,
        )

        self.size = (dp(30), dp(30))


class StaticMissionInterruptionPointMapMarkerPopup(StaticMapMarkerPopup):
    def __init__(
        self,
        feature_num: int = -1,
        polygon_num: int = -1,
        point_num: int = -1,
        custom_text: str = "Стоп",
        **kwargs,
    ):
        super().__init__(
            feature_num,
            polygon_num,
            point_num,
            custom_text,
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    "images", "map", "markers", "interruption_marker.png"
                )
            ),
            **kwargs,
        )


class StaticMissionDrawPointMapMarkerPopup(StaticMapMarkerPopup):
    def __init__(
        self, point_num: int, feature_num: int = 0, polygon_num: int = 0, **kwargs
    ):
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

        self.size = (dp(18), dp(18))
        self.popup_size = (dp(35), dp(25))


class InteractiveMissionAvoidancePointMapMarkerPopup(InteractiveMapMarkerPopup):
    def __init__(self, feature_num: int, polygon_num: int, point_num: int, **kwargs):
        super().__init__(
            feature_num,
            polygon_num,
            point_num,
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    "images", "map", "markers", "avoidance_marker.png"
                )
            ),
            **kwargs,
        )


class StaticMissionAvoidancePointMapMarkerPopup(StaticMapMarkerPopup):
    def __init__(
        self,
        feature_num: int,
        polygon_num: int,
        point_num: int,
        custom_text=None,
        **kwargs,
    ):
        super().__init__(
            feature_num,
            polygon_num,
            point_num,
            custom_text=custom_text,
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    "images", "map", "markers", "avoidance_marker.png"
                )
            ),
            **kwargs,
        )


class InteractiveSprayingPointMapMarkerPopup(InteractiveMapMarkerPopup):
    def __init__(self, feature_num: int, polygon_num: int, point_num: int, **kwargs):
        super().__init__(
            feature_num,
            polygon_num,
            point_num,
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    "images", "map", "markers", "spraying_marker.png"
                )
            ),
            **kwargs,
        )


class StaticSprayingPointMapMarkerPopup(StaticMapMarkerPopup):
    def __init__(self, feature_num: int, polygon_num: int, point_num: int, **kwargs):
        super().__init__(
            feature_num,
            polygon_num,
            point_num,
            source=str(
                ProjectPathManager.get_assets_path().joinpath(
                    "images", "map", "markers", "spraying_marker.png"
                )
            ),
            **kwargs,
        )
