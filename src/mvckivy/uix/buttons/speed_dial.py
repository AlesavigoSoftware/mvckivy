from __future__ import annotations

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivymd.font_definitions import theme_font_styles
from typing import Optional, Union

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    DictProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
    VariableListProperty,
    BoundedNumericProperty,
)

from kivy.weakproxy import WeakProxy
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import (
    CommonElevationBehavior,
    DeclarativeBehavior,
    RotateBehavior,
    RectangularRippleBehavior,
)
from kivymd.uix.label import MDLabel
from kivymd.uix.tooltip import MDTooltip

from mvckivy import ButtonHoverBehavior
from mvckivy import MVCFloatLayout


FLOATING_ACTION_BUTTON_M2_ELEVATION = 1
FLOATING_ACTION_BUTTON_M2_OFFSET = (0, -1)
FLOATING_ACTION_BUTTON_M3_ELEVATION = 0.5
FLOATING_ACTION_BUTTON_M3_OFFSET = (0, -2)
FLOATING_ACTION_BUTTON_M3_SOFTNESS = 0
RAISED_BUTTON_OFFSET = (0, -2)

text_colors = {
    "Red": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "FFFFFF",
        "500": "FFFFFF",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "FFFFFF",
        "A400": "FFFFFF",
        "A700": "FFFFFF",
    },
    "Pink": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "FFFFFF",
        "400": "FFFFFF",
        "500": "FFFFFF",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "FFFFFF",
        "A400": "FFFFFF",
        "A700": "FFFFFF",
    },
    "Purple": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "FFFFFF",
        "400": "FFFFFF",
        "500": "FFFFFF",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "FFFFFF",
        "A400": "FFFFFF",
        "A700": "FFFFFF",
    },
    "DeepPurple": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "FFFFFF",
        "400": "FFFFFF",
        "500": "FFFFFF",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "FFFFFF",
        "A400": "FFFFFF",
        "A700": "FFFFFF",
    },
    "Indigo": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "FFFFFF",
        "400": "FFFFFF",
        "500": "FFFFFF",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "FFFFFF",
        "A400": "FFFFFF",
        "A700": "FFFFFF",
    },
    "Blue": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "FFFFFF",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "FFFFFF",
        "A400": "FFFFFF",
        "A700": "FFFFFF",
    },
    "LightBlue": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "000000",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "000000",
        "A400": "000000",
        "A700": "FFFFFF",
    },
    "Cyan": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "000000",
        "600": "000000",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "000000",
        "A400": "000000",
        "A700": "000000",
    },
    "Teal": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "FFFFFF",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "000000",
        "A400": "000000",
        "A700": "000000",
    },
    "Green": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "000000",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "000000",
        "A400": "000000",
        "A700": "000000",
    },
    "LightGreen": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "000000",
        "600": "000000",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "000000",
        "A400": "000000",
        "A700": "000000",
    },
    "Lime": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "000000",
        "600": "000000",
        "700": "000000",
        "800": "000000",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "000000",
        "A400": "000000",
        "A700": "000000",
    },
    "Yellow": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "000000",
        "600": "000000",
        "700": "000000",
        "800": "000000",
        "900": "000000",
        "A100": "000000",
        "A200": "000000",
        "A400": "000000",
        "A700": "000000",
    },
    "Amber": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "000000",
        "600": "000000",
        "700": "000000",
        "800": "000000",
        "900": "000000",
        "A100": "000000",
        "A200": "000000",
        "A400": "000000",
        "A700": "000000",
    },
    "Orange": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "000000",
        "600": "000000",
        "700": "000000",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "000000",
        "A400": "000000",
        "A700": "000000",
    },
    "DeepOrange": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "FFFFFF",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "000000",
        "A200": "000000",
        "A400": "FFFFFF",
        "A700": "FFFFFF",
    },
    "Brown": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "FFFFFF",
        "400": "FFFFFF",
        "500": "FFFFFF",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "FFFFFF",
        "A200": "FFFFFF",
        "A400": "FFFFFF",
        "A700": "FFFFFF",
    },
    "Gray": {
        "50": "FFFFFF",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "000000",
        "500": "000000",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "FFFFFF",
        "A200": "FFFFFF",
        "A400": "FFFFFF",
        "A700": "FFFFFF",
    },
    "BlueGray": {
        "50": "000000",
        "100": "000000",
        "200": "000000",
        "300": "000000",
        "400": "FFFFFF",
        "500": "FFFFFF",
        "600": "FFFFFF",
        "700": "FFFFFF",
        "800": "FFFFFF",
        "900": "FFFFFF",
        "A100": "FFFFFF",
        "A200": "FFFFFF",
        "A400": "FFFFFF",
        "A700": "FFFFFF",
    },
}
hex_colormap = {
    "aliceblue": "#f0f8ff",
    "antiquewhite": "#faebd7",
    "aqua": "#00ffff",
    "aquamarine": "#7fffd4",
    "azure": "#f0ffff",
    "beige": "#f5f5dc",
    "bisque": "#ffe4c4",
    "black": "#000000",
    "blanchedalmond": "#ffebcd",
    "blue": "#0000ff",
    "blueviolet": "#8a2be2",
    "brown": "#a52a2a",
    "burlywood": "#deb887",
    "cadetblue": "#5f9ea0",
    "chartreuse": "#7fff00",
    "chocolate": "#d2691e",
    "coral": "#ff7f50",
    "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc",
    "crimson": "#dc143c",
    "cyan": "#00ffff",
    "darkblue": "#00008b",
    "darkcyan": "#008b8b",
    "darkgoldenrod": "#b8860b",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "darkgreen": "#006400",
    "darkkhaki": "#bdb76b",
    "darkmagenta": "#8b008b",
    "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00",
    "darkorchid": "#9932cc",
    "darkred": "#8b0000",
    "darksalmon": "#e9967a",
    "darkseagreen": "#8fbc8f",
    "darkslateblue": "#483d8b",
    "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f",
    "darkturquoise": "#00ced1",
    "darkviolet": "#9400d3",
    "deeppink": "#ff1493",
    "deepskyblue": "#00bfff",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "dodgerblue": "#1e90ff",
    "firebrick": "#b22222",
    "floralwhite": "#fffaf0",
    "forestgreen": "#228b22",
    "fuchsia": "#ff00ff",
    "gainsboro": "#dcdcdc",
    "ghostwhite": "#f8f8ff",
    "gold": "#ffd700",
    "goldenrod": "#daa520",
    "gray": "#808080",
    "grey": "#808080",
    "green": "#008000",
    "greenyellow": "#adff2f",
    "honeydew": "#f0fff0",
    "hotpink": "#ff69b4",
    "indianred": "#cd5c5c",
    "indigo": "#4b0082",
    "ivory": "#fffff0",
    "khaki": "#f0e68c",
    "lavender": "#e6e6fa",
    "lavenderblush": "#fff0f5",
    "lawngreen": "#7cfc00",
    "lemonchiffon": "#fffacd",
    "lightblue": "#add8e6",
    "lightcoral": "#f08080",
    "lightcyan": "#e0ffff",
    "lightgoldenrodyellow": "#fafad2",
    "lightgreen": "#90ee90",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "lightpink": "#ffb6c1",
    "lightsalmon": "#ffa07a",
    "lightseagreen": "#20b2aa",
    "lightskyblue": "#87cefa",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "lightsteelblue": "#b0c4de",
    "lightyellow": "#ffffe0",
    "lime": "#00ff00",
    "limegreen": "#32cd32",
    "linen": "#faf0e6",
    "magenta": "#ff00ff",
    "maroon": "#800000",
    "mediumaquamarine": "#66cdaa",
    "mediumblue": "#0000cd",
    "mediumorchid": "#ba55d3",
    "mediumpurple": "#9370db",
    "mediumseagreen": "#3cb371",
    "mediumslateblue": "#7b68ee",
    "mediumspringgreen": "#00fa9a",
    "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585",
    "midnightblue": "#191970",
    "mintcream": "#f5fffa",
    "mistyrose": "#ffe4e1",
    "moccasin": "#ffe4b5",
    "navajowhite": "#ffdead",
    "navy": "#000080",
    "oldlace": "#fdf5e6",
    "olive": "#808000",
    "olivedrab": "#6b8e23",
    "orange": "#ffa500",
    "orangered": "#ff4500",
    "orchid": "#da70d6",
    "palegoldenrod": "#eee8aa",
    "palegreen": "#98fb98",
    "paleturquoise": "#afeeee",
    "palevioletred": "#db7093",
    "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9",
    "peru": "#cd853f",
    "pink": "#ffc0cb",
    "plum": "#dda0dd",
    "powderblue": "#b0e0e6",
    "purple": "#800080",
    "red": "#ff0000",
    "rosybrown": "#bc8f8f",
    "royalblue": "#4169e1",
    "saddlebrown": "#8b4513",
    "salmon": "#fa8072",
    "sandybrown": "#f4a460",
    "seagreen": "#2e8b57",
    "seashell": "#fff5ee",
    "sienna": "#a0522d",
    "silver": "#c0c0c0",
    "skyblue": "#87ceeb",
    "slateblue": "#6a5acd",
    "slategray": "#708090",
    "slategrey": "#708090",
    "snow": "#fffafa",
    "springgreen": "#00ff7f",
    "steelblue": "#4682b4",
    "tan": "#d2b48c",
    "teal": "#008080",
    "thistle": "#d8bfd8",
    "tomato": "#ff6347",
    "turquoise": "#40e0d0",
    "violet": "#ee82ee",
    "wheat": "#f5deb3",
    "white": "#ffffff",
    "whitesmoke": "#f5f5f5",
    "yellow": "#ffff00",
    "yellowgreen": "#9acd32",
}
theme_text_color_options = (
    "Primary",
    "Secondary",
    "Hint",
    "Error",
    "Custom",
    "ContrastParentBackground",
)


class BaseButtonLegacy(
    DeclarativeBehavior,
    RectangularRippleBehavior,
    ThemableBehavior,
    ButtonBehavior,
    AnchorLayout,
):
    """
    mvckivy class for all buttons.

    For more information, see in the
    :class:`~kivymd.uix.behaviors.DeclarativeBehavior` and
    :class:`~kivymd.uix.behaviors.RectangularRippleBehavior` and
    :class:`~kivymd.theming.ThemableBehavior` and
    :class:`~kivy.uix.behaviors.ButtonBehavior` and
    :class:`~kivy.uix.anchorlayout.AnchorLayout`
    classes documentation.
    """

    padding = VariableListProperty([dp(16), dp(8), dp(16), dp(8)])
    """
    Padding between the widget box and its children, in pixels:
    [padding_left, padding_top, padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].

    .. versionadded:: 1.0.0

    :attr:`padding` is a :class:`~kivy.properties.VariableListProperty`
    and defaults to [16dp, 8dp, 16dp, 8dp].
    """

    halign = OptionProperty("center", options=("left", "center", "right"))
    """
    Horizontal anchor.

    .. versionadded:: 1.0.0

    :attr:`anchor_x` is an :class:`~kivy.properties.OptionProperty`
    and defaults to 'center'. It accepts values of 'left', 'center' or 'right'.
    """

    valign = OptionProperty("center", options=("top", "center", "bottom"))
    """
    Vertical anchor.

    .. versionadded:: 1.0.0

    :attr:`anchor_y` is an :class:`~kivy.properties.OptionProperty`
    and defaults to 'center'. It accepts values of 'top', 'center' or 'bottom'.
    """

    text = StringProperty("")
    """
    Button text.

    :attr:`text` is a :class:`~kivy.properties.StringProperty`
    and defaults to `''`.
    """

    icon = StringProperty("")
    """
    Button icon.

    :attr:`icon` is a :class:`~kivy.properties.StringProperty`
    and defaults to `''`.
    """

    font_style = OptionProperty("Body1", options=theme_font_styles)
    """
    Button text font style.

    Available vanilla font_style are: `'H1'`, `'H2'`, `'H3'`, `'H4'`, `'H5'`,
    `'H6'`, `'Subtitle1'`, `'Subtitle2'`, `'Body1'`, `'Body2'`, `'Button'`,
    `'Caption'`, `'Overline'`, `'Icon'`.

    :attr:`font_style` is a :class:`~kivy.properties.StringProperty`
    and defaults to `'Body1'`.
    """

    theme_text_color = OptionProperty(None, options=theme_text_color_options)
    """
    Button text type. Available options are: (`"Primary"`, `"Secondary"`,
    `"Hint"`, `"Error"`, `"Custom"`, `"ContrastParentBackground"`).

    :attr:`theme_text_color` is an :class:`~kivy.properties.OptionProperty`
    and defaults to `None` (set by button class).
    """

    theme_icon_color = OptionProperty(None, options=theme_text_color_options)
    """
    Button icon type. Available options are: (`"Primary"`, `"Secondary"`,
    `"Hint"`, `"Error"`, `"Custom"`, `"ContrastParentBackground"`).

    .. versionadded:: 1.0.0

    :attr:`theme_icon_color` is an :class:`~kivy.properties.OptionProperty`
    and defaults to `None` (set by button subclass).
    """

    text_color = ColorProperty(None)
    """
    Button text color in (r, g, b, a) or string format.

    :attr:`text_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    icon_color = ColorProperty(None)
    """
    Button icon color in (r, g, b, a) or string format.

    :attr:`icon_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    font_name = StringProperty()
    """
    Button text font name.

    :attr:`font_name` is a :class:`~kivy.properties.StringProperty`
    and defaults to `''`.
    """

    font_size = NumericProperty("14sp")
    """
    Button text font size.

    :attr:`font_size` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `14sp`.
    """

    icon_size = NumericProperty()
    """
    Icon font size.
    Use this parameter as the font size, that is, in sp units.

    .. versionadded:: 1.0.0

    :attr:`icon_size` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `None`.
    """

    line_width = NumericProperty(1)
    """
    Line width for button border.

    :attr:`line_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `1`.
    """

    line_color = ColorProperty(None)
    """
    Line color in (r, g, b, a) or string format for button border.

    :attr:`line_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    line_color_disabled = ColorProperty(None)
    """
    Disabled line color in (r, g, b, a) or string format for button border.

    .. versionadded:: 1.0.0

    :attr:`line_color_disabled` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    md_bg_color = ColorProperty(None)
    """
    Button background color in (r, g, b, a) or string format.

    :attr:`md_bg_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    md_bg_color_disabled = ColorProperty(None)
    """
    The background color in (r, g, b, a) or string format of the button when
    the button is disabled.

    :attr:`md_bg_color_disabled` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    disabled_color = ColorProperty(None)
    """
    The color of the text and icon when the button is disabled,
    in (r, g, b, a) or string format.

    .. versionadded:: 1.0.0

    :attr:`disabled_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    rounded_button = BooleanProperty(False)
    """
    Should the button have fully rounded corners (e.g. like M3 buttons)?

    .. versionadded:: 1.0.0

    :attr:`rounded_button` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    # Note - _radius must be > 0 to avoid rendering issues.
    _radius = BoundedNumericProperty(dp(4), min=0.0999, errorvalue=0.1)
    # Properties used for rendering.
    _disabled_color = ColorProperty([0.0, 0.0, 0.0, 0.0])
    _md_bg_color = ColorProperty([0.0, 0.0, 0.0, 0.0])
    _md_bg_color_disabled = ColorProperty([0.0, 0.0, 0.0, 0.0])
    _line_color = ColorProperty([0.0, 0.0, 0.0, 0.0])
    _line_color_disabled = ColorProperty([0.0, 0.0, 0.0, 0.0])
    _theme_text_color = OptionProperty(None, options=theme_text_color_options)
    _theme_icon_color = OptionProperty(None, options=theme_text_color_options)
    _text_color = ColorProperty(None)
    _icon_color = ColorProperty(None)

    # Defaults which can be overridden in subclasses
    _min_width = NumericProperty(dp(64))
    _min_height = NumericProperty(dp(36))

    # Default colors - set to None to use primary theme colors
    _default_md_bg_color = [0.0, 0.0, 0.0, 0.0]
    _default_md_bg_color_disabled = [0.0, 0.0, 0.0, 0.0]
    _default_line_color = [0.0, 0.0, 0.0, 0.0]
    _default_line_color_disabled = [0.0, 0.0, 0.0, 0.0]
    _default_theme_text_color = StringProperty("Primary")
    _default_theme_icon_color = StringProperty("Primary")
    _default_text_color = ColorProperty(None)
    _default_icon_color = ColorProperty(None)

    _animation_fade_bg = ObjectProperty(None, allownone=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.theme_cls.bind(
            primary_palette=self.set_all_colors,
            theme_style=self.set_all_colors,
        )
        self.bind(
            md_bg_color=self.set_button_colors,
            md_bg_color_disabled=self.set_button_colors,
            line_color=self.set_button_colors,
            line_color_disabled=self.set_button_colors,
            theme_text_color=self.set_text_color,
            text_color=self.set_text_color,
            theme_icon_color=self.set_icon_color,
            icon_color=self.set_icon_color,
            disabled_color=self.set_disabled_color,
            rounded_button=self.set_radius,
            height=self.set_radius,
        )
        Clock.schedule_once(self.set_all_colors)
        Clock.schedule_once(self.set_radius)

    def set_disabled_color(self, *args):
        """
        Sets the color for the icon, text and line of the button when button
        is disabled.
        """

        if self.disabled:
            disabled_color = (
                self.disabled_color
                if self.disabled_color
                else self.theme_cls.disabled_hint_text_color
            )
            self._disabled_color = disabled_color
            # Button icon color.
            if "lbl_ic" in self.ids:
                self.ids.lbl_ic.disabled_color = disabled_color
            # Button text color.
            if "lbl_txt" in self.ids:
                self.ids.lbl_txt.disabled_color = disabled_color
        else:
            self._disabled_color = self._line_color

    def set_all_colors(self, *args) -> None:
        """Set all button colours."""

        self.set_button_colors()
        self.set_text_color()
        self.set_icon_color()

    def set_button_colors(self, *args) -> None:
        """Set all button colours (except text/icons)."""

        # Set main color
        _md_bg_color = (
            self.md_bg_color or self._default_md_bg_color or self.theme_cls.primaryColor
        )

        # Set disabled color
        _md_bg_color_disabled = (
            self.md_bg_color_disabled
            or (
                [sum(self.md_bg_color[0:3]) / 3.0] * 3
                + [0.38 if self.theme_cls.theme_style == "Light" else 0.5]
                if self.md_bg_color
                else None
            )
            or self._default_md_bg_color_disabled
            or self.theme_cls.inversePrimaryColor
        )

        # Set line color
        _line_color = (
            self.line_color or self._default_line_color or self.theme_cls.primaryColor
        )

        # Set disabled line color
        _line_color_disabled = (
            self.line_color_disabled
            or (
                [sum(self.line_color[0:3]) / 3.0] * 3
                + [0.38 if self.theme_cls.theme_style == "Light" else 0.5]
                if self.line_color
                else None
            )
            or self._default_line_color_disabled
            or self.theme_cls.inversePrimaryColor
        )

        if self.theme_cls.theme_style_switch_animation:
            Animation(
                _md_bg_color=_md_bg_color,
                _md_bg_color_disabled=_md_bg_color_disabled,
                _line_color=_line_color,
                _line_color_disabled=_line_color_disabled,
                d=self.theme_cls.theme_style_switch_animation_duration,
                t="linear",
            ).start(self)
        else:
            self._md_bg_color = _md_bg_color
            self._md_bg_color_disabled = _md_bg_color_disabled
        self._line_color = _line_color
        self._line_color_disabled = _line_color_disabled

    def set_text_color(self, *args) -> None:
        """
        Set _theme_text_color and _text_color based on defaults and options.
        """

        self._theme_text_color = self.theme_text_color or self._default_theme_text_color
        if self._default_text_color == "PrimaryHue":
            default_text_color = hex_colormap[self.theme_cls.primary_palette.lower()]
        elif self._default_text_color == "Primary":
            default_text_color = self.theme_cls.onPrimaryColor
        else:
            default_text_color = self.theme_cls.onPrimaryColor
        self._text_color = self.text_color or default_text_color

    def set_icon_color(self, *args) -> None:
        """
        Set _theme_icon_color and _icon_color based on defaults and options.
        """

        self._theme_icon_color = (
            (self.theme_icon_color or self._default_theme_icon_color)
            if not self.disabled
            else "Custom"
        )
        if self._default_icon_color == "PrimaryHue":
            # default_icon_color = self.theme_cls.onPrimaryColor
            default_icon_color = hex_colormap[self.theme_cls.primary_palette.lower()]
        elif self._default_icon_color == "Primary":
            default_icon_color = self.theme_cls.onPrimaryColor
        else:
            default_icon_color = self.theme_cls.onPrimaryColor
        self._icon_color = self.icon_color or default_icon_color

    def set_radius(self, *args) -> None:
        """
        Set the radius, if we are a rounded button, based on the
        current height.
        """

        if self.rounded_button:
            self._radius = self.height / 2

    # Touch events that cause transparent buttons to fade to background
    def on_touch_down(self, touch):
        """
        Animates fade to background on press, for buttons with no
        background color.
        """

        if touch.is_mouse_scrolling:
            return False
        elif not self.collide_point(touch.x, touch.y):
            return False
        elif self in touch.ud:
            return False
        elif self.disabled:
            return False
        else:
            if self._md_bg_color[3] == 0.0:
                self._animation_fade_bg = Animation(
                    duration=0.5, _md_bg_color=[0.0, 0.0, 0.0, 0.1]
                )
                self._animation_fade_bg.start(self)
            return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        """Animates return to original background on touch release."""

        if not self.disabled and self._animation_fade_bg:
            self._animation_fade_bg.stop_property(self, "_md_bg_color")
            self._animation_fade_bg = None
            md_bg_color = (
                self.md_bg_color
                or self._default_md_bg_color
                or self.theme_cls.primaryColor
            )
            Animation(duration=0.05, _md_bg_color=md_bg_color).start(self)
        return super().on_touch_up(touch)

    def on_disabled(self, instance_button, disabled_value: bool) -> None:
        if hasattr(super(), "on_disabled"):
            if self.disabled is True:
                Animation.cancel_all(self, "elevation")
            super().on_disabled(instance_button, disabled_value)
        Clock.schedule_once(self.set_disabled_color)


class OldButtonIconMixin:
    """Backwards-compatibility for icons."""

    icon = StringProperty("android")

    def on_icon_color(self, instance_button, color: list) -> None:
        """
        If we are setting an icon color, set theme_icon_color to Custom.
        For backwards compatibility (before theme_icon_color existed).
        """

        if color and (self.theme_text_color == "Custom"):
            self.theme_icon_color = "Custom"


class ButtonElevationBehaviour(CommonElevationBehavior):
    """
    Implements elevation behavior as well as the recommended down/disabled
    colors for raised buttons.

    The minimum elevation for any raised button is `'1dp'`,
    by default, set to `'2dp'`.

    The `_elevation_raised` is automatically computed and is set to
    `self.elevation + 6` each time `self.elevation` is updated.
    """

    _elevation_raised = NumericProperty()
    _anim_raised = ObjectProperty(None, allownone=True)
    _default_elevation = 2

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.elevation == 0:
            self.elevation = self._default_elevation
        if hasattr(self, "radius"):
            self.bind(_radius=self.setter("radius"))
        Clock.schedule_once(self.create_anim_raised)
        self.on_disabled(self, self.disabled)

    def create_anim_raised(self, *args) -> None:
        if self.elevation:
            self._elevation_raised = self.elevation
            self._anim_raised = Animation(elevation=self.elevation + 1, d=0.15)

    def on_touch_down(self, touch):
        if not self.disabled:
            if touch.is_mouse_scrolling:
                return False
            if not self.collide_point(touch.x, touch.y):
                return False
            if self in touch.ud:
                return False
            if self._anim_raised and self.elevation:
                self._anim_raised.start(self)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if not self.disabled:
            if self in touch.ud:
                self.stop_elevation_anim()
                return super().on_touch_up(touch)
        return super().on_touch_up(touch)

    def stop_elevation_anim(self):
        Animation.cancel_all(self, "elevation")
        if self._anim_raised and self.elevation:
            self.elevation = self._elevation_raised


class ButtonContentsIconLegacy:
    """
    Contents for a round BaseButton consisting of an :class:`~MDIcon` class.
    """

    _min_width = NumericProperty(0)

    def on_text_color(self, instance_button, color: list) -> None:
        """
        Set icon_color equal to text_color.
        For backwards compatibility - can use text_color instead
        of icon_color.
        """

        if color:
            self.icon_color = color


class MDFloatingActionButton(
    BaseButtonLegacy,
    OldButtonIconMixin,
    ButtonElevationBehaviour,
    ButtonContentsIconLegacy,
):
    """
    Implementation
    `FAB <https://m3.material.io/components/floating-action-button/overview>`_
    button.

    For more information, see in the
    :class:`~BaseButton` and
    :class:`~OldButtonIconMixin` and
    :class:`~ButtonElevationBehaviour` and
    :class:`~ButtonContentsIcon` classes documentation.
    """

    type = OptionProperty("standard", options=["small", "large", "standard"])
    """
    Type of M3 button.

    .. versionadded:: 1.0.0

    Available options are: 'small', 'large', 'standard'.

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/md-floating-action-button-types.png
        :align: center

    :attr:`type` is an :class:`~kivy.properties.OptionProperty`
    and defaults to `'standard'`.
    """

    _default_md_bg_color = None
    _default_md_bg_color_disabled = None
    _default_theme_icon_color = "Custom"
    _default_icon_color = "PrimaryHue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FIXME: GraphicException: Invalid width value, must be > 0
        self.line_width = 0.001
        Clock.schedule_once(self.set_size)
        Clock.schedule_once(self.set__radius)
        Clock.schedule_once(self.set_font_size)

    def set_font_size(self, *args) -> None:
        if self.type == "large":
            self.icon_size = "36sp"
        else:
            self.icon_size = 0

    def set__radius(self, *args) -> None:
        self.shadow_softness = FLOATING_ACTION_BUTTON_M3_SOFTNESS
        self.shadow_offset = FLOATING_ACTION_BUTTON_M3_OFFSET
        self.elevation = FLOATING_ACTION_BUTTON_M3_ELEVATION
        self.rounded_button = False

        if self.type == "small":
            self._radius = dp(12)
        elif self.type == "standard":
            self._radius = dp(16)
        elif self.type == "large":
            self._radius = dp(28)

        self.shadow_radius = self._radius

    def set_size_and_radius(self, *args) -> None:
        self.set_size(args)
        self.set__radius(args)

    def set_size(self, *args) -> None:
        if self.type == "small":
            self.size = dp(40), dp(40)
        elif self.type == "standard":
            self.size = dp(56), dp(56)
        elif self.type == "large":
            self.size = dp(96), dp(96)

    def on_type(self, instance_md_floating_action_button, type: str) -> None:
        self.set_size()
        self.set_font_size()


class BaseFloatingBottomButtonLegacy(MDFloatingActionButton, MDTooltip):
    _canvas_width = NumericProperty(0)
    _padding_right = NumericProperty(0)
    _bg_color = ColorProperty(None)

    def set_size(self, interval: Union[int, float]) -> None:
        self.width = "46dp"
        self.height = "46dp"


class MDFloatingBottomButton(BaseFloatingBottomButtonLegacy):
    _bg_color = ColorProperty(None)


class MDFloatingRootButtonLegacy(RotateBehavior, MDFloatingActionButton):
    rotate_value_angle = NumericProperty(0)


class MDFloatingLabelLegacy(MDLabel):
    bg_color = ColorProperty([0, 0, 0, 0])


class FixedMDFloatingBottomButton(ButtonHoverBehavior, MDFloatingBottomButton):
    def set_size(self, interval: Union[int, float]) -> None:
        """Calls only once (on init)"""
        self.height = "48dp"
        self.width = "48dp"


class MVCSpeedDial(MVCFloatLayout):
    """
    For more information, see in the
    :class:`~kivy.uix.floatlayout.FloatLayout` class documentation.

    For more information, see in the
    :class:`~kivymd.uix.behaviors.DeclarativeBehavior` and
    :class:`~kivymd.theming.ThemableBehavior` and
    :class:`~kivy.uix.floatlayout.FloatLayout`
    lasses documentation.

    :Events:
        :attr:`on_open`
            Called when a stack is opened.
        :attr:`on_close`
            Called when a stack is closed.
        :attr:`on_press_stack_button`
            Called at the on_press event for the stack button.
        :attr:`on_release_stack_button`
            Called at the on_press event for the stack button.
    """

    icon = StringProperty("plus")
    """
    Root button icon name.

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            icon: "pencil"

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-icon.png
        :align: center

    :attr:`icon` is a :class:`~kivy.properties.StringProperty`
    and defaults to `'plus'`.
    """

    anchor = OptionProperty("right", option=["right"])
    """
    Stack anchor. Available options are: `'right'`.

    :attr:`anchor` is a :class:`~kivy.properties.OptionProperty`
    and defaults to `'right'`.
    """

    label_text_color = ColorProperty(None)
    """
    Color of floating text labels in (r, g, b, a) or string format.

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            label_text_color: "orange"

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-label-text-color.png
        :align: center

    :attr:`label_text_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    label_bg_color = ColorProperty([0, 0, 0, 0])
    """
    Background color of floating text labels in (r, g, b, a) or string format.

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            label_text_color: "black"
            label_bg_color: "orange"

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-label-bg-color.png
        :align: center

    :attr:`label_bg_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `[0, 0, 0, 0]`.
    """

    label_radius = VariableListProperty([0], length=4)
    """
    The radius of the background of floating text labels.

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            label_text_color: "black"
            label_bg_color: "orange"

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-label-radius.png
        :align: center

    :attr:`label_radius` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `[0, 0, 0, 0]`.
    """

    data = DictProperty()
    """
    Must be a dictionary.

    .. code-block:: python

        {
            'name-icon': 'Text label',
            ...,
            ...,
        }
    """

    right_pad = BooleanProperty(False)
    """
    If `True`, the background for the floating text label will increase by the
    number of pixels specified in the :attr:`~right_pad_value` parameter.

    Works only if the :attr:`~hint_animation` parameter is set to `True`.

    .. rubric:: False

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            hint_animation: True
            right_pad: False

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-right-pad.gif
        :align: center

    .. rubric:: True

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            hint_animation: True
            right_pad: True
            right_pad_value: "10dp"

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-right-pad-true.gif
        :align: center

    :attr:`right_pad` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    right_pad_value = NumericProperty(0)
    """
    See :attr:`~right_pad` parameter for more information.

    :attr:`right_pad_value` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `0`.
    """

    root_button_anim = BooleanProperty(False)
    """
    If ``True`` then the root button will rotate 45 degrees when the stack
    is opened.

    :attr:`root_button_anim` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    opening_transition = StringProperty("out_cubic")
    """
    The name of the stack opening animation type.

    :attr:`opening_transition` is a :class:`~kivy.properties.StringProperty`
    and defaults to `'out_cubic'`.
    """

    closing_transition = StringProperty("out_cubic")
    """
    The name of the stack closing animation type.

    :attr:`closing_transition` is a :class:`~kivy.properties.StringProperty`
    and defaults to `'out_cubic'`.
    """

    opening_transition_button_rotation = StringProperty("out_cubic")
    """
    The name of the animation type to rotate the root button when opening the
    stack.

    :attr:`opening_transition_button_rotation` is a :class:`~kivy.properties.StringProperty`
    and defaults to `'out_cubic'`.
    """

    closing_transition_button_rotation = StringProperty("out_cubic")
    """
    The name of the animation type to rotate the root button when closing the
    stack.

    :attr:`closing_transition_button_rotation` is a :class:`~kivy.properties.StringProperty`
    and defaults to `'out_cubic'`.
    """

    opening_time = NumericProperty(0.5)
    """
    Time required for the stack to go to: attr:`state` `'open'`.

    :attr:`opening_time` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `0.2`.
    """

    closing_time = NumericProperty(0.2)
    """
    Time required for the stack to go to: attr:`state` `'close'`.

    :attr:`closing_time` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `0.2`.
    """

    opening_time_button_rotation = NumericProperty(0.2)
    """
    Time required to rotate the root button 45 degrees during the stack
    opening animation.

    :attr:`opening_time_button_rotation` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `0.2`.
    """

    closing_time_button_rotation = NumericProperty(0.2)
    """
    Time required to rotate the root button 0 degrees during the stack
    closing animation.

    :attr:`closing_time_button_rotation` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `0.2`.
    """

    state = OptionProperty("close", options=("close", "open"))
    """
    Indicates whether the stack is closed or open.
    Available options are: `'close'`, `'open'`.

    :attr:`state` is a :class:`~kivy.properties.OptionProperty`
    and defaults to `'close'`.
    """

    bg_color_root_button = ColorProperty(None)
    """
    Background color of root button in (r, g, b, a) or string format.

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            bg_color_root_button: "red"

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-bg-color-root-button.png
        :align: center

    :attr:`bg_color_root_button` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    bg_color_stack_button = ColorProperty(None)
    """
    Background color of the stack buttons in (r, g, b, a) or string format.

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            bg_color_root_button: "red"
            bg_color_stack_button: "red"

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-bg-color-stack-button.png
        :align: center

    :attr:`bg_color_stack_button` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    color_icon_stack_button = ColorProperty(None)
    """
    The color icon of the stack buttons in (r, g, b, a) or string format.

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            bg_color_root_button: "red"
            bg_color_stack_button: "red"
            color_icon_stack_button: "white"

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-color-icon-stack-button.png
        :align: center

    :attr:`color_icon_stack_button` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    color_icon_root_button = ColorProperty(None)
    """
    The color icon of the root button in (r, g, b, a) or string format.

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            bg_color_root_button: "red"
            bg_color_stack_button: "red"
            color_icon_stack_button: "white"
            color_icon_root_button: self.color_icon_stack_button

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-color-icon-root-button.png
        :align: center

    :attr:`color_icon_root_button` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    bg_hint_color = ColorProperty(None)
    """
    Background color for the floating text of the buttons in (r, g, b, a)
    or string format.

    .. code-block:: kv

        MDFloatingActionButtonSpeedDial:
            bg_hint_color: "red"
            hint_animation: True

    .. image:: https://github.com/HeaTTheatR/KivyMD-data/raw/master/gallery/kivymddoc/MDFloatingActionButtonSpeedDial-bg-hint-color.png
        :align: center

    :attr:`bg_hint_color` is a :class:`~kivy.properties.ColorProperty`
    and defaults to `None`.
    """

    hint_animation = BooleanProperty(False)
    """
    Whether to use button extension animation to display floating text.

    :attr:`hint_animation` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    stack_buttons = DictProperty()

    _label_pos_y_set = False
    _anim_buttons_data = {}
    _anim_labels_data = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_open")
        self.register_event_type("on_close")
        self.register_event_type("on_press_stack_button")
        self.register_event_type("on_release_stack_button")
        Window.bind(on_resize=self._update_pos_buttons)

    def on_open(self, *args):
        """Called when a stack is opened."""

    def on_close(self, *args):
        """Called when a stack is closed."""

    def on_leave(self, instance_button: MDFloatingBottomButton) -> None:
        """Called when the mouse cursor goes outside the button of stack."""

        if self.state == "open":
            for widget in self.children:
                if isinstance(widget, MDFloatingLabelLegacy) and self.hint_animation:
                    Animation.cancel_all(widget)
                    for item in self.data.items():
                        if widget.text in item:
                            Animation(
                                _canvas_width=0,
                                _padding_right=0,
                                d=self.opening_time,
                                t=self.opening_transition,
                                _elevation=0,
                            ).start(instance_button)
                            Animation(
                                opacity=0, d=0.1, t=self.opening_transition
                            ).start(widget)

    def on_enter(self, instance_button: MDFloatingBottomButton) -> None:
        """Called when the mouse cursor is over a button from the stack."""

        if self.state == "open":
            for widget in self.children:
                if isinstance(widget, MDFloatingLabelLegacy) and self.hint_animation:
                    Animation.cancel_all(widget)
                    for item in self.data.items():
                        if widget.text in item:
                            Animation(
                                _canvas_width=widget.width + dp(24),
                                _padding_right=(
                                    self.right_pad_value if self.right_pad else 0
                                ),
                                d=self.opening_time,
                                t=self.opening_transition,
                            ).start(instance_button)
                            if (
                                instance_button.icon == self.data[f"{widget.text}"]
                                or instance_button.icon
                                == self.data[f"{widget.text}"][0]
                            ):
                                Animation(
                                    opacity=1,
                                    d=self.opening_time,
                                    t=self.opening_transition,
                                ).start(widget)
                            else:
                                Animation(
                                    opacity=0, d=0.1, t=self.opening_transition
                                ).start(widget)

        Window.set_system_cursor("hand")

    def on_icon(self, instance_speed_dial, name_icon: str) -> None:
        self._set_button_property(MDFloatingRootButtonLegacy, "icon", name_icon)

    def on_label_text_color(self, instance_speed_dial, color: list | str) -> None:
        for widget in self.children:
            if isinstance(widget, MDFloatingLabelLegacy):
                widget.text_color = color

    def on_color_icon_stack_button(self, instance_speed_dial, color: list) -> None:
        self._set_button_property(MDFloatingBottomButton, "icon_color", color)

    def on_hint_animation(self, instance_speed_dial, value: bool) -> None:
        for widget in self.children:
            if isinstance(widget, MDFloatingLabelLegacy):
                widget.md_bg_color = (0, 0, 0, 0)

    def on_bg_hint_color(self, instance_speed_dial, color: list) -> None:
        setattr(MDFloatingBottomButton, "_bg_color", color)

    def on_color_icon_root_button(self, instance_speed_dial, color: list) -> None:
        self._set_button_property(MDFloatingRootButtonLegacy, "icon_color", color)

    def on_bg_color_stack_button(self, instance_speed_dial, color: list) -> None:
        self._set_button_property(MDFloatingBottomButton, "md_bg_color", color)

    def on_bg_color_root_button(self, instance_speed_dial, color: list) -> None:
        self._set_button_property(MDFloatingRootButtonLegacy, "md_bg_color", color)

    def on_press_stack_button(self, *args) -> None:
        """
        Called at the on_press event for the stack button.

        .. code-block:: kv

            MDFloatingActionButtonSpeedDial:
                on_press_stack_button: print(*args)

        .. versionadded:: 1.1.0
        """

    def on_release_stack_button(self, *args) -> None:
        """
        Called at the on_release event for the stack button.

        .. code-block:: kv

            MDFloatingActionButtonSpeedDial:
                on_release_stack_button: print(*args)

        .. versionadded:: 1.1.0
        """
        Window.set_system_cursor("arrow")
        self.close_stack()

    def set_pos_labels(self, instance_floating_label: MDFloatingLabelLegacy) -> None:
        """
        Sets the position of the floating labels.
        Called when the application's root window is resized.
        """

        if self.anchor == "right":
            instance_floating_label.x = (
                Window.width - instance_floating_label.width - dp(86)
            )

    def set_pos_root_button(
        self, instance_floating_root_button: MDFloatingRootButtonLegacy
    ) -> None:
        """
        Sets the position of the root button.
        Called when the application's root window is resized.
        """

        def set_pos_root_button(*args):
            if self.anchor == "right":
                instance_floating_root_button.y = dp(20)
                instance_floating_root_button.x = self.parent.width - (dp(56) + dp(20))

        Clock.schedule_once(set_pos_root_button)

    def set_pos_bottom_buttons(
        self, instance_floating_bottom_button: MDFloatingBottomButton
    ) -> None:
        """
        Sets the position of the bottom buttons in a stack.
        Called when the application's root window is resized.
        """

        if self.anchor == "right":
            if self.state != "open":
                instance_floating_bottom_button.y = (
                    instance_floating_bottom_button.height / 2
                )

            instance_floating_bottom_button.x = Window.width - (
                instance_floating_bottom_button.height
                + instance_floating_bottom_button.width / 2
            )

    def do_animation_open_stack(self, anim_data: dict) -> None:
        """
        :param anim_data:
            {
                <kivymd.uix.button.MDFloatingBottomButton object>:
                    <kivy.animation.Animation>,
                <kivymd.uix.button.MDFloatingBottomButton object>:
                    <kivy.animation.Animation object>,
                ...,
            }
        """

        def on_progress(animation, widget, value):
            if value >= 0.1:
                animation_open_stack()

        def animation_open_stack(*args):
            try:
                widget = next(widgets_list)
                animation = anim_data[widget]
                animation.bind(on_progress=on_progress)
                animation.start(widget)
            except StopIteration:
                pass

        widgets_list = iter(list(anim_data.keys()))
        animation_open_stack()

    def close_stack(self):
        """Closes the button stack."""

        for widget in self.children:
            if isinstance(widget, MDFloatingBottomButton):
                Animation(
                    y=widget.height / 2,
                    d=self.closing_time,
                    t=self.closing_transition,
                    opacity=0,
                ).start(widget)
            elif isinstance(widget, MDFloatingLabelLegacy):
                if widget.opacity > 0:
                    Animation(opacity=0, d=0.1).start(widget)
            elif (
                isinstance(widget, MDFloatingRootButtonLegacy) and self.root_button_anim
            ):
                Animation(
                    rotate_value_angle=0,
                    shadow_softness=FLOATING_ACTION_BUTTON_M3_SOFTNESS,
                    d=self.closing_time_button_rotation,
                    t=self.closing_transition_button_rotation,
                ).start(widget)

        self.state = "close"
        self.dispatch("on_close")

    def _update_pos_buttons(self, instance, width, height):
        # Updates button positions when resizing screen.
        for widget in self.children:
            if isinstance(widget, MDFloatingBottomButton):
                self.set_pos_bottom_buttons(widget)
            elif isinstance(widget, MDFloatingRootButtonLegacy):
                self.set_pos_root_button(widget)
            elif isinstance(widget, MDFloatingLabelLegacy):
                self.set_pos_labels(widget)

    def _set_button_property(
        self, instance, property_name: str, property_value: str | list
    ):
        def set_count_widget(*args):
            if self.children:
                for widget in self.children:
                    if isinstance(widget, instance):
                        setattr(instance, property_name, property_value)
                        Clock.unschedule(set_count_widget)
                        break

        Clock.schedule_interval(set_count_widget, 0)

    def on_stack_open(self, widget):
        pass

    def on_stack_close(self, widget):
        pass

    def open_stack(
        self, instance_floating_root_button: Optional[MDFloatingRootButtonLegacy]
    ) -> None:
        """Opens a button stack."""

        for widget in self.children:
            if isinstance(widget, MDFloatingLabelLegacy):
                Animation.cancel_all(widget)

        if self.state != "open":
            y = 0
            label_position = dp(54)
            anim_buttons_data = {}
            anim_labels_data = {}

            for widget in self.children:
                if isinstance(widget, MDFloatingBottomButton):
                    # Sets new button positions.
                    y += dp(56) if Window.height > dp(700) else dp(42)
                    widget.y = widget.y * 2 + y
                    widget.center_x = self.root_button.center_x
                    if not self._anim_buttons_data:
                        anim_buttons_data[widget] = Animation(
                            opacity=1,
                            d=self.opening_time,
                            t=self.opening_transition,
                        )
                elif isinstance(widget, MDFloatingLabelLegacy):
                    # Sets new labels positions.
                    label_position += dp(60)
                    # Sets the position of signatures only once.
                    if not self._label_pos_y_set:
                        widget.y = widget.y * 2 + label_position
                        widget.x = Window.width - widget.width - dp(86)
                    if not self._anim_labels_data:
                        anim_labels_data[widget] = Animation(
                            opacity=1, d=self.opening_time
                        )
                elif (
                    isinstance(widget, MDFloatingRootButtonLegacy)
                    and self.root_button_anim
                ):
                    # Rotates the root button 45 degrees.
                    Animation(
                        rotate_value_angle=-45,
                        shadow_softness=5,
                        d=self.opening_time_button_rotation,
                        t=self.opening_transition_button_rotation,
                    ).start(widget)

            if anim_buttons_data:
                self._anim_buttons_data = anim_buttons_data
            if anim_labels_data and not self.hint_animation:
                self._anim_labels_data = anim_labels_data

            self.state = "open"
            self.dispatch("on_open")
            self.do_animation_open_stack(self._anim_buttons_data)
            self.do_animation_open_stack(self._anim_labels_data)
            if not self._label_pos_y_set:
                self._label_pos_y_set = True

        else:
            self.close_stack()

    def on_data(self, instance_speed_dial, data: dict) -> None:
        """Creates a stack of buttons."""

        def on_data(*args):
            # Bottom buttons.
            for name, parameters in data.items():
                name_icon = parameters if (type(parameters) is str) else parameters[0]

                bottom_button = FixedMDFloatingBottomButton(
                    icon=name_icon,
                    on_enter=self.on_enter,
                    on_leave=self.on_leave,
                    opacity=0,
                )

                bottom_button.bind(
                    on_press=lambda x: self.dispatch("on_press_stack_button"),
                    on_release=lambda x: self.dispatch("on_release_stack_button"),
                )

                if "on_press" in parameters:
                    callback = parameters[parameters.index("on_press") + 1]
                    bottom_button.bind(on_press=callback)

                if "on_release" in parameters:
                    callback = parameters[parameters.index("on_release") + 1]
                    bottom_button.bind(on_release=callback)

                self.set_pos_bottom_buttons(bottom_button)
                self.add_widget(bottom_button)
                self.stack_buttons[name] = WeakProxy(bottom_button)
                # Labels.
                floating_text = name
                if floating_text:
                    label = MDFloatingLabelLegacy(text=floating_text, opacity=0)
                    label.bg_color = self.label_bg_color
                    label.radius = self.label_radius
                    label.text_color = self.theme_cls.onBackgroundColor
                    self.add_widget(label)
            # Top root button.
            self.root_button = MDFloatingRootButtonLegacy(on_release=self.open_stack)
            self.root_button.icon = self.icon
            self.set_pos_root_button(self.root_button)
            self.add_widget(self.root_button)

        self.clear_widgets()
        self.stack_buttons = {}
        self._anim_buttons_data = {}
        self._anim_labels_data = {}
        self._label_pos_y_set = False
        Clock.schedule_once(on_data)
