from __future__ import annotations

from kivy.properties import (
    ColorProperty,
    OptionProperty,
    AliasProperty,
    BooleanProperty,
)
from kivymd.uix.behaviors import RectangularRippleBehavior

from mvckivy.uix.behaviors.hover_behavior import ButtonHoverBehavior
from mvckivy.uix.label import AutoResizeIcon


class AutoResizeMDIconButton(
    RectangularRippleBehavior,
    ButtonHoverBehavior,
    AutoResizeIcon,
):
    style = OptionProperty(
        "standard", options=["standard", "filled", "tonal", "outlined"]
    )
    md_bg_color_disabled = ColorProperty(None)
    disabled = BooleanProperty(False)

    def _get_radius_list(self):
        return [self.height / 2]

    radius_list = AliasProperty(_get_radius_list, None, bind=("height",))

    @staticmethod
    def _with_alpha(color, a: float):
        if not color:
            return [0, 0, 0, a]
        r, g, b, _ = color
        return [r, g, b, a]

    def _get_bg_rgba(self):
        if not self.disabled:
            if self.theme_bg_color == "Primary":
                mapping = {
                    "standard": self.theme_cls.transparentColor,
                    "outlined": self.theme_cls.transparentColor,
                    "tonal": self.theme_cls.secondaryContainerColor,
                    "filled": self.theme_cls.primaryColor,
                }
                return mapping.get(self.style, self.theme_cls.transparentColor)
            return self.md_bg_color or self.theme_cls.transparentColor
        # disabled
        if self.md_bg_color_disabled:
            return self.md_bg_color_disabled
        if self.style == "tonal":
            a = self.icon_button_tonal_opacity_value_disabled_container
            return self._with_alpha(self.theme_cls.onSurfaceColor, a)
        if self.style == "filled":
            a = self.icon_button_filled_opacity_value_disabled_container
            return self._with_alpha(self.theme_cls.onSurfaceColor, a)
        return self.theme_cls.transparentColor

    bg_rgba = AliasProperty(
        _get_bg_rgba,
        None,
        bind=(
            "disabled",
            "style",
            "md_bg_color_disabled",
            "md_bg_color",
            "theme_bg_color",
        ),
    )

    def _get_line_rgba(self):
        if self.style != "outlined":
            return self.theme_cls.transparentColor
        if self.disabled:
            a = self.icon_button_outlined_opacity_value_disabled_line
            return self._with_alpha(self.theme_cls.onSurfaceColor, a)
        if self.theme_line_color == "Primary":
            return self.theme_cls.outlineColor
        custom = self.line_color
        return custom if custom is not None else self.theme_cls.transparentColor

    line_rgba = AliasProperty(
        _get_line_rgba,
        None,
        bind=("disabled", "style", "theme_line_color", "line_color"),
    )

    def _get_icon_rgba(self):
        if self.theme_icon_color == "Primary":
            mapping = {
                "standard": self.theme_cls.primaryColor,
                "tonal": self.theme_cls.onSecondaryContainerColor,
                "filled": self.theme_cls.onPrimaryColor,
                "outlined": self.theme_cls.onSurfaceVariantColor,
            }
            return mapping.get(self.style, self.theme_cls.onSurfaceVariantColor)
        return self.icon_color or self.theme_cls.transparentColor

    icon_rgba = AliasProperty(
        _get_icon_rgba, None, bind=("style", "theme_icon_color", "icon_color")
    )

    def _get_disabled_icon_rgba(self):
        custom = self.icon_color_disabled
        if custom is not None:
            return custom
        a_map = {
            "standard": self.icon_button_standard_opacity_value_disabled_icon,
            "tonal": self.icon_button_tonal_opacity_value_disabled_icon,
            "filled": self.icon_button_filled_opacity_value_disabled_icon,
            "outlined": self.icon_button_outlined_opacity_value_disabled_icon,
        }
        return self._with_alpha(
            self.theme_cls.onSurfaceColor, a_map.get(self.style, 0.38)
        )

    disabled_icon_rgba = AliasProperty(
        _get_disabled_icon_rgba, None, bind=("style", "icon_color_disabled")
    )
