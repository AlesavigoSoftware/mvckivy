from __future__ import annotations

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.graphics.transformation import Matrix

from kivymd.app import MDApp
from mvckivy.base_mvc.base_app_model import BaseAppModel
from mvckivy.uix.dialog import MDAdaptiveDialog

from kivymd.uix.behaviors import HoverBehavior
from kivymd.uix.list import (
    MDListItem,
    MDListItemLeadingIcon,
    MDListItemHeadlineText,
)
from kivymd.uix.button import MDButton


def _vpad(pad) -> float:
    if isinstance(pad, (list, tuple)):
        return float(pad[1] + pad[3])
    return float(pad) * 2.0


# -----------------------------------------------------------------------------
# МИКСИН ДЛЯ ИНТЕРАКТИВНЫХ ДЕТЕЙ (кнопки/айтемы): корректирует touch в coords родителя
# -----------------------------------------------------------------------------
class ScaleAwareInputMixin:
    """
    Инвертирует координаты события относительно центра scale_provider (диалога)
    на время on_touch_down/move/up, **в системе координат родителя виджета**.
    """

    scale_provider = ObjectProperty(allownone=True)  # диалог с render_scale

    def _push_inverse_scale_for_parent_space(self, touch) -> bool:
        sp = self.scale_provider
        parent = self.parent
        if not sp or not parent:
            return False

        s = float(getattr(sp, "render_scale", 1.0) or 1.0)
        if s == 1.0:
            return False  # масштаб не активен -> инверсия не нужна

        # 1) центр диалога в координатах окна (тот же origin, что в KV Scale)
        ox, oy = sp.to_window(sp.center_x, sp.center_y)

        # 2) обратный масштаб в оконных координатах
        m = Matrix().translate(ox, oy, 0)
        m = m.multiply(Matrix().scale(1.0 / s, 1.0 / s, 1.0))
        m = m.multiply(Matrix().translate(-ox, -oy, 0))

        # 3) переводим точку: РОДИТЕЛЬ -> ОКНО -> (инверсия) -> РОДИТЕЛЬ
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


# -----------------------------------------------------------------------------
# АЙТЕМ СПИСКА: hover правим ДО HoverBehavior + корректный touch через миксин
# -----------------------------------------------------------------------------
class HoverScaledListItem(ScaleAwareInputMixin, MDListItem):
    """
    MDListItem с корректным hover/press при визуальном Scale у диалога.
    - on_mouse_update: корректируем позицию курсора в координатах окна и
      передаём её в HoverBehavior (стабильно даже при быстрых перемещениях).
    - on_touch_*: берём из миксина ScaleAwareInputMixin (coords родителя).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, "detect_visible"):
            self.detect_visible = False  # внутри модалки безопасно отключить

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


# -----------------------------------------------------------------------------
# КНОПКА С ПОДДЕРЖКОЙ МАСШТАБИРОВАНИЯ
# -----------------------------------------------------------------------------
class ScaledMDButton(ScaleAwareInputMixin, MDButton):
    """MDButton с корректной зоной on_press при визуальном Scale диалога."""

    pass


# -----------------------------------------------------------------------------
# ДИАЛОГИ: Scale включается ТОЛЬКО при вертикальном ограничении
# -----------------------------------------------------------------------------
class AdaptiveListDialog(MDAdaptiveDialog):
    """Диалог со списком. Масштаб 1→0.5 включается только при vertical-лимите."""

    design_width = NumericProperty(dp(560))
    design_height = NumericProperty(dp(640))
    occupy_ratio_w = NumericProperty(0.70)  # <= 70% окна по ширине
    occupy_ratio_h = NumericProperty(0.80)  # <= 80% окна по высоте

    render_scale = NumericProperty(1.0)  # используется в KV Scale
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
        # целевые видимые размеры (то, что должно получиться на экране)
        target_w_vis = min(self.design_width, w * self.occupy_ratio_w)
        target_h_vis = min(self.design_height, h * self.occupy_ratio_h)

        # масштаб включаем только если по ВЫСОТЕ не помещаемся
        if target_h_vis < self.design_height:
            s = max(self.min_scale, target_h_vis / float(self.design_height or 1.0))
            self.render_scale = s

            # геометрические размеры виджета до масштабирования
            geom_h = self.design_height  # высоту держим "дизайнерской"
            geom_w = target_w_vis / s  # компенсируем горизонталь
        else:
            self.render_scale = 1.0
            geom_h = self.design_height
            geom_w = target_w_vis

        # применяем геометрию и центрируем
        self.size = (geom_w, geom_h)
        self.pos = ((w - self.width) / 2.0, (h - self.height) / 2.0)

        # перераскладка внутреннего контента (как раньше)
        self._reflow()

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

        # перенос текста
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

    def on_save(self):
        self.dismiss()


class SuccessGSConnDialog(MDAdaptiveDialog):
    """Простой диалог: масштаб 1→0.5 активируется только при вертикальном лимите."""

    design_width = NumericProperty(dp(560))
    design_height = NumericProperty(dp(400))
    occupy_ratio_w = NumericProperty(0.70)
    occupy_ratio_h = NumericProperty(0.80)
    render_scale = NumericProperty(1.0)
    min_scale = NumericProperty(0.5)

    def on_open(self, *args):
        self._update_size(Window, Window.width, Window.height)
        Window.bind(on_resize=self._update_size)

    def on_dismiss(self, *args):
        try:
            Window.unbind(on_resize=self._update_size)
        except Exception:
            pass

    def _update_size(self, _win, w, h):
        # целевые видимые размеры (то, что должно получиться на экране)
        target_w_vis = min(self.design_width, w * self.occupy_ratio_w)
        target_h_vis = min(self.design_height, h * self.occupy_ratio_h)

        # масштаб включаем только если по ВЫСОТЕ не помещаемся
        if target_h_vis < self.design_height:
            s = max(self.min_scale, target_h_vis / float(self.design_height or 1.0))
            self.render_scale = s

            # геометрические размеры виджета до масштабирования
            geom_h = self.design_height  # высоту держим "дизайнерской"
            geom_w = target_w_vis / s  # компенсируем горизонталь
        else:
            self.render_scale = 1.0
            geom_h = self.design_height
            geom_w = target_w_vis

        # применяем геометрию и центрируем
        self.size = (geom_w, geom_h)
        self.pos = ((w - self.width) / 2.0, (h - self.height) / 2.0)

        # перераскладка внутреннего контента (как раньше)
        self._reflow()

    def on_save(self):
        self.dismiss()

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

        # перенос текста
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


# -----------------------------------------------------------------------------
# APP
# -----------------------------------------------------------------------------
class AppModel(BaseAppModel):
    pass


class DemoApp(MDApp):
    dialog_list: AdaptiveListDialog | None = None
    dialog_success: SuccessGSConnDialog | None = None

    def build(self):
        # ваш общий dialog.kv с контейнерами MDAdaptiveDialog
        Builder.load_file(r"/src/mvckivy\uix\dialog\dialog.kv")
        self.model = AppModel()
        return Builder.load_file("md_list.kv")

    def open_list_dialog(self, count=40):
        items = [f"Элемент {i+1}" for i in range(count)]
        self.dialog_list = AdaptiveListDialog(items=items)
        self.dialog_list.open()

    def open_success_dialog(self):
        if not self.dialog_success:
            self.dialog_success = SuccessGSConnDialog()
        self.dialog_success.open()


if __name__ == "__main__":
    DemoApp().run()
