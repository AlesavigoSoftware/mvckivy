from __future__ import annotations

import re
from datetime import date

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
    VariableListProperty,
)
from kivy.uix.textinput import TextInput

from kivymd.font_definitions import theme_font_styles
from kivymd.theming import ThemableBehavior, ThemeManager
from kivymd.uix.behaviors import DeclarativeBehavior, BackgroundColorBehavior
from kivymd.uix.behaviors.state_layer_behavior import StateLayerBehavior
from kivymd.uix.label import MDIcon, MDLabel


class AutoFormatTelephoneNumber:
    """
    Implements automatic formatting of the text entered in the text field
    according to the mask, for example '+38 (###) ### ## ##'.

    .. warning:: This class has not yet been implemented and it is not
        recommended to use it yet.
    """

    def __init__(self):
        self._backspace = False

    def isnumeric(self, value) -> bool:
        try:
            int(value)
            return True
        except ValueError:
            return False

    def do_backspace(self, *args) -> None:
        """Do backspace operation from the current cursor position."""

        if self.validator and self.validator == "phone":
            self._backspace = True
            text = self.text
            text = text[:-1]
            self.text = text
            self._backspace = False

    def field_filter(self, value, boolean) -> None:
        if self.validator and self.validator == "phone":
            if len(self.text) == 14:
                return
            if self.isnumeric(value):
                return value
        return value

    def format(self, value) -> None:
        if value != "" and not value.isspace() and not self._backspace:
            if len(value) <= 1 and self.focus:
                self.text = value
                self._check_cursor()
            elif len(value) == 4:
                start = self.text[:-1]
                end = self.text[-1]
                self.text = "%s) %s" % (start, end)
                self._check_cursor()
            elif len(value) == 8:
                self.text += "-"
                self._check_cursor()
            elif len(value) in [12, 16]:
                start = self.text[:-1]
                end = self.text[-1]
                self.text = "%s-%s" % (start, end)
                self._check_cursor()

    def _check_cursor(self):
        def set_pos_cursor(pos_corsor, interval=0.5):
            self.cursor = (pos_corsor, 0)

        if self.focus:
            Clock.schedule_once(lambda x: set_pos_cursor(len(self.text)), 0.1)


class Validator:
    """Container class for various validation methods."""

    datetime_date = ObjectProperty()
    """
    The last valid date as a <class 'datetime.date'> object.

    :attr:`datetime_date` is an :class:`~kivy.properties.ObjectProperty`
    and defaults to `None`.
    """

    date_interval = ListProperty([None, None])
    """
    The date interval that is valid for input.
    Can be entered as <class 'datetime.date'> objects or a string format.
    Both values or just one value can be entered.

    In string format, must follow the current date_format.
    Example: Given date_format -> "mm/dd/yyyy"
    Input examples -> "12/31/1900", "12/31/2100" or "12/31/1900", None.

    :attr:`date_interval` is an :class:`~kivy.properties.ListProperty`
    and defaults to `[None, None]`.
    """

    date_format = OptionProperty(
        None,
        options=[
            "dd/mm/yyyy",
            "mm/dd/yyyy",
            "yyyy/mm/dd",
        ],
    )

    """
    Format of date strings that will be entered.
    Available options are: `'dd/mm/yyyy'`, `'mm/dd/yyyy'`, `'yyyy/mm/dd'`.

    :attr:`date_format` is an :class:`~kivy.properties.OptionProperty`
    and defaults to `None`.
    """

    def is_email_valid(self, text: str) -> bool:
        """Checks the validity of the email."""

        if not re.match(r"[^@]+@[^@]+\.[^@]+", text):
            return True
        return False

    def is_time_valid(self, text: str) -> bool:
        """Checks the validity of the time."""

        if re.match(r"^(2[0-3]|[01]?[0-9]):([0-5]?[0-9])$", text) or re.match(
            r"^(2[0-3]|[01]?[0-9]):([0-5]?[0-9]):([0-5]?[0-9])$", text
        ):
            return False

        return True

    def is_date_valid(self, text: str) -> bool:
        """Checks the validity of the date."""

        if not self.date_format:
            raise Exception("TextInput date_format was not defined.")

        # Regex strings.
        dd = "[0][1-9]|[1-2][0-9]|[3][0-1]"
        mm = "[0][1-9]|[1][0-2]"
        yyyy = "[0-9][0-9][0-9][0-9]"
        fmt = self.date_format.split("/")
        args = locals()
        # Access  the local variables  dict in the correct format based on
        # date_format split. Example: "mm/dd/yyyy" -> ["mm", "dd", "yyyy"]
        # args[fmt[0]] would be args["mm"] so the month regex string.
        if re.match(f"^({args[fmt[0]]})/({args[fmt[1]]})/({args[fmt[2]]})$", text):
            input_split = text.split("/")
            args[fmt[0]] = input_split[0]
            args[fmt[1]] = input_split[1]
            args[fmt[2]] = input_split[2]
            # Organize input  into correct slots and try to convert
            # to datetime  object. This way February exceptions are
            # tested. Also tests with the date_interval are simpler
            # using datetime objects.
            try:
                datetime = date(int(args["yyyy"]), int(args["mm"]), int(args["dd"]))
            except ValueError:
                return True

            if self.date_interval:
                if (
                    self.date_interval[0]
                    and not self.date_interval[0] <= datetime
                    or self.date_interval[1]
                    and not datetime <= self.date_interval[1]
                ):
                    return True

            self.datetime_date = datetime
            return False
        return True

    def on_date_interval(self, *args) -> None:
        """Default event handler for date_interval input."""

        def on_date_interval():
            if not self.date_format:
                raise Exception("TextInput date_format was not defined.")

            fmt = self.date_format.split("/")
            args = {}
            # Convert string inputs into datetime.date objects and store
            # them back into self.date_interval.
            try:
                if self.date_interval[0] and not isinstance(
                    self.date_interval[0], date
                ):
                    split = self.date_interval[0].split("/")
                    args[fmt[0]] = split[0]
                    args[fmt[1]] = split[1]
                    args[fmt[2]] = split[2]
                    self.date_interval[0] = date(
                        int(args["yyyy"]), int(args["mm"]), int(args["dd"])
                    )
                if self.date_interval[1] and not isinstance(
                    self.date_interval[1], date
                ):
                    split = self.date_interval[1].split("/")
                    args[fmt[0]] = split[0]
                    args[fmt[1]] = split[1]
                    args[fmt[2]] = split[2]
                    self.date_interval[1] = date(
                        int(args["yyyy"]), int(args["mm"]), int(args["dd"])
                    )

            except Exception:
                raise Exception(
                    r"TextInput date_interval was defined incorrectly, "
                    r"it must be composed of <class 'datetime.date'> objects "
                    r"or strings following current date_format."
                )

            # Test if the interval is valid.
            if isinstance(self.date_interval[0], date) and isinstance(
                self.date_interval[1], date
            ):
                if self.date_interval[0] >= self.date_interval[1]:
                    raise Exception(
                        "TextInput date_interval last date must be greater "
                        "than the first date or set to None."
                    )

        Clock.schedule_once(lambda x: on_date_interval())


class BaseTextFieldLabel(MDLabel):
    text_color_normal = ColorProperty(None)
    text_color_focus = ColorProperty(None)


class MDTextFieldHelperText(BaseTextFieldLabel):
    mode = OptionProperty("on_focus", options=["on_error", "persistent", "on_focus"])


class MDTextFieldMaxLengthText(BaseTextFieldLabel):
    max_text_length = NumericProperty(None)


class MDTextFieldHintText(BaseTextFieldLabel):
    pass


class BaseTextFieldIcon(MDIcon):
    icon_color_normal = ColorProperty(None)
    icon_color_focus = ColorProperty(None)


class MDTextFieldLeadingIcon(BaseTextFieldIcon):
    pass


class MDTextFieldTrailingIcon(BaseTextFieldIcon):
    pass


class MDTextField(
    DeclarativeBehavior,
    StateLayerBehavior,
    ThemableBehavior,
    TextInput,
    Validator,
    AutoFormatTelephoneNumber,
    BackgroundColorBehavior,
):
    font_style = StringProperty("Body")
    role = StringProperty("large")
    mode = OptionProperty("outlined", options=["outlined", "filled"])
    error_color = ColorProperty(None)
    error = BooleanProperty(False)
    text_color_normal = ColorProperty(None)
    text_color_focus = ColorProperty(None)
    radius = VariableListProperty([dp(4), dp(4), dp(4), dp(4)])
    required = BooleanProperty(False)
    line_color_normal = ColorProperty(None)
    line_color_focus = ColorProperty(None)
    fill_color_normal = ColorProperty(None)
    fill_color_focus = ColorProperty(None)
    max_height = NumericProperty(0)
    phone_mask = StringProperty("")
    """
    This property has not yet been implemented and it is not recommended to
    use it yet.

    :attr:`phone_mask` is a :class:`~kivy.properties.StringProperty` and
    defaults to ''.
    """

    validator = OptionProperty(None, options=["date", "email", "time", "phone"])

    # Helper text label object.
    _helper_text_label = ObjectProperty()
    # Hint text label object.
    _hint_text_label = ObjectProperty()
    # Leading icon object.
    _leading_icon = ObjectProperty()
    # Trailing icon object.
    _trailing_icon = ObjectProperty()
    # Max length label object.
    _max_length_label = ObjectProperty()
    # Maximum length of characters to be input.
    _max_length = "0"
    # Active indicator height.
    _indicator_height = NumericProperty(dp(1))
    # Outline height.
    _outline_height = NumericProperty(dp(1))
    # The x-axis position of the hint text in the text field.
    _hint_x = NumericProperty(0)
    # The y-axis position of the hint text in the text field.
    _hint_y = NumericProperty(0)
    # The right/left lines coordinates of the text field in 'outlined' mode.
    _left_x_axis_pos = NumericProperty(dp(32))
    _right_x_axis_pos = NumericProperty(dp(32))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind(text=self.set_text)
        self.theme_cls.bind(
            primary_palette=self.update_colors,
            theme_style=self.update_colors,
        )
        Clock.schedule_once(self._check_text)

    def update_colors(self, theme_manager: ThemeManager, theme_color: str) -> None:
        """Fired when the `primary_palette` or `theme_style` value changes."""

        def update_colors(*args):
            if not self.disabled:
                self.on_focus(self, self.focus)
            else:
                self.on_disabled(self, self.disabled)

        Clock.schedule_once(update_colors, 1)

    def add_widget(self, widget, index=0, canvas=None):
        if isinstance(widget, MDTextFieldHelperText):
            self._helper_text_label = widget
        if isinstance(widget, MDTextFieldHintText):
            self._hint_text_label = widget
        if isinstance(widget, MDTextFieldLeadingIcon):
            self._leading_icon = widget
        if isinstance(widget, MDTextFieldTrailingIcon):
            self._trailing_icon = widget
        if isinstance(widget, MDTextFieldMaxLengthText):
            self._max_length_label = widget
        else:
            return super().add_widget(widget)

    def set_texture_color(
        self, texture, canvas_group, color: list, error: bool = False
    ) -> None:
        """
        Animates the color of the
        leading/trailing icons/hint/helper/max length text.
        """

        def update_hint_text_rectangle(*args):
            hint_text_rectangle = self.canvas.after.get_group("hint-text-rectangle")[0]
            hint_text_rectangle.texture = None
            texture.texture_update()
            hint_text_rectangle.texture = texture.texture

        if texture:
            Animation(rgba=color, d=0).start(canvas_group)
            a = Animation(color=color, d=0)
            if texture is self._hint_text_label:
                a.bind(on_complete=update_hint_text_rectangle)
            a.start(texture)

    def set_pos_hint_text(self, y: float, x: float) -> None:
        """Animates the x-axis width and y-axis height of the hint text."""

        Animation(_hint_y=y, _hint_x=x, d=0.2, t="out_quad").start(self)

    def set_hint_text_font_size(self) -> None:
        """Animates the font size of the hint text."""

        Animation(size=self._hint_text_label.texture_size, d=0.2, t="out_quad").start(
            self.canvas.after.get_group("hint-text-rectangle")[0]
        )

    def set_space_in_line(
        self, left_width: float | int, right_width: float | int
    ) -> None:
        """
        Animates the length of the right line of the text field for the
        hint text.
        """

        Animation(_left_x_axis_pos=left_width, d=0.2, t="out_quad").start(self)
        Animation(_right_x_axis_pos=right_width, d=0.2, t="out_quad").start(self)

    def set_max_text_length(self) -> None:
        """
        Fired when text is entered into a text field.
        Set max length text and updated max length texture.
        """

        if self._max_length_label:
            self._max_length_label.text = ""
            self._max_length_label.text = (
                f"{len(self.text)}/{self._max_length_label.max_text_length}"
            )
            self._max_length_label.texture_update()
            max_length_rect = self.canvas.before.get_group("max-length-rect")[0]
            max_length_rect.texture = None
            max_length_rect.texture = self._max_length_label.texture
            max_length_rect.size = self._max_length_label.texture_size
            max_length_rect.pos = (
                (self.x + self.width)
                - (self._max_length_label.texture_size[0] + dp(16)),
                self.y - dp(18),
            )

    def set_text(self, instance, text: str) -> None:
        """Fired when text is entered into a text field."""

        def set_text(*args):
            self.text = re.sub("\n", " ", text) if not self.multiline else text
            self.set_max_text_length()

            if self.text and self._get_has_error() or self._get_has_error():
                self.error = True
            elif self.text and not self._get_has_error():
                self.error = False

            # Start the appropriate texture animations when programmatically
            # pasting text into a text field.
            if len(self.text) != 0 and not self.focus:
                if self._hint_text_label:
                    self._hint_text_label.font_size = theme_font_styles[
                        self._hint_text_label.font_style
                    ]["small"]["font-size"]
                    self._hint_text_label.texture_update()
                    self.set_hint_text_font_size()

            if (not self.text and not self.focus) or (self.text and not self.focus):
                self.on_focus(instance, False)

        set_text()

    def on_focus(self, instance, focus: bool) -> None:
        """Fired when the `focus` value changes."""

        if focus:
            if self.mode == "filled":
                Animation(_indicator_height=dp(1.25), d=0).start(self)
            else:
                Animation(_outline_height=dp(1.25), d=0).start(self)

            if self._trailing_icon:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._trailing_icon,
                        self.canvas.before.get_group("trailing-icons-color")[0],
                        (
                            (
                                self.theme_cls.onSurfaceVariantColor
                                if self._trailing_icon.theme_icon_color == "Primary"
                                or not self._trailing_icon.icon_color_focus
                                else self._trailing_icon.icon_color_focus
                            )
                            if not self.error
                            else self._get_error_color()
                        ),
                    )
                )
            if self._leading_icon:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._leading_icon,
                        self.canvas.before.get_group("leading-icons-color")[0],
                        (
                            self.theme_cls.onSurfaceVariantColor
                            if self._leading_icon.theme_icon_color == "Primary"
                            or not self._leading_icon.icon_color_focus
                            else self._leading_icon.icon_color_focus
                        ),
                    )
                )
            if self._max_length_label and not self.error:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._max_length_label,
                        self.canvas.before.get_group("max-length-color")[0],
                        (
                            self.theme_cls.onSurfaceVariantColor
                            if not self._max_length_label.text_color_focus
                            else self._max_length_label.text_color_focus
                        ),
                    )
                )

            if self._helper_text_label and self._helper_text_label.mode in (
                "on_focus",
                "persistent",
            ):
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._helper_text_label,
                        self.canvas.before.get_group("helper-text-color")[0],
                        (
                            (
                                self.theme_cls.onSurfaceVariantColor
                                if not self._helper_text_label.text_color_focus
                                else self._helper_text_label.text_color_focus
                            )
                            if not self.error
                            else self._get_error_color()
                        ),
                    )
                )
            if (
                self._helper_text_label
                and self._helper_text_label.mode == "on_error"
                and not self.error
            ):
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._helper_text_label,
                        self.canvas.before.get_group("helper-text-color")[0],
                        self.theme_cls.transparentColor,
                    )
                )
            if self._hint_text_label:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._hint_text_label,
                        self.canvas.after.get_group("hint-text-color")[0],
                        (
                            (
                                self.theme_cls.primaryColor
                                if not self._hint_text_label.text_color_focus
                                else self._hint_text_label.text_color_focus
                            )
                            if not self.error
                            else self._get_error_color()
                        ),
                    )
                )
                self.set_pos_hint_text(
                    0 if self.mode != "outlined" else dp(-14),
                    (
                        (
                            -(
                                (
                                    self._leading_icon.texture_size[0]
                                    if self._leading_icon
                                    else 0
                                )
                                + dp(12)
                            )
                            if self._leading_icon
                            else 0
                        )
                        if self.mode == "outlined"
                        else -(
                            (
                                self._leading_icon.texture_size[0]
                                if self._leading_icon
                                else 0
                            )
                            - dp(24)
                        )
                    ),
                )
                self._hint_text_label.font_size = theme_font_styles[
                    self._hint_text_label.font_style
                ]["small"]["font-size"]
                self._hint_text_label.texture_update()
                self.set_hint_text_font_size()
                if self.mode == "outlined":
                    self.set_space_in_line(
                        dp(14), self._hint_text_label.texture_size[0] + dp(18)
                    )
        else:
            if self.mode == "filled":
                Animation(_indicator_height=dp(1), d=0).start(self)
            else:
                Animation(_outline_height=dp(1), d=0).start(self)

            if self._leading_icon:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._leading_icon,
                        self.canvas.before.get_group("leading-icons-color")[0],
                        (
                            self.theme_cls.onSurfaceVariantColor
                            if self._leading_icon.theme_icon_color == "Primary"
                            or not self._leading_icon.icon_color_normal
                            else self._leading_icon.icon_color_normal
                        ),
                    )
                )
            if self._trailing_icon:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._trailing_icon,
                        self.canvas.before.get_group("trailing-icons-color")[0],
                        (
                            (
                                self.theme_cls.onSurfaceVariantColor
                                if self._trailing_icon.theme_icon_color == "Primary"
                                or not self._trailing_icon.icon_color_normal
                                else self._trailing_icon.icon_color_normal
                            )
                            if not self.error
                            else self._get_error_color()
                        ),
                    )
                )
            if self._max_length_label and not self.error:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._max_length_label,
                        self.canvas.before.get_group("max-length-color")[0],
                        (
                            self.theme_cls.onSurfaceVariantColor
                            if not self._max_length_label.text_color_normal
                            else self._max_length_label.text_color_normal
                        ),
                    )
                )
            if self._helper_text_label and self._helper_text_label.mode == "on_focus":
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._helper_text_label,
                        self.canvas.before.get_group("helper-text-color")[0],
                        self.theme_cls.transparentColor,
                    )
                )
            elif (
                self._helper_text_label and self._helper_text_label.mode == "persistent"
            ):
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._helper_text_label,
                        self.canvas.before.get_group("helper-text-color")[0],
                        (
                            (
                                self.theme_cls.onSurfaceVariantColor
                                if not self._helper_text_label.text_color_normal
                                else self._helper_text_label.text_color_normal
                            )
                            if not self.error
                            else self._get_error_color()
                        ),
                    )
                )

            if not self.text:
                if self._hint_text_label:
                    if self.mode == "outlined":
                        self.set_space_in_line(dp(32), dp(32))
                    self._hint_text_label.font_size = theme_font_styles[
                        self._hint_text_label.font_style
                    ]["large"]["font-size"]
                    self._hint_text_label.texture_update()
                    self.set_hint_text_font_size()
                    self.set_pos_hint_text(
                        (self.height / 2) - (self._hint_text_label.texture_size[1] / 2),
                        0,
                    )
            else:
                if self._hint_text_label:
                    if self.mode == "outlined":
                        self.set_space_in_line(
                            dp(14),
                            self._hint_text_label.texture_size[0] + dp(18),
                        )
                    self.set_pos_hint_text(
                        0 if self.mode != "outlined" else dp(-14),
                        (
                            (
                                -(
                                    (
                                        self._leading_icon.texture_size[0]
                                        if self._leading_icon
                                        else 0
                                    )
                                    + dp(12)
                                )
                                if self._leading_icon
                                else 0
                            )
                            if self.mode == "outlined"
                            else -(
                                (
                                    self._leading_icon.texture_size[0]
                                    if self._leading_icon
                                    else 0
                                )
                                - dp(24)
                            )
                        ),
                    )

            if self._hint_text_label:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._hint_text_label,
                        self.canvas.after.get_group("hint-text-color")[0],
                        (
                            (
                                self.theme_cls.onSurfaceVariantColor
                                if not self._hint_text_label.text_color_normal
                                else self._hint_text_label.text_color_normal
                            )
                            if not self.error
                            else self._get_error_color()
                        ),
                    ),
                )

    def on_disabled(self, instance, disabled: bool) -> None:
        """Fired when the `disabled` value changes."""

        super().on_disabled(instance, disabled)

        def on_disabled(*args):
            if disabled:
                self._set_disabled_colors()
            else:
                self._set_enabled_colors()

        Clock.schedule_once(on_disabled, 0.2)

    def on_error(self, instance, error: bool) -> None:
        """
        Changes the primary colors of the text box to match the `error` value
        (text field is in an error state or not).
        """

        if error:
            if self._max_length_label:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._max_length_label,
                        self.canvas.before.get_group("max-length-color")[0],
                        self._get_error_color(),
                    )
                )
            if self._hint_text_label:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._hint_text_label,
                        self.canvas.after.get_group("hint-text-color")[0],
                        self._get_error_color(),
                    ),
                )
            if self._helper_text_label and self._helper_text_label.mode in (
                "persistent",
                "on_error",
            ):
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._helper_text_label,
                        self.canvas.before.get_group("helper-text-color")[0],
                        self._get_error_color(),
                    )
                )
            if self._trailing_icon:
                Clock.schedule_once(
                    lambda x: self.set_texture_color(
                        self._trailing_icon,
                        self.canvas.before.get_group("trailing-icons-color")[0],
                        self._get_error_color(),
                    )
                )
        else:
            self.on_focus(self, self.focus)

    def on_height(self, instance, value_height: float) -> None:
        if value_height >= self.max_height and self.max_height:
            self.height = self.max_height

    def _set_enabled_colors(self):
        def schedule_set_texture_color(widget, group_name, color):
            Clock.schedule_once(
                lambda x: self.set_texture_color(widget, group_name, color)
            )

        max_length_label_group = self.canvas.before.get_group("max-length-color")
        helper_text_label_group = self.canvas.before.get_group("helper-text-color")
        hint_text_label_group = self.canvas.after.get_group("hint-text-color")
        leading_icon_group = self.canvas.before.get_group("leading-icons-color")
        trailing_icon_group = self.canvas.before.get_group("trailing-icons-color")

        error_color = self._get_error_color()
        on_surface_variant_color = self.theme_cls.onSurfaceVariantColor

        if self._max_length_label:
            schedule_set_texture_color(
                self._max_length_label,
                max_length_label_group[0],
                (
                    self._max_length_label.color[:-1] + [1]
                    if not self.error
                    else error_color
                ),
            )
        if self._helper_text_label:
            schedule_set_texture_color(
                self._helper_text_label,
                helper_text_label_group[0],
                (
                    on_surface_variant_color
                    if not self._helper_text_label.text_color_focus
                    else (
                        self._helper_text_label.text_color_focus
                        if not self.error
                        else error_color
                    )
                ),
            )
        if self._hint_text_label:
            schedule_set_texture_color(
                self._hint_text_label,
                hint_text_label_group[0],
                (
                    on_surface_variant_color
                    if not self._hint_text_label.text_color_normal
                    else (
                        self._hint_text_label.text_color_normal
                        if not self.error
                        else error_color
                    )
                ),
            )
        if self._leading_icon:
            schedule_set_texture_color(
                self._leading_icon,
                leading_icon_group[0],
                (
                    on_surface_variant_color
                    if self._leading_icon.theme_icon_color == "Primary"
                    or not self._leading_icon.icon_color_normal
                    else self._leading_icon.icon_color_normal
                ),
            )
        if self._trailing_icon:
            schedule_set_texture_color(
                self._trailing_icon,
                trailing_icon_group[0],
                (
                    on_surface_variant_color
                    if self._trailing_icon.theme_icon_color == "Primary"
                    or not self._trailing_icon.icon_color_normal
                    else (
                        self._trailing_icon.icon_color_normal
                        if not self.error
                        else error_color
                    )
                ),
            )

    def _set_disabled_colors(self):
        def schedule_set_texture_color(widget, group_name, color, opacity):
            Clock.schedule_once(
                lambda x: self.set_texture_color(widget, group_name, color + [opacity])
            )

        max_length_label_group = self.canvas.before.get_group("max-length-color")
        helper_text_label_group = self.canvas.before.get_group("helper-text-color")
        hint_text_label_group = self.canvas.after.get_group("hint-text-color")
        leading_icon_group = self.canvas.before.get_group("leading-icons-color")
        trailing_icon_group = self.canvas.before.get_group("trailing-icons-color")

        disabled_color = self.theme_cls.disabledTextColor[:-1]

        if self._max_length_label:
            schedule_set_texture_color(
                self._max_length_label,
                max_length_label_group[0],
                disabled_color,
                self.text_field_opacity_value_disabled_max_length_label,
            )
        if self._helper_text_label:
            schedule_set_texture_color(
                self._helper_text_label,
                helper_text_label_group[0],
                disabled_color,
                self.text_field_opacity_value_disabled_helper_text_label,
            )
        if self._hint_text_label:
            schedule_set_texture_color(
                self._hint_text_label,
                hint_text_label_group[0],
                disabled_color,
                self.text_field_opacity_value_disabled_hint_text_label,
            )
        if self._leading_icon:
            schedule_set_texture_color(
                self._leading_icon,
                leading_icon_group[0],
                disabled_color,
                self.text_field_opacity_value_disabled_leading_icon,
            )
        if self._trailing_icon:
            schedule_set_texture_color(
                self._trailing_icon,
                trailing_icon_group[0],
                disabled_color,
                self.text_field_opacity_value_disabled_trailing_icon,
            )

    def _get_has_error(self) -> bool:
        """
        Returns `False` or `True` depending on the state of the text field,
        for example when the allowed character limit has been exceeded or when
        the :attr:`~MDTextField.required` parameter is set to `True`.
        """

        if self.validator and self.validator != "phone":
            has_error = {
                "date": self.is_date_valid,
                "email": self.is_email_valid,
                "time": self.is_time_valid,
            }[self.validator](self.text)
            return has_error
        if (
            self._max_length_label
            and len(self.text) > self._max_length_label.max_text_length
        ):
            has_error = True
        else:
            if all((self.required, len(self.text) == 0)):
                has_error = True
            else:
                has_error = False
        return has_error

    def _get_error_color(self):
        return self.theme_cls.errorColor if not self.error_color else self.error_color

    def _check_text(self, *args) -> None:
        self.set_text(self, self.text)

    def _refresh_hint_text(self):
        """Method override to avoid duplicate hint text texture."""
