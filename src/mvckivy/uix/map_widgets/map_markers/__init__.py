from typing import TypeVar

from .base_markers import InteractiveMapMarkerPopup, StaticMapMarkerPopup
from .mission_point_markers import (StaticMissionPointMapMarkerPopup,
                                    InteractiveMissionPointMapMarkerPopup,
                                    InteractiveCenterAddNewMapMarkerPopup)
from .uav_marker import UAVMapMarker
from .mission_utility_markers import (StaticHomePointMapMarkerPopup,
                                      StaticMissionInterruptionPointMapMarkerPopup,
                                      InteractiveMissionAvoidancePointMapMarkerPopup,
                                      StaticMissionAvoidancePointMapMarkerPopup,
                                      InteractiveSprayingPointMapMarkerPopup,
                                      StaticSprayingPointMapMarkerPopup,
                                      StaticChooseLineMapMarkerPopup,
                                      StaticMissionDrawPointMapMarkerPopup)

DynamicMarker = TypeVar('DynamicMarker', bound=InteractiveMapMarkerPopup)
StaticMarker = TypeVar('StaticMarker', bound=StaticMapMarkerPopup)
