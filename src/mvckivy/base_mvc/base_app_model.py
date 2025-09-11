from mvckivy.base_mvc import BaseModel
from mvckivy.properties import ExtendedConfigParserProperty
from mvckivy.properties.extended_config_parser_property import (
    ConfigParserString,
)
from mvckivy.utils.constants import Palette, Scheme


class BaseAppModel(BaseModel):
    language = ExtendedConfigParserProperty(
        "Русский",
        "DesignSettings",
        "language",
        "app",
        val_type=ConfigParserString,
        options=["English", "Русский"],
    )

    # App params
    theme_style = ExtendedConfigParserProperty(
        "Light",
        "DesignSettings",
        "dark_theme",
        "app",
        val_type=str,
        options=["Light", "Dark"],
    )
    primary_palette = ExtendedConfigParserProperty(
        "Darkviolet",
        "DesignSettings",
        "primary_palette",
        "app",
        val_type=str,
        options=Palette,
    )
    scheme_name = ExtendedConfigParserProperty(
        "FRUIT_SALAD",
        "DesignSettings",
        "scheme_name",
        "app",
        val_type=str,
        options=Scheme,
    )
