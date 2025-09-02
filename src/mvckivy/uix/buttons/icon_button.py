from kivy.properties import OptionProperty, ColorProperty
from kivymd.uix.behaviors import RectangularRippleBehavior

from mvckivy import ButtonHoverBehavior
from ..label import AutoResizeIcon


class AutoResizeMDIconButton(
    RectangularRippleBehavior, ButtonHoverBehavior, AutoResizeIcon
):
    style = OptionProperty(
        "standard", options=("standard", "filled", "tonal", "outlined")
    )
    md_bg_color_disabled = ColorProperty(None)
    _line_color = ColorProperty(None)

    def on_line_color(self, instance, value) -> None:
        if not self.disabled and self.theme_line_color == "Custom":
            self._line_color = value
