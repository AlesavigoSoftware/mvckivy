from kivymd.uix.boxlayout import MDBoxLayout

from mvckivy import MenuItems


class MapSourceMenuItems(MenuItems):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extend(
            [
                {
                    "leading_icon": "map-marker-distance",
                    "text": "Схема",
                    "on_release": lambda: self.controller.dispatch_to_model(
                        map_source="osm-de"
                    ),
                },
                {
                    "leading_icon": "space-station",
                    "text": "Спутник",
                    "on_release": lambda: self.controller.dispatch_to_model(
                        map_source="osm-hot"
                    ),
                },
                {
                    "leading_icon": "map-legend",
                    "text": "Гибрид",
                    "on_release": lambda: self.controller.dispatch_to_model(
                        map_source="osm-fr"
                    ),
                },
            ]
        )


class MapSourceMenuHeader(MDBoxLayout):
    pass
