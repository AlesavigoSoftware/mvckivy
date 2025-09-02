from datetime import datetime

from kivy import platform
from kivy.properties import OptionProperty

from mvckivy.base_mvc import BaseModel
from mvckivy.properties import ExtendedConfigParserProperty
from mvckivy.utils.constants import (
    AVAILABLE_PLATFORMS,
    DEVICE_ORIENTATIONS,
    DEVICE_TYPES,
    INPUT_MODES,
    DESKTOP_PLATFORMS,
)


class BaseAppModel(BaseModel):
    # ID params
    session_id = datetime.now().strftime("%Y%m%d%H%M%S")

    # App behavior params
    platform = OptionProperty("unknown", options=[*AVAILABLE_PLATFORMS, "unknown"])
    device_orientation = OptionProperty("none", options=[*DEVICE_ORIENTATIONS, "none"])
    device_type = OptionProperty("none", options=[*DEVICE_TYPES, "none"])
    input_mode = OptionProperty("none", options=[*INPUT_MODES, "none"])
    language = ExtendedConfigParserProperty(
        "Русский", "DesignSettings", "language", "app", val_type=str
    )
    language_options = OptionProperty("Русский", options=["Русский", "English"])

    # App params
    theme_style = ExtendedConfigParserProperty(
        "Light", "DesignSettings", "dark_theme", "app", val_type=str
    )
    primary_palette = ExtendedConfigParserProperty(
        "Darkviolet", "DesignSettings", "primary_palette", "app", val_type=str
    )
    scheme_name = ExtendedConfigParserProperty(
        "FRUIT_SALAD", "DesignSettings", "scheme_name", "app", val_type=str
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_model = self
        self.platform = platform
        self.input_mode = (
            "mouse" if self.platform in DESKTOP_PLATFORMS else "touch"
        )  # TODO: Implement dynamic input control system
        self.app.theme_cls.bind(device_orientation=self.setter("device_orientation"))
        self.device_orientation = self.app.theme_cls.device_orientation
