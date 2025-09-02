from __future__ import annotations

import logging
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import (
    NumericProperty,
    ListProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.graphics.transformation import Matrix

from kivymd.app import MDApp
from mvckivy.uix.dialog import MDAdaptiveDialog

from kivymd.uix.behaviors import HoverBehavior
from kivymd.uix.list import (
    MDListItem,
    MDListItemLeadingIcon,
    MDListItemHeadlineText,
)
from kivymd.uix.button import MDButton
from mvckivy.utils.builder import MVCBuilder

logging.basicConfig(level=logging.INFO)


# ── Заглушка модели ──────────────────────────────────────────────────────────
class DummyModel:
    def bind(self, **kwargs):
        logging.info("DummyModel.bind: %s", ", ".join(kwargs.keys()))

    def unbind(self, **kwargs):
        logging.info("DummyModel.unbind: %s", ", ".join(kwargs.keys()))

    def __getattr__(self, name):
        logging.info("DummyModel.__getattr__(%s) -> None", name)
        return None


# ── Вспом. утилита ───────────────────────────────────────────────────────────
def _vpad(pad) -> float:
    if isinstance(pad, (list, tuple)):
        return float(pad[1] + pad[3])
    return float(pad) * 2.0


# ── Миксин для корректного тача при Scale (детям диалога) ────────────────────
class ScaleAwareInputMixin:
    scale_provider = ObjectProperty(allownone=True)

    def _push_inverse_scale_for_parent_space(self, touch) -> bool:
        sp = self.scale_provider
        parent = self.parent
        if not sp or not parent:
            return False

        s = float(getattr(sp, "render_scale", 1.0) or 1.0)
        if s == 1.0:
            return False

        ox, oy = sp.to_window(sp.center_x, sp.center_y)
        m = Matrix().translate(ox, oy, 0)
        m = m.multiply(Matrix().scale(1.0 / s, 1.0 / s, 1.0))
        m = m.multiply(Matrix().translate(-ox, -oy, 0))

        def _parent_space_inverse(x, y, _m=m, _p=parent):
            wx, wy = _p.to_window(x, y)
            cx, cy, _ = _m.transform_point(wx, wy, 0)
            return _p.to_widget(cx, cy)

        touch.push()
        touch.apply_transform_2d(_parent_space_inverse)
        return True

    def on_touch_down(self, touch):
        pushed = self._push_inverse_scale_for_parent_space(touch)
        try:
            return super().on_touch_down(touch)
        finally:
            if pushed:
                touch.pop()

    def on_touch_move(self, touch):
        pushed = self._push_inverse_scale_for_parent_space(touch)
        try:
            return super().on_touch_move(touch)
        finally:
            if pushed:
                touch.pop()

    def on_touch_up(self, touch):
        pushed = self._push_inverse_scale_for_parent_space(touch)
        try:
            return super().on_touch_up(touch)
        finally:
            if pushed:
                touch.pop()


# ── Ховер-айтем списка (оставлен как пример) ────────────────────────────────
class HoverScaledListItem(ScaleAwareInputMixin, MDListItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, "detect_visible"):
            self.detect_visible = False

    def on_mouse_update(self, window, pos):
        sp = self.scale_provider
        if sp is not None:
            s = float(getattr(sp, "render_scale", 1.0) or 1.0)
            if s != 1.0:
                ox, oy = sp.to_window(sp.center_x, sp.center_y)
                m = Matrix().translate(ox, oy, 0)
                m = m.multiply(Matrix().scale(1.0 / s, 1.0 / s, 1.0))
                m = m.multiply(Matrix().translate(-ox, -oy, 0))
                pos = m.transform_point(pos[0], pos[1], 0)[:2]
        return HoverBehavior.on_mouse_update(self, window, pos)


# ── Кнопка с учётом масштаба ────────────────────────────────────────────────
class ScaledMDButton(ScaleAwareInputMixin, MDButton):
    pass


# ── Интерфейс внешнего валидатора ───────────────────────────────────────────
class InputValidator:
    """Базовый протокол: у валидатора должен быть единственный метод validate()."""

    def validate(self, text: str) -> bool:
        raise NotImplementedError


class NumberRangeValidator(InputValidator):
    def __init__(self, min_value: int, max_value: int):
        self.min = int(min_value)
        self.max = int(max_value)

    def validate(self, text: str) -> bool:
        t = text.strip()
        if not t.isdigit():
            return False
        n = int(t)
        return self.min <= n <= self.max


from kivymd.uix.label import MDIcon
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.font_definitions import theme_font_styles
import logging


from mvckivy.uix.text_field import (
    MVCTextField,
    MDTextFieldLeadingIcon,
    MDTextFieldTrailingIcon,
)


class DialogPatchedTextField(MVCTextField):
    """
    Устойчивый к диалогам MDTextField.
    - Внешняя валидация: input_validator.validate(str)->bool
    - Чинит hint/helper + ИКОНКИ. Если у штатной иконки нет текстуры,
      рисует поверх прокси-MDIcon (не перехватывает события).
    """

    input_validator = ObjectProperty(allownone=True)
    error_message = StringProperty("")

    # --- валидация ---
    def run_validation(self):
        ok = True
        if self.input_validator:
            try:
                ok = bool(self.input_validator.validate(self.text))
            except Exception as e:
                logging.info("Validator error: %s", e)
                ok = False
        self.error = not ok
        self.helper_text = (
            self.error_message
            if self.error_message
            else ("Недопустимое значение" if self.error else "")
        )
        self.helper_text_mode = "on_error"

    def on_text(self, *_):
        self.run_validation()
        Clock.schedule_once(self._late_layout, 0)

    # --- жизненный цикл ---
    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        Clock.schedule_once(self._late_mount, 0)

    def on_focus(self, instance, focus):
        super().on_focus(instance, focus)
        Clock.schedule_once(self._late_layout, 0)

    def on_size(self, *_):
        Clock.schedule_once(self._late_layout, 0)

    # --- прокси-иконки (если базовые пустые) ---
    _leading_proxy: MDIcon | None = None
    _trailing_proxy: MDIcon | None = None

    def _ensure_icon_proxy(self, side: str):
        """Покажем прокси-иконку, если штатная не отрисовалась."""
        icon_widget = getattr(self, f"_{side}_icon", None)
        # живой текстуры нет -> нужна прокси
        needs_proxy = not icon_widget or not getattr(icon_widget, "texture", None)

        proxy_attr = f"_{side}_proxy"
        proxy = getattr(self, proxy_attr, None)

        if needs_proxy:
            # создать/обновить прокси
            if not proxy:
                # имя иконки берём из декларативной
                icon_name = getattr(icon_widget, "icon", "") if icon_widget else ""
                if not icon_name:
                    return  # нечего рисовать
                proxy = MDIcon(
                    icon=icon_name,
                    theme_icon_color="Custom",
                    icon_color=self.theme_cls.onSurfaceVariantColor,
                    size_hint=(None, None),
                    size=(dp(20), dp(20)),
                    disabled=True,  # не перехватывает инпут
                    opacity=1,
                )
                # поверх содержимого поля
                self.add_widget(proxy)
                setattr(self, proxy_attr, proxy)

            # позиция прокси
            def _place(*_):
                if side == "leading":
                    proxy.x = self.x + dp(12)
                else:  # trailing
                    proxy.right = self.right - dp(12)
                proxy.center_y = self.center_y

            _place()
            self.bind(pos=_place, size=_place)
        else:
            # штатная иконка ожила -> уберём прокси
            if proxy:
                self.remove_widget(proxy)
                setattr(self, proxy_attr, None)

    # --- подготовка после монтирования ---
    def _late_mount(self, *_):
        # захватим ссылки на декларативные иконки, если их ещё нет
        for ch in self.children[:]:
            if (
                isinstance(ch, MDTextFieldLeadingIcon)
                and getattr(self, "_leading_icon", None) is None
            ):
                self._leading_icon = ch
            elif (
                isinstance(ch, MDTextFieldTrailingIcon)
                and getattr(self, "_trailing_icon", None) is None
            ):
                self._trailing_icon = ch

        # первый/второй проход
        self._late_layout()
        Clock.schedule_once(self._late_layout, 0)

    # --- повторная раскладка/перекраска ---
    def _late_layout(self, *_):
        # helper text
        if getattr(self, "_helper_text_label", None):
            group = self.canvas.before.get_group("helper-text-color")
            if group:
                color = (
                    self.theme_cls.transparentColor
                    if self._helper_text_label.mode == "on_focus" and not self.focus
                    else (
                        self._get_error_color()
                        if self.error
                        else self.theme_cls.onSurfaceVariantColor
                    )
                )
                self.set_texture_color(self._helper_text_label, group[0], color)

        # ИКОНКИ: сначала попытаемся использовать штатные, иначе включаем прокси
        for side in ("leading", "trailing"):
            self._ensure_icon_proxy(side)

        # floating hint
        hint = getattr(self, "_hint_text_label", None)
        lead = getattr(self, "_leading_icon", None)
        lead_w = 0
        if lead and getattr(lead, "texture_size", None):
            lead_w = lead.texture_size[0] or 0
        # если используем прокси-иконку, учтём её ширину тоже
        if not lead_w and self._leading_proxy:
            lead_w = self._leading_proxy.width

        if hint:
            if self.focus or self.text:
                # поднятое состояние
                y = 0 if self.mode != "outlined" else dp(-14)
                if self.mode == "outlined":
                    x = -(lead_w + dp(12)) if lead_w else 0  # ВАЖНО: без иконки x=0
                else:
                    x = -(lead_w - dp(24))
                self.set_pos_hint_text(y, x)

                hint.font_size = theme_font_styles[hint.font_style]["small"][
                    "font-size"
                ]
                hint.texture_update()
                self.set_hint_text_font_size()
                if self.mode == "outlined":
                    self.set_space_in_line(dp(14), hint.texture_size[0] + dp(18))
            else:
                if self.mode == "outlined":
                    self.set_space_in_line(dp(32), dp(32))
                hint.font_size = theme_font_styles[hint.font_style]["large"][
                    "font-size"
                ]
                hint.texture_update()
                self.set_hint_text_font_size()
                self.set_pos_hint_text(
                    (self.height / 2) - (hint.texture_size[1] / 2),
                    0,
                )

        self.canvas.ask_update()


# ── Диалог ввода числа ──────────────────────────────────────────────────────
class NumberInputDialog(MDAdaptiveDialog):
    """Диалог ввода числа (0..65556). Масштаб включается только при вертикальном лимите."""

    design_width = NumericProperty(dp(480))
    design_height = NumericProperty(dp(280))
    occupy_ratio_w = NumericProperty(0.70)
    occupy_ratio_h = NumericProperty(0.80)
    render_scale = NumericProperty(1.0)
    min_scale = NumericProperty(0.5)

    on_submit = ObjectProperty(allownone=True)

    def on_open(self, *args):
        self._update_size(Window, Window.width, Window.height)
        Window.bind(on_resize=self._update_size)

    def on_dismiss(self, *args):
        try:
            Window.unbind(on_resize=self._update_size)
        except Exception:
            pass

    def _update_size(self, _win, w, h):
        target_w_vis = min(self.design_width, w * self.occupy_ratio_w)
        target_h_vis = min(self.design_height, h * self.occupy_ratio_h)
        if target_h_vis < self.design_height:
            s = max(self.min_scale, target_h_vis / float(self.design_height or 1.0))
            self.render_scale = s
            geom_h = self.design_height
            geom_w = target_w_vis / s
        else:
            self.render_scale = 1.0
            geom_h = self.design_height
            geom_w = target_w_vis
        self.size = (geom_w, geom_h)
        self.pos = ((w - self.width) / 2.0, (h - self.height) / 2.0)

    def accept(self):
        field: DialogPatchedTextField = self.ids.port_field
        field.run_validation()
        if field.error:
            return
        value = int(field.text)
        if self.on_submit:
            logging.info("NumberInputDialog accept -> %d", value)
            self.on_submit(value)
        self.dismiss()


# ── (опционально) диалог со списком из прежних задач ────────────────────────
class AdaptiveListDialog(MDAdaptiveDialog):
    design_width = NumericProperty(dp(560))
    design_height = NumericProperty(dp(640))
    occupy_ratio_w = NumericProperty(0.70)
    occupy_ratio_h = NumericProperty(0.80)
    render_scale = NumericProperty(1.0)
    min_scale = NumericProperty(0.5)
    items = ListProperty([])

    def on_open(self, *args):
        self._update_size(Window, Window.width, Window.height)
        Window.bind(on_resize=self._update_size)
        Clock.schedule_once(lambda *_: (self._fill_list_once(), self._reflow()), 0)

    def on_dismiss(self, *args):
        try:
            Window.unbind(on_resize=self._update_size)
        except Exception:
            pass

    def _fill_list_once(self):
        lst = self.ids.get("items_list")
        if lst is None or getattr(self, "_list_filled", False):
            return
        for txt in self.items:
            it = HoverScaledListItem(scale_provider=self)
            it.add_widget(MDListItemLeadingIcon(icon="format-list-bulleted"))
            head = MDListItemHeadlineText(text=txt)
            head.font_style, head.role = "Body", "medium"
            it.add_widget(head)
            lst.add_widget(it)
        self._list_filled = True
        self._reflow()

    def _update_size(self, _win, w, h):
        target_w_vis = min(self.design_width, w * self.occupy_ratio_w)
        target_h_vis = min(self.design_height, h * self.occupy_ratio_h)
        if target_h_vis < self.design_height:
            s = max(self.min_scale, target_h_vis / float(self.design_height or 1.0))
            self.render_scale = s
            geom_h = self.design_height
            geom_w = target_w_vis / s
        else:
            self.render_scale = 1.0
            geom_h = self.design_height
            geom_w = target_w_vis
        self.size = (geom_w, geom_h)
        self.pos = ((w - self.width) / 2.0, (h - self.height) / 2.0)

    def _reflow(self):
        ids = self.ids
        icon = ids.get("icon_c")
        head = ids.get("headline_c")
        sup = ids.get("support_c")
        btn = ids.get("buttons_c")
        content = ids.get("content_c")
        scroll = ids.get("scroll")
        if not all((icon, head, sup, btn, content, scroll)):
            return
        for lab in (head, sup):
            lab.text_size = (lab.width, None)
            lab.adaptive_height = True
        fixed_h = float(icon.height + head.height + sup.height + btn.height)
        pad_v = _vpad(self.padding)
        spacing = float(dp(16)) * 4.0
        free_h = max(0.0, self.height - fixed_h - pad_v - spacing)
        content.size_hint_y = None
        content.height = free_h
        scroll.size_hint_y = None
        scroll.height = free_h


# ── Приложение ───────────────────────────────────────────────────────────────
class DemoApp(MDApp):
    # держим экземпляр валидатора, чтобы удобно прокинуть в KV
    number_validator = NumberRangeValidator(0, 65556)

    def build(self):
        # ВАЖНО: загружаем KV из подключенных библиотек (как просили)
        MVCBuilder().load_libs_kv_files()

        # заглушка модели, чтобы mvckivy-behaviors не падали
        self.model = DummyModel()

        return Builder.load_file("md_dialog.kv")

    def open_number_dialog(self):
        dlg = NumberInputDialog()

        def _log_positions(*_):
            tf = dlg.ids.port_field
            if getattr(tf, "_hint_text_label", None):
                hx, hy = tf._hint_text_label.x, tf._hint_text_label.y
                wx, wy = tf.to_window(tf.x, tf.y)
                logging.info(
                    "TF pos=(%.1f,%.1f) win=(%.1f,%.1f) hint=(%.1f,%.1f) focus=%s",
                    tf.x,
                    tf.y,
                    wx,
                    wy,
                    hx,
                    hy,
                    tf.focus,
                )

        dlg.bind(on_open=lambda *_: Clock.schedule_once(_log_positions, 0))
        dlg.open()


if __name__ == "__main__":
    DemoApp().run()
