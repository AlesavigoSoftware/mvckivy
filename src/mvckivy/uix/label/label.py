from __future__ import annotations

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.graphics import Color
from kivy.graphics.vertex_instructions import SmoothRoundedRectangle
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
    VariableListProperty,
)
from kivy.uix.label import Label

from kivymd.icon_definitions import md_icons
from kivymd.theming import ThemableBehavior
from kivymd.uix.label import MDIcon
from kivymd.uix import MDAdaptiveWidget
from kivymd.uix.behaviors import (
    DeclarativeBehavior,
    TouchBehavior,
    BackgroundColorBehavior,
)
from kivymd.uix.behaviors.state_layer_behavior import StateLayerBehavior

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty


class MKVBaseLabel(
    AliasDedupeMixin,
    DeclarativeBehavior,
    ThemableBehavior,
    BackgroundColorBehavior,
    Label,
    MDAdaptiveWidget,
    TouchBehavior,
    StateLayerBehavior,
):
    font_style = StringProperty("Body")
    role = OptionProperty("large", options=["large", "medium", "small"])
    text = StringProperty()
    text_color = ColorProperty(None)

    font_size_custom = NumericProperty(None, allownone=True)
    line_height_custom = NumericProperty(None, allownone=True)
    font_name_custom = StringProperty(None, allownone=True)

    def _get_font_style_value(self, token: str, default):
        font_styles = {}
        theme_cls = self.theme_cls
        if theme_cls is not None and hasattr(theme_cls, "font_styles"):
            styles_attr = theme_cls.font_styles or {}
            if isinstance(styles_attr, dict):
                font_styles = styles_attr
        style_block = font_styles.get(self.font_style, {})
        role_block = style_block.get(self.role, {})
        return role_block.get(token, default)

    # --- text color -----------------------------------------------------
    def _get_alias_color(self, prop: ExtendedAliasProperty):
        return self._calc_alias_color(prop)

    def _calc_alias_color(self, prop: ExtendedAliasProperty):
        theme_cls = self.theme_cls
        on_surface = theme_cls.onSurfaceColor

        on_surface_variant = on_surface
        if hasattr(theme_cls, "onSurfaceVariantColor"):
            variant_value = theme_cls.onSurfaceVariantColor
            if variant_value is not None:
                on_surface_variant = variant_value

        outline_color = on_surface
        if hasattr(theme_cls, "outlineColor"):
            outline_value = theme_cls.outlineColor
            if outline_value is not None:
                outline_color = outline_value

        error_color = on_surface
        if hasattr(theme_cls, "errorColor"):
            error_value = theme_cls.errorColor
            if error_value is not None:
                error_color = error_value

        mapping = {
            "Primary": on_surface,
            "Secondary": on_surface_variant,
            "Hint": outline_color,
            "Error": error_color,
        }
        if self.theme_text_color == "Custom" and self.text_color:
            return self.text_color
        if self.theme_text_color in mapping:
            return mapping[self.theme_text_color]
        if self.text_color:
            return self.text_color
        return self.theme_cls.onSurfaceColor

    alias_color = ExtendedAliasProperty(
        _get_alias_color,
        None,
        bind=(
            "theme_text_color",
            "text_color",
            "theme_cls.onSurfaceColor",
            "theme_cls.onSurfaceVariantColor",
            "theme_cls.outlineColor",
            "theme_cls.errorColor",
        ),
        cache=True,
        watch_before_use=True,
    )

    def _get_alias_text_size(self, prop: ExtendedAliasProperty):
        return self._calc_alias_text_size(prop)

    def _calc_alias_text_size(self, prop: ExtendedAliasProperty):
        if self.adaptive_size:
            return None, None
        if self.adaptive_width:
            return None, None
        return self.width, None

    alias_text_size = ExtendedAliasProperty(
        _get_alias_text_size,
        None,
        bind=(
            "adaptive_size",
            "adaptive_width",
            "width",
            "height",
        ),
        cache=True,
        watch_before_use=True,
    )

    # --- disabled color -------------------------------------------------
    def _get_alias_disabled_color(self, prop: ExtendedAliasProperty):
        return self._calc_alias_disabled_color(prop)

    def _calc_alias_disabled_color(self, prop: ExtendedAliasProperty):
        base = list(self.theme_cls.onSurfaceColor)
        if len(base) < 4:
            base = base[:3] + [1.0]
        base[3] = self.label_opacity_value_disabled_text
        return base

    alias_disabled_color = ExtendedAliasProperty(
        _get_alias_disabled_color,
        None,
        bind=(
            "theme_cls.onSurfaceColor",
            "label_opacity_value_disabled_text",
        ),
        cache=True,
        watch_before_use=True,
    )

    # --- font size ------------------------------------------------------
    def _get_alias_font_size(self, prop: ExtendedAliasProperty):
        return self._calc_alias_font_size(prop)

    def _calc_alias_font_size(self, prop: ExtendedAliasProperty):
        if self.theme_font_size == "Primary":
            default = self.property("font_size").defaultvalue
            return self._get_font_style_value("font-size", default)
        if self.font_size_custom is not None:
            return self.font_size_custom
        return self.property("font_size").defaultvalue

    alias_font_size = ExtendedAliasProperty(
        _get_alias_font_size,
        None,
        bind=(
            "theme_font_size",
            "font_size_custom",
            "font_style",
            "role",
            "theme_cls.font_styles",
        ),
        cache=True,
        watch_before_use=True,
    )

    # --- line height ----------------------------------------------------
    def _get_alias_line_height(self, prop: ExtendedAliasProperty):
        return self._calc_alias_line_height(prop)

    def _calc_alias_line_height(self, prop: ExtendedAliasProperty):
        if self.theme_line_height == "Primary":
            default = self.property("line_height").defaultvalue
            return self._get_font_style_value("line-height", default)
        if self.line_height_custom is not None:
            return self.line_height_custom
        return self.property("line_height").defaultvalue

    alias_line_height = ExtendedAliasProperty(
        _get_alias_line_height,
        None,
        bind=(
            "theme_line_height",
            "line_height_custom",
            "font_style",
            "role",
            "theme_cls.font_styles",
        ),
        cache=True,
        watch_before_use=True,
    )

    # --- font name ------------------------------------------------------
    def _get_alias_font_name(self, prop: ExtendedAliasProperty):
        return self._calc_alias_font_name(prop)

    def _calc_alias_font_name(self, prop: ExtendedAliasProperty):
        if self.theme_font_name == "Primary":
            default = self.property("font_name").defaultvalue
            return self._get_font_style_value("font-name", default)
        if self.font_name_custom:
            return self.font_name_custom
        return self.property("font_name").defaultvalue

    alias_font_name = ExtendedAliasProperty(
        _get_alias_font_name,
        None,
        bind=(
            "theme_font_name",
            "font_name_custom",
            "font_style",
            "role",
            "theme_cls.font_styles",
        ),
        cache=True,
        watch_before_use=True,
    )

    # --- sync helpers ---------------------------------------------------
    def on_font_size(self, instance, value):
        try:
            super().on_font_size(instance, value)
        except AttributeError:
            pass
        if self.theme_font_size == "Custom":
            self.font_size_custom = value

    def on_theme_font_size(self, instance, value):
        if value == "Primary":
            self.font_size_custom = None

    def on_line_height(self, instance, value):
        try:
            super().on_line_height(instance, value)
        except AttributeError:
            pass
        if self.theme_line_height == "Custom":
            self.line_height_custom = value

    def on_theme_line_height(self, instance, value):
        if value == "Primary":
            self.line_height_custom = None

    def on_font_name(self, instance, value):
        try:
            super().on_font_name(instance, value)
        except AttributeError:
            pass
        if self.theme_font_name == "Custom":
            self.font_name_custom = value

    def on_theme_font_name(self, instance, value):
        if value == "Primary":
            self.font_name_custom = None


class MKVLabel(MKVBaseLabel):
    allow_copy = BooleanProperty(False)
    allow_selection = BooleanProperty(False)
    color_selection = ColorProperty(None)
    color_deselection = ColorProperty(None)
    is_selected = BooleanProperty(False)
    radius = VariableListProperty([0], length=4)
    _canvas_bg = ObjectProperty(allownone=True)

    __events__ = ("on_copy", "on_selection", "on_cancel_selection")

    def do_selection(self) -> None:
        if not self.is_selected:
            self.md_bg_color = (
                self.theme_cls.secondaryContainerColor
                if not self.color_selection
                else self.color_selection
            )

    def cancel_selection(self) -> None:
        if self.is_selected:
            self.canvas.before.remove_group("md-label-selection-color")
            self.canvas.before.remove_group("md-label-selection-color-rectangle")
            self.md_bg_color = (
                self.parent.md_bg_color
                if not self.color_deselection
                else self.color_deselection
            )
            self.dispatch("on_cancel_selection")
            self.is_selected = False
            self._canvas_bg = None

    def on_double_tap(self, touch, *args) -> None:
        if self.allow_copy and self.collide_point(*touch.pos):
            Clipboard.copy(self.text)
            self.dispatch("on_copy")
        if self.allow_selection and self.collide_point(*touch.pos):
            self.do_selection()
            self.dispatch("on_selection")
            self.is_selected = True

    def on_window_touch(self, *args) -> None:
        if self.is_selected:
            self.cancel_selection()

    def on_copy(self, *args) -> None:
        pass

    def on_selection(self, *args) -> None:
        pass

    def on_cancel_selection(self, *args) -> None:
        pass

    def on_allow_selection(self, instance_label, selection: bool) -> None:
        if selection:
            Window.bind(on_touch_down=self.on_window_touch)
        else:
            Window.unbind(on_touch_down=self.on_window_touch)

    def on_text_color(self, instance_label, color: list | str) -> None:
        if self.theme_text_color == "Custom":
            if self.theme_cls.theme_style_switch_animation:
                Animation(
                    color=self.text_color,
                    d=self.theme_cls.theme_style_switch_animation_duration,
                    t="linear",
                ).start(self)
            else:
                self.color = self.text_color

    def on_md_bg_color(self, instance_label, color: list | str) -> None:
        def on_md_bg_color(*args) -> None:
            from kivymd.uix.selectioncontrol import MDCheckbox
            from kivymd.uix.tooltip import MDTooltipPlain

            if not issubclass(
                self.__class__, (MDCheckbox, MDIcon, MKVIcon, MDTooltipPlain)
            ):
                self.canvas.remove_group("Background_instruction")
                with self.canvas.before:
                    Color(rgba=color, group="md-label-selection-color")
                    self._canvas_bg = SmoothRoundedRectangle(
                        pos=self.pos,
                        size=self.size,
                        radius=self.radius,
                        group="md-label-selection-color-rectangle",
                    )
                    self.bind(pos=self.update_canvas_bg_pos)

        Clock.schedule_once(on_md_bg_color)

    def on_size(self, instance_label, size: list) -> None:
        if self._canvas_bg:
            self._canvas_bg.size = size

    def update_canvas_bg_pos(self, instance_label, pos: list) -> None:
        if self._canvas_bg:
            self._canvas_bg.pos = pos


class MKVIcon(MKVLabel):
    icon = StringProperty("blank")
    source = StringProperty(None, allownone=True)
    icon_color = ColorProperty(None)
    icon_color_disabled = ColorProperty(None)
    _badge = ObjectProperty()

    def _get_alias_icon_text(self, prop: ExtendedAliasProperty):
        return self._calc_alias_icon_text(prop)

    def _calc_alias_icon_text(self, prop: ExtendedAliasProperty):
        if self.font_name == "Icons":
            return md_icons.get(self.icon, "blank")
        return self.icon

    alias_icon_text = ExtendedAliasProperty(
        _get_alias_icon_text,
        None,
        bind=("icon", "font_name"),
        cache=True,
        watch_before_use=True,
    )

    def _get_alias_icon_color(self, prop: ExtendedAliasProperty):
        return self._calc_alias_icon_color(prop)

    def _calc_alias_icon_color(self, prop: ExtendedAliasProperty):
        try:
            is_disabled = self.disabled
        except AttributeError:
            # ``Widget`` has not finished initialising yet. Treat as enabled
            # to avoid accessing ``_disabled_count`` before it exists.
            is_disabled = False

        if is_disabled and self.icon_color_disabled:
            return self.icon_color_disabled
        if self.icon_color:
            return self.icon_color
        theme_cls = self.theme_cls
        base = theme_cls.onSurfaceColor
        if hasattr(theme_cls, "onSurfaceVariantColor"):
            variant_value = theme_cls.onSurfaceVariantColor
            if variant_value is not None:
                base = variant_value
        if is_disabled:
            muted = list(base)
            if len(muted) < 4:
                muted = muted[:3] + [1.0]
            muted[3] = self.label_opacity_value_disabled_text
            return muted
        return base

    alias_icon_color = ExtendedAliasProperty(
        _get_alias_icon_color,
        None,
        bind=(
            "icon_color",
            "icon_color_disabled",
            "disabled",
            "theme_cls.onSurfaceVariantColor",
            "theme_cls.onSurfaceColor",
            "label_opacity_value_disabled_text",
        ),
        cache=True,
        watch_before_use=True,
    )

    def _get_alias_icon_source(self, prop: ExtendedAliasProperty):
        return self._calc_alias_icon_source(prop)

    def _calc_alias_icon_source(self, prop: ExtendedAliasProperty):
        if self.source is not None:
            return self.source
        if self.font_name == "Icons" and self.icon in md_icons:
            return None
        if self.icon in md_icons:
            return None
        return self.icon

    alias_icon_source = ExtendedAliasProperty(
        _get_alias_icon_source,
        None,
        bind=("icon", "source", "font_name"),
        cache=True,
        watch_before_use=True,
    )

    def add_widget(self, widget, index=0, canvas=None):
        from kivymd.uix.badge import MDBadge

        if isinstance(widget, MDBadge):
            self._badge = widget
            return super().add_widget(widget)
        return super().add_widget(widget, index=index, canvas=canvas)
