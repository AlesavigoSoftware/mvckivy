from __future__ import annotations

import re

from kivy.properties import (
    ColorProperty,
    OptionProperty,
    VariableListProperty,
)
from kivy.uix.textinput import TextInput

from kivymd.font_definitions import theme_font_styles
from kivymd.theming import ThemableBehavior, ThemeManager
from kivymd.uix.behaviors import DeclarativeBehavior, BackgroundColorBehavior
from kivymd.uix.behaviors.state_layer_behavior import StateLayerBehavior
from kivymd.uix.label import MDIcon, MDLabel

from types import SimpleNamespace
from typing import Callable, TypedDict, Literal

from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import (
    AliasProperty,
    NumericProperty,
)

from importlib import import_module
from typing import Any

from kivy.properties import (
    ListProperty,
    StringProperty,
    BooleanProperty,
    ObjectProperty,
)
from kivy.clock import Clock

try:
    from kivymd.uix.textfield import MDTextField as _BaseField
except Exception:
    from kivy.uix.textinput import TextInput as _BaseField

from .validators import (
    ValidatorBehavior,
    ValidatorResolver,
    EmailValidator,
    IPValidator,
    PhoneValidator,
    DateValidator,
    DateRangeValidator,
    TimeValidator,
)
from .masks import PhoneMask


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


class IndicatorPatch(TypedDict, total=False):
    outline_height: float
    indicator_height: float


class HintPatch(TypedDict, total=False):
    y: float
    x: float
    font_size: float
    space_in_line: tuple[float, float]  # (left, width)


class AlphasPatch(TypedDict, total=False):
    helper_alpha: float
    hint_alpha: float
    leading_alpha: float
    trailing_alpha: float
    maxlen_alpha: float


class AnimSpec(TypedDict, total=False):
    target: Literal["self", "hint_label", "leading_icon", "trailing_icon"]
    props: dict[str, float]
    d: float
    t: str | None
    delay: float
    key: str | None


class AnimGroup(TypedDict, total=False):
    mode: Literal["parallel", "sequence"]
    items: list[AnimSpec | "AnimGroup"]


class Patch(TypedDict, total=False):
    indicator: IndicatorPatch
    hint: HintPatch
    alphas: AlphasPatch
    anims: list[AnimGroup | AnimSpec]


class StyleTokens:
    def __init__(self, theme_cls):
        self.t = theme_cls

    def indicator_height(self, w) -> IndicatorPatch:
        if getattr(w, "mode", "filled") == "filled":
            return {"indicator_height": dp(1.25 if w.focus else 1.0)}
        else:
            return {"outline_height": dp(1.25 if w.focus else 1.0)}

    def hint_metrics(self, w, hint_label, leading_icon) -> HintPatch:
        has_text = bool(getattr(w, "text", ""))
        if not has_text and not w.focus:
            font_size = theme_font_styles[hint_label.font_style]["large"]["font-size"]
            # центрируем текстуру по вертикали контейнера — дальше это уйдёт в _hint_y
            y = (hint_label.height / 2) - (hint_label.texture_size[1] / 2)
            return {"y": y, "x": 0.0, "font_size": font_size}

        font_size = theme_font_styles[hint_label.font_style]["small"]["font-size"]
        if getattr(w, "mode", "filled") == "outlined":
            x = -(
                ((leading_icon.texture_size[0] if leading_icon else 0) + dp(12))
                if leading_icon
                else 0
            )
            return {
                "y": dp(0.0),
                "x": x,
                "font_size": font_size,
                "space_in_line": (dp(14), hint_label.texture_size[0] + dp(18)),
            }
        else:
            x = -((leading_icon.texture_size[0] if leading_icon else 0) - dp(24))
            return {"y": 0.0, "x": x, "font_size": font_size}

    # целевые альфы для плавного проявления/скрытия
    def helper_target_alpha(self, w) -> float:
        lbl = w._helper_text_label
        mode = getattr(lbl, "mode", None) if lbl else None
        if not mode:
            return 0.0
        if mode == "persistent":
            return 1.0
        if mode == "on_focus":
            return 1.0 if (w.focus and not w.error) else 0.0
        if mode == "on_error":
            return 1.0 if w.error else 0.0
        return 0.0

    def hint_target_alpha(self, w) -> float:
        return 1.0 if w._hint_text_label else 0.0

    def leading_target_alpha(self, w) -> float:
        return 1.0 if w._leading_icon else 0.0

    def trailing_target_alpha(self, w) -> float:
        return 1.0 if w._trailing_icon else 0.0

    def maxlen_target_alpha(self, w) -> float:
        lab = w._max_length_label
        return 1.0 if (lab and lab.texture) else 0.0


RoleRule = Callable[[Any, Any, StyleTokens], dict]


def rule_indicator(w, o, t: StyleTokens) -> dict:
    return {"indicator": t.indicator_height(w)}


def rule_hint_text(w, o, t: StyleTokens) -> dict:
    if not o.hint_label:
        return {}
    hint = t.hint_metrics(w, o.hint_label, o.leading_icon)
    return {
        "hint": hint,
        "alphas": {"hint_alpha": t.hint_target_alpha(w)},
    }


def rule_helper_text(w, o, t: StyleTokens) -> dict:
    if not o.helper_label:
        return {}
    return {"alphas": {"helper_alpha": t.helper_target_alpha(w)}}


def rule_icons(w, o, t: StyleTokens) -> dict:
    return {
        "alphas": {
            "leading_alpha": t.leading_target_alpha(w),
            "trailing_alpha": t.trailing_target_alpha(w),
        }
    }


def rule_max_length(w, o, t: StyleTokens) -> dict:
    return {"alphas": {"maxlen_alpha": t.maxlen_target_alpha(w)}}


class RoleRegistry:
    def __init__(self):
        self._rules: dict[str, RoleRule] = {}

    def register(self, role: str, rule: RoleRule) -> None:
        self._rules[role] = rule

    def build_patch(self, w, tokens: StyleTokens, *, objs) -> dict:
        patch: dict = {}
        for _, rule in self._rules.items():
            part = rule(w, objs, tokens)
            for k, v in part.items():
                if isinstance(v, dict):
                    if k == "anims":
                        patch.setdefault(k, [])
                        if isinstance(v, list):
                            patch[k].extend(v)
                        else:
                            patch[k].append(v)
                    else:
                        patch.setdefault(k, {}).update(v)
                else:
                    patch[k] = v
        return patch


class Renderer:
    def __init__(self, host_widget):
        self.w = host_widget
        self._anim_by_key: dict[str, Animation] = {}

    def _resolve_target(self, name: str):
        return {
            "self": self.w,
            "hint_label": self.w._hint_text_label,
            "leading_icon": self.w._leading_icon,
            "trailing_icon": self.w._trailing_icon,
        }.get(name, None)

    def _build_kivy_anim(self, spec: AnimSpec):
        target = self._resolve_target(spec.get("target", "self"))
        if not target:
            return None, None, None, 0.0
        props = spec.get("props", {})
        anim = Animation(**props, d=spec.get("d", 0.0), t=spec.get("t", None))
        return anim, target, spec.get("key"), spec.get("delay", 0.0)

    def _play_group(self, g: AnimGroup | AnimSpec):
        if isinstance(g, dict) and "target" in g:
            anim, target, key, delay = self._build_kivy_anim(g)  # type: ignore[arg-type]
            if not anim or not target:
                return
            if key and (old := self._anim_by_key.get(key)):
                try:
                    old.stop(target=target)
                except Exception:
                    pass

            def _start(_dt):
                if key:
                    self._anim_by_key[key] = anim
                anim.start(target)

            Clock.schedule_once(_start, delay or 0)
            return

        mode = g.get("mode", "parallel")
        items = g.get("items", [])
        if mode == "parallel":
            for it in items:
                self._play_group(it)
        else:  # sequence
            chain: Animation | None = None
            target0 = None
            for it in items:
                anim, target, key, delay = self._build_kivy_anim(it)  # type: ignore[arg-type]
                if not anim or not target or delay:

                    def _step_start(a=anim, tg=target, k=key):
                        if k and (old := self._anim_by_key.get(k)):
                            try:
                                old.stop(target=tg)
                            except Exception:
                                pass
                        a.start(tg)

                    Clock.schedule_once(lambda _dt, fn=_step_start: fn(), 0)
                    continue
                if chain is None:
                    chain, target0 = anim, target
                else:
                    chain = chain + anim
            if chain is not None:
                Clock.schedule_once(lambda _dt: chain.start(target0), 0)

    def apply(self, patch: Patch) -> None:
        # 1) высоты индикаторов (NumericProperty → KV перерисует Line)
        ind = patch.get("indicator", {})
        if "indicator_height" in ind:
            Animation(_indicator_height=ind["indicator_height"], d=0).start(self.w)
        if "outline_height" in ind:
            Animation(_outline_height=ind["outline_height"], d=0).start(self.w)

        # 2) hint-метрики → свойства (никаких texture_update/set_* вызовов)
        def _apply_hint(_dt):
            hint = patch.get("hint", {})
            if not hint:
                return
            if "font_size" in hint:
                # меняем только prop — лейбл возьмёт её через биндинг; Kivy сам обновит текстуру
                self.w.hint_font_size = hint["font_size"]
            if "x" in hint:
                self.w._hint_x = hint["x"]
            if "y" in hint:
                self.w._hint_y = hint["y"]
            if (
                "space_in_line" in hint
                and getattr(self.w, "mode", "filled") == "outlined"
            ):
                left, width = hint["space_in_line"]
                # прямая замена set_space_in_line(left, width):
                self.w._left_x_axis_pos = left
                self.w._right_x_axis_pos = left + width

        Clock.schedule_once(_apply_hint, 0)

        # 3) мгновенные альфы (если без анимации)
        def _apply_alphas(_dt):
            alphas = patch.get("alphas", {})
            for prop in (
                "helper_alpha",
                "hint_alpha",
                "leading_alpha",
                "trailing_alpha",
                "maxlen_alpha",
            ):
                if prop in alphas:
                    setattr(self.w, prop, alphas[prop])  # type: ignore[index]

        Clock.schedule_once(_apply_alphas, 0)

        # 4) анимации свойств (если роли их добавят)
        for g in patch.get("anims", []) or []:
            self._play_group(g)


class MVCDefaultTextFieldView(
    DeclarativeBehavior,
    StateLayerBehavior,
    ThemableBehavior,
    TextInput,
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
    line_color_focus = ColorProperty(None)
    line_color_normal = ColorProperty(None)
    fill_color_normal = ColorProperty(None)
    fill_color_focus = ColorProperty(None)
    max_height = NumericProperty(0)

    pad_left_base = NumericProperty(dp(16))
    pad_right_base = NumericProperty(dp(16))
    pad_leading_outlined = NumericProperty(dp(12))
    pad_leading_filled_noicon = NumericProperty(dp(4))
    pad_leading_filled_icon = NumericProperty(dp(16))
    pad_trailing_right = NumericProperty(dp(14))
    hint_gap_with_leading = NumericProperty(dp(28))
    helper_y_offset = NumericProperty(dp(-18))

    _max_length: str = "0"

    _indicator_height = NumericProperty(dp(1))
    _outline_height = NumericProperty(dp(1))
    _hint_x = NumericProperty(0)
    _hint_y = NumericProperty(0)
    _left_x_axis_pos = NumericProperty(dp(32))
    _right_x_axis_pos = NumericProperty(dp(32))

    hint_font_size = NumericProperty(0)

    helper_alpha = NumericProperty(1.0)
    hint_alpha = NumericProperty(1.0)
    leading_alpha = NumericProperty(1.0)
    trailing_alpha = NumericProperty(1.0)
    maxlen_alpha = NumericProperty(1.0)
    validators_spec = ListProperty([])
    validator_resolver = ObjectProperty(allownone=True)
    validation_mode = StringProperty(
        "on_focus"
    )  # on_focus | on_enter | on_type | on_focus_or_enter
    mask_name = StringProperty("")
    mask_pattern = StringProperty("")
    mask_placeholder = StringProperty("#")
    is_valid = BooleanProperty(True)

    __validators: list[ValidatorBehavior]
    __mask: Any | None
    __digits: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__validators = []
        self.__mask = None
        self.__digits = ""
        self.multiline = False
        self.bind(
            validators_spec=self._on_spec,
            mask_name=self._on_mask_change,
            mask_pattern=self._on_mask_change,
            mask_placeholder=self._on_mask_change,
        )
        self.bind(on_text_validate=self._on_enter)

    def register_validator_aliases(
        self, mapping: dict[str, str | type[ValidatorBehavior]]
    ) -> None:
        res = self._ensure_resolver()
        for name, ref in mapping.items():
            if isinstance(ref, str):
                modname, clsname = (
                    ref.split(":", 1)
                    if ":" in ref
                    else (".".join(ref.split(".")[:-1]), ref.split(".")[-1])
                )
                mod = import_module(modname)
                cls = getattr(mod, clsname)
            else:
                cls = ref
            res.register(name, cls)

    def _ensure_resolver(self) -> ValidatorResolver:
        if self.validator_resolver is None:
            r = ValidatorResolver()
            r.register("email", EmailValidator)
            r.register("ip", IPValidator)
            r.register("phone", PhoneValidator)
            r.register("date", DateValidator)
            r.register("date_range", DateRangeValidator)
            r.register("time", TimeValidator)
            self.validator_resolver = r
        return self.validator_resolver

    def on_kv_post(self, base_widget):
        if self.validators_spec:
            self._rebuild_validators()
        if self.mask_name or self.mask_pattern:
            self._rebuild_mask()

    def _on_spec(self, *_):
        self._rebuild_validators()

    def _rebuild_validators(self) -> None:
        res = self._ensure_resolver()
        self.__validators = res.create_many(self.validators_spec)

    def _on_mask_change(self, *_):
        self._rebuild_mask()

    def _rebuild_mask(self) -> None:
        self.__mask = None
        if self.mask_name == "phone" or self.mask_pattern:
            pattern = self.mask_pattern or "+38 (###) ### ## ##"
            self.__mask = PhoneMask(pattern=pattern, placeholder=self.mask_placeholder)
            self._apply_mask_after_text_change()

    def _editable_positions(self) -> list[int]:
        return self.__mask.editable_positions() if self.__mask else []

    def _digit_index_from_cursor(self, pos: int) -> int:
        idxs = self._editable_positions()
        return len([i for i in idxs if i < pos])

    def _cursor_from_digit_index(self, di: int) -> int:
        idxs = self._editable_positions()
        if not idxs:
            return 0
        di = max(0, min(di, len(idxs)))
        if di == len(idxs):
            return idxs[-1] + 1
        return idxs[di]

    def _apply_mask_after_text_change(self) -> None:
        if not self.__mask:
            return
        self.text = self.__mask.render(self.__digits)
        self.cursor = (self._cursor_from_digit_index(len(self.__digits)), 0)

    def insert_text(self, substring: str, from_undo=False):
        if not self.__mask:
            return super().insert_text(substring, from_undo=from_undo)
        digits_in = "".join(ch for ch in substring if ch.isdigit())
        if not digits_in:
            return
        cap = len(self._editable_positions())
        di = self._digit_index_from_cursor(self.cursor_col)
        before = self.__digits[:di]
        after = self.__digits[di:]
        newdigits = (before + digits_in + after)[:cap]
        self.__digits = newdigits
        self._apply_mask_after_text_change()

    def do_backspace(self, from_undo=False, mode="bkspc"):
        if not self.__mask:
            return super().do_backspace(from_undo=from_undo, mode=mode)
        if self.__digits:
            di = self._digit_index_from_cursor(self.cursor_col)
            remove_index = max(0, di - 1)
            self.__digits = (
                self.__digits[:remove_index] + self.__digits[remove_index + 1 :]
            )
            self._apply_mask_after_text_change()

    def _on_enter(self, *args):
        if self.validation_mode in ("on_enter", "on_focus_or_enter"):
            self.validate_all()

    def on_focus(self, instance, value: bool):
        super().on_focus(instance, value)
        if not value and self.validation_mode in ("on_focus", "on_focus_or_enter"):
            self.validate_all()

    def validate_all(self) -> bool:
        ok = True
        for v in self.__validators:
            if not v.validate(self.text):
                ok = False
                break
        self.is_valid = ok
        return ok

    # --- вспомогалки размеров иконок ---
    def _lead_size(self):
        ic = getattr(self, "_leading_icon", None)
        if ic and getattr(ic, "texture_size", None):
            return ic.texture_size
        return 0, 0

    def _trail_size(self):
        ic = getattr(self, "_trailing_icon", None)
        if ic and getattr(ic, "texture_size", None):
            return ic.texture_size
        return 0, 0

    # --- цвета через AliasProperty (KV читает root.*_rgba) ---
    def _get_fill_rgba(self):
        if self.mode != "filled":
            return self.theme_cls.transparentColor
        if not self.focus:
            base = (
                self.theme_cls.surfaceVariantColor
                if self.theme_bg_color == "Primary"
                else (self.fill_color_normal or self.theme_cls.surfaceVariantColor)
            )
        else:
            base = (
                self.theme_cls.surfaceVariantColor
                if self.theme_bg_color == "Primary"
                else (self.fill_color_focus or self.theme_cls.onSurfaceVariantColor)
            )
        return base

    fill_rgba = AliasProperty(
        _get_fill_rgba,
        None,
        bind=(
            "mode",
            "focus",
            "theme_bg_color",
            "fill_color_normal",
            "fill_color_focus",
        ),
    )

    def _get_active_rgba(self):
        if self.mode != "filled":
            return self.theme_cls.transparentColor
        col = (
            self.theme_cls.onSurfaceVariantColor
            if self.theme_line_color == "Primary"
            else (self.line_color_normal or self.theme_cls.onSurfaceVariantColor)
        )
        if self.focus:
            col = (
                self.theme_cls.primaryColor
                if self.theme_line_color == "Primary"
                else (self.line_color_focus or self.theme_cls.primaryColor)
            )
        if self.error:
            col = self._get_error_color()
        if self.disabled:
            col = self.theme_cls.disabledTextColor
        return col

    active_rgba = AliasProperty(
        _get_active_rgba,
        None,
        bind=(
            "mode",
            "focus",
            "error",
            "disabled",
            "theme_line_color",
            "line_color_normal",
            "line_color_focus",
        ),
    )

    def _get_outline_rgba(self):
        if self.mode == "filled":
            return self.theme_cls.transparentColor
        col = (
            (
                self.theme_cls.primaryColor
                if self.theme_line_color == "Primary"
                else (self.line_color_focus or self.theme_cls.primaryColor)
            )
            if self.focus
            else (
                self.theme_cls.outlineColor
                if self.theme_line_color == "Primary"
                else (self.line_color_normal or self.theme_cls.outlineColor)
            )
        )
        if self.error:
            col = self._get_error_color()
        if self.disabled:
            r, g, b, _ = self.theme_cls.onSurfaceColor
            col = [r, g, b, self.text_field_opacity_value_disabled_line]
        return col

    outline_rgba = AliasProperty(
        _get_outline_rgba,
        None,
        bind=(
            "mode",
            "focus",
            "error",
            "disabled",
            "theme_line_color",
            "line_color_normal",
            "line_color_focus",
        ),
    )

    def _get_text_rgba(self):
        if self.disabled:
            return self.theme_cls.disabled_hint_text_color
        if self.focus:
            if self.theme_text_color == "Custom" and self.text_color_focus:
                return self.text_color_focus
            return self.theme_cls.onSurfaceColor
        else:
            if self.theme_text_color == "Custom" and self.text_color_normal:
                return self.text_color_normal
            return self.theme_cls.onSurfaceVariantColor

    text_rgba = AliasProperty(
        _get_text_rgba,
        None,
        bind=(
            "disabled",
            "focus",
            "theme_text_color",
            "text_color_focus",
            "text_color_normal",
        ),
    )

    def _get_cursor_rgba(self):
        if self.focus and not self._cursor_blink:
            return (
                self._get_error_color() if self.error else self.theme_cls.primaryColor
            )
        return 0, 0, 0, 0

    cursor_rgba = AliasProperty(
        _get_cursor_rgba, None, bind=("focus", "_cursor_blink", "error")
    )

    # --- индикатор ---
    def _get_indicator_points(self):
        x, y, w = self.x, self.y, self.width
        off = dp(1) if self.focus else 0
        return [x + off, y, x - off + w, y]

    indicator_points = AliasProperty(
        _get_indicator_points, None, bind=("x", "y", "width", "focus")
    )

    # --- геометрия helper/hint/leading/trailing/maxlen ---
    def _get_helper_pos(self):
        x, y = self.x, self.y
        left = dp(16) if self.mode == "filled" else dp(12)
        return (x + left, y + self.helper_y_offset)

    helper_pos = AliasProperty(_get_helper_pos, None, bind=("x", "y", "mode"))

    def _get_helper_size(self):
        lab = getattr(self, "_helper_text_label", None)
        return lab.texture_size if (lab and lab.texture) else (0, 0)

    helper_size = AliasProperty(_get_helper_size, None, bind=("_helper_text_label",))

    def _get_leading_pos(self):
        w0, h0 = self._lead_size()
        if not (w0 and h0):
            return (0, 0)
        x = (
            self.x + (0 if self.mode != "outlined" else self.pad_leading_outlined)
            if self.mode != "filled"
            else (
                self.pad_leading_filled_noicon
                if not w0
                else self.pad_leading_filled_icon
            )
            + self.x
        )
        y = self.center_y - h0 / 2.0
        return x, y

    leading_pos = AliasProperty(
        _get_leading_pos, None, bind=("x", "center_y", "mode", "_leading_icon")
    )

    def _get_leading_size(self):
        return self._lead_size()

    leading_size = AliasProperty(_get_leading_size, None, bind=("_leading_icon",))

    def _get_trailing_pos(self):
        w1, h1 = self._trail_size()
        if not (w1 and h1):
            return 0, 0
        x = (self.x + self.width) - h1 - self.pad_trailing_right
        y = self.center_y - h1 / 2.0
        return x, y

    trailing_pos = AliasProperty(
        _get_trailing_pos, None, bind=("x", "width", "center_y", "_trailing_icon")
    )

    def _get_trailing_size(self):
        return self._trail_size()

    trailing_size = AliasProperty(_get_trailing_size, None, bind=("_trailing_icon",))

    def _get_maxlen_pos(self):
        lab = getattr(self, "_max_length_label", None)
        if lab and lab.texture:
            return (
                (self.x + self.width) - (lab.texture_size[0] + dp(16)),
                self.y - dp(18),
            )
        return 0, 0

    maxlen_pos = AliasProperty(
        _get_maxlen_pos, None, bind=("x", "y", "width", "_max_length_label")
    )

    def _get_maxlen_size(self):
        lab = getattr(self, "_max_length_label", None)
        return lab.texture_size if (lab and lab.texture) else (0, 0)

    maxlen_size = AliasProperty(_get_maxlen_size, None, bind=("_max_length_label",))

    def _get_hint_pos(self):
        hint = getattr(self, "_hint_text_label", None)
        if not (hint and hint.texture):
            return 0, 0
        lead_w, _ = self._lead_size()
        hx = self.x + (
            self.pad_left_base
            if not lead_w
            else lead_w + self.hint_gap_with_leading + self._hint_x
        )
        hy = (
            self.y
            + self.height
            + (hint.texture_size[1] / 2.0)
            - (self.height / 2.0)
            - self._hint_y
        )
        return (hx, hy)

    hint_pos = AliasProperty(
        _get_hint_pos,
        None,
        bind=(
            "x",
            "y",
            "width",
            "height",
            "_hint_x",
            "_hint_y",
            "_leading_icon",
            "_hint_text_label",
        ),
    )

    def _get_hint_size(self):
        hint = getattr(self, "_hint_text_label", None)
        return hint.texture_size if (hint and hint.texture) else (0, 0)

    hint_size = AliasProperty(_get_hint_size, None, bind=("_hint_text_label",))

    # --- padding ---
    def _get_padding_tuple(self):
        lead_w, _ = self._lead_size()
        if self.mode != "filled":
            left = self.pad_left_base if not lead_w else dp(42)
        else:
            left = self.pad_left_base if not lead_w else dp(52)

        trail_w, _ = self._trail_size()
        right = self.pad_right_base if not trail_w else trail_w + dp(28)

        top = (self.height / 2.0 - (self.line_height / 2.0) * len(self._lines)) + (
            dp(8) if self.mode == "filled" else 0
        )
        return left, top, right, 0

    padding_tuple = AliasProperty(
        _get_padding_tuple,
        None,
        bind=("height", "mode", "_leading_icon", "_trailing_icon", "_lines"),
    )

    # --- шрифты из темы ---
    def on_font_style(self, *_):
        self._apply_font_from_theme()

    def on_role(self, *_):
        self._apply_font_from_theme()

    def _apply_font_from_theme(self):
        fs = theme_font_styles[self.font_style][self.role]
        self.font_name = fs["font-name"]
        # Основной text font — как раньше; hint управляется hint_font_size отдельно
        self.font_size = fs["font-size"]

    def _mul_alpha(self, rgba, a: float):
        r, g, b, A = rgba
        return (r, g, b, A * a)

    def _get_helper_rgba(self):
        r, g, b, a = self.theme_cls.onSurfaceVariantColor
        return (r, g, b, a * self.helper_alpha)

    helper_rgba = AliasProperty(_get_helper_rgba, None, bind=("helper_alpha",))

    def _get_hint_rgba(self):
        base = (
            self._get_error_color()
            if self.error
            else (
                self.theme_cls.primaryColor
                if self.focus
                else self.theme_cls.onSurfaceVariantColor
            )
        )
        return self._mul_alpha(base, self.hint_alpha)

    hint_rgba = AliasProperty(
        _get_hint_rgba, None, bind=("focus", "error", "hint_alpha")
    )

    def _get_leading_rgba(self):
        ic = getattr(self, "_leading_icon", None)
        if not ic:
            return 0, 0, 0, 0
        if self.disabled:
            base = self.theme_cls.onSurfaceDisabledColor
        elif self.focus:
            base = (
                self.theme_cls.onSurfaceVariantColor
                if getattr(ic, "theme_icon_color", None) == "Primary"
                or not getattr(ic, "icon_color_focus", None)
                else ic.icon_color_focus
            )
        else:
            base = (
                self.theme_cls.onSurfaceVariantColor
                if getattr(ic, "theme_icon_color", None) == "Primary"
                or not getattr(ic, "icon_color_normal", None)
                else ic.icon_color_normal
            )
        return self._mul_alpha(base, self.leading_alpha)

    leading_rgba = AliasProperty(
        _get_leading_rgba,
        None,
        bind=("disabled", "focus", "leading_alpha", "_leading_icon"),
    )

    def _get_trailing_rgba(self):
        ic = getattr(self, "_trailing_icon", None)
        if not ic:
            return 0, 0, 0, 0
        if self.error:
            base = self._get_error_color()
        elif self.disabled:
            base = self.theme_cls.onSurfaceDisabledColor
        elif self.focus:
            base = (
                self.theme_cls.onSurfaceVariantColor
                if getattr(ic, "theme_icon_color", None) == "Primary"
                or not getattr(ic, "icon_color_focus", None)
                else ic.icon_color_focus
            )
        else:
            base = (
                self.theme_cls.onSurfaceVariantColor
                if getattr(ic, "theme_icon_color", None) == "Primary"
                or not getattr(ic, "icon_color_normal", None)
                else ic.icon_color_normal
            )
        return self._mul_alpha(base, self.trailing_alpha)

    trailing_rgba = AliasProperty(
        _get_trailing_rgba,
        None,
        bind=("error", "disabled", "focus", "trailing_alpha", "_trailing_icon"),
    )

    def _get_maxlen_rgba(self):
        base = (
            self._get_error_color()
            if self.error
            else self.theme_cls.onSurfaceVariantColor
        )
        return self._mul_alpha(base, self.maxlen_alpha)

    maxlen_rgba = AliasProperty(_get_maxlen_rgba, None, bind=("error", "maxlen_alpha"))

    # ВАЖНО: привязываем font_size хинта к hint_font_size без texture_update()
    def on_hint_font_size(self, *_):
        lbl = getattr(self, "_hint_text_label", None)
        if lbl:
            lbl.font_size = self.hint_font_size  # Kivy сам обновит texture на кадре


class MVCTextField(MVCDefaultTextFieldView):
    _helper_text_label: ObjectProperty[MDTextFieldHelperText] = ObjectProperty()
    _hint_text_label: ObjectProperty[MDTextFieldHintText] = ObjectProperty()
    _leading_icon: ObjectProperty[MDTextFieldLeadingIcon] = ObjectProperty()
    _trailing_icon: ObjectProperty[MDTextFieldTrailingIcon] = ObjectProperty()
    _max_length_label: ObjectProperty[MDTextFieldMaxLengthText] = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tokens = StyleTokens(self.theme_cls)
        self._renderer = Renderer(self)
        self._render_scheduled = False

        self._roles = RoleRegistry()
        self._roles.register("indicator", rule_indicator)
        self._roles.register("hint_text", rule_hint_text)
        self._roles.register("helper_text", rule_helper_text)
        self._roles.register("icons", rule_icons)
        self._roles.register("max_length", rule_max_length)

    def _schedule_render(self) -> None:
        if not self._render_scheduled:
            return
        self._render_scheduled = True
        Clock.schedule_once(self._do_render, 0)

    def _do_render(self, _dt):
        try:
            self.render()
        finally:
            self._render_scheduled = False

    def render(self) -> None:
        objs = SimpleNamespace(
            leading_icon=getattr(self, "_leading_icon", None),
            trailing_icon=getattr(self, "_trailing_icon", None),
            hint_label=getattr(self, "_hint_text_label", None),
            helper_label=getattr(self, "_helper_text_label", None),
            max_length_label=getattr(self, "_max_length_label", None),
        )
        patch = self._roles.build_patch(self, self._tokens, objs=objs)
        self._renderer.apply(patch)

    # обработчики → только планирование рендера
    def on_focus(self, instance, focus: bool) -> None:
        self._schedule_render()

    def on_disabled(self, instance, disabled: bool) -> None:
        super().on_disabled(instance, disabled)
        self._schedule_render()

    def on_error(self, instance, error: bool) -> None:
        self._schedule_render()

    def on_text(self, instance, value: str) -> None:
        self._schedule_render()

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
