from __future__ import annotations

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.graphics.transformation import Matrix
from kivy.uix.widget import Widget

from kivymd.app import MDApp
from mvckivy.mvc_base.base_app_model import BaseAppModel
from mvckivy.uix.dialog import MKVDialog

from kivymd.uix.behaviors import HoverBehavior
from kivymd.uix.list import (
    MDListItem,
    MDListItemLeadingIcon,
    MDListItemHeadlineText,
)
from kivymd.uix.button import MDButton

from mvckivy.utils.builder import MVCBuilder


def _vpad(pad) -> float:
    if isinstance(pad, (list, tuple)):
        return float(pad[1] + pad[3])
    return float(pad) * 2.0


# -----------------------------------------------------------------------------
# МИКСИН: инвертируем touch в КООРДИНАТАХ РОДИТЕЛЯ интерактивного виджета
# -----------------------------------------------------------------------------
class ScaleAwareInputMixin:
    """Инвертирует координаты события относительно центра диалога (scale_provider)
    на время on_touch_down/move/up, в системе координат РОДИТЕЛЯ виджета.
    """

    scale_provider = ObjectProperty(allownone=True)  # диалог с render_scale

    def _push_inverse_scale_for_parent_space(self, touch) -> bool:
        sp = self.scale_provider
        parent = self.parent
        if not sp or not parent:
            return False

        s = float(getattr(sp, "render_scale", 1.0) or 1.0)
        if s == 1.0:
            return False

        # центр диалога в координатах окна (тот же origin, что в KV Scale)
        ox, oy = sp.to_window(sp.center_x, sp.center_y)

        m = (
            Matrix()
            .translate(ox, oy, 0)
            .multiply(Matrix().scale(1.0 / s, 1.0 / s, 1.0))
            .multiply(Matrix().translate(-ox, -oy, 0))
        )

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
# СПИСОК: hover (в оконных координатах) + корректный touch через миксин
# -----------------------------------------------------------------------------
class HoverScaledListItem(ScaleAwareInputMixin, MDListItem):
    """MDListItem с корректным hover/press при визуальном Scale у диалога."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, "detect_visible"):
            self.detect_visible = False  # внутри модалки можно смело отключить

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
        # нативная логика hover
        return HoverBehavior.on_mouse_update(self, window, pos)


# -----------------------------------------------------------------------------
# КНОПКА: hover тоже считаем через ПРОСТРАНСТВО РОДИТЕЛЯ (как у touch)
# -----------------------------------------------------------------------------


class ScaledMDButton(ScaleAwareInputMixin, MDButton):
    def on_mouse_update(self, window, pos):
        # 1) Виджет не привязан к окну – ничего не делаем
        if not self.get_root_window():
            return

        # 2) ВСЕГДА работаем с координатами окна -> локальные координаты виджета
        #    to_widget уже учитывает Scatter/Rotate/Translate предков.
        lx, ly = self.to_widget(*pos)

        # 3) Базовая проверка попадания в саму кнопку
        if not self.collide_point(lx, ly):
            self.hovering = False
            self.enter_point = None
            if self.hover_visible:
                self.hover_visible = False
                self.dispatch("on_leave")
            return

        # 4) Если уже в режиме hovering — ок
        if self.hovering:
            return

        self.hovering = True
        self.hover_visible = True

        # 5) Проверка "видимости" по пути к корню:
        #    на каждом уровне переводим координату окна -> локальные координаты ЭТОГО уровня
        widget: Widget = self
        parent: Widget | None = widget.parent

        while parent is not None:
            plx, ply = parent.to_widget(*pos)  # pos всегда в Window-координатах!
            if not parent.collide_point(plx, ply):
                self.hover_visible = False
                break
            widget = parent
            parent = widget.parent

        # 6) Если невидимы по дереву – выходим
        if not self.hover_visible:
            self.hovering = False
            self.enter_point = None
            return

        # 7) Проверка перекрытий на верхнем уровне: смотрим сиблингов у корня ветки
        #    Здесь `widget` — первый виджет ветки под общим родителем `parent`.
        #    Чтобы дойти до настоящего корня окна, поднимались в while,
        #    следовательно сейчас parent == None, а widget — верхний контейнер ветки.
        #    В большинстве случаев это child окна/корневого layout'а.
        top_container = widget
        if top_container.parent is not None:
            siblings = top_container.parent.children
            for child in siblings:
                if child is top_container:
                    break  # Наше поддерево выше всех, значит видно
                # Проверяем перекрывающих "старших" соседей по Z-упорядочению
                clx, cly = child.to_widget(*pos)
                if child.collide_point(clx, cly):
                    self.hover_visible = False
                    break

        if self.hover_visible:
            self.enter_point = pos  # логично хранить исходные Window-координаты
            self.dispatch("on_enter")
        else:
            self.hovering = False
            self.enter_point = None


# -----------------------------------------------------------------------------
# ДИАЛОГИ
# -----------------------------------------------------------------------------
class AdaptiveListDialog(MKVDialog):
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
        # видимый предел
        target_w_vis = min(self.design_width, w * self.occupy_ratio_w)
        target_h_vis = min(self.design_height, h * self.occupy_ratio_h)

        # масштаб включаем, если по ВЫСОТЕ не помещаемся
        if target_h_vis < self.design_height:
            s = max(self.min_scale, target_h_vis / float(self.design_height or 1.0))
            self.render_scale = s
            geom_h = self.design_height  # геометрия — «дизайнерская»
            geom_w = target_w_vis / s  # компенсируем ширину
        else:
            self.render_scale = 1.0
            geom_h = self.design_height
            geom_w = target_w_vis

        # центрируем диалог
        self.size = (geom_w, geom_h)
        self.pos = ((w - self.width) / 2.0, (h - self.height) / 2.0)

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

        # авто-высота текстов
        for lab in (head, sup):
            lab.text_size = (lab.width, None)
            lab.adaptive_height = True

        base_pad = dp(24)

        # сначала выдаём высоту под список (чтобы он не «прыгнул»)
        fixed_h = float(icon.height + head.height + sup.height + btn.height)
        spacing = float(dp(16)) * 4.0
        avail_for_list = max(0.0, self.height - 2 * base_pad - fixed_h - spacing)

        content.size_hint_y = None
        content.height = avail_for_list
        scroll.size_hint_y = None
        scroll.height = avail_for_list

        # теперь сколько реально заняли (с учётом списка) и центрируем блок
        used = fixed_h + spacing + content.height
        extra = max(0.0, self.height - used - 2 * base_pad)

        top = base_pad + extra / 2.0
        bot = base_pad + extra / 2.0
        # выставляем симметричные паддинги: [left, top, right, bottom]
        self.padding = [base_pad, top, base_pad, bot]

    def on_save(self):
        self.dismiss()


class AppModel(BaseAppModel):
    pass


class DemoApp(MDApp):
    dialog_list: AdaptiveListDialog | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = AppModel()

    def build(self):
        MVCBuilder.load_libs_kv_files()
        return Builder.load_file("md_list.kv")

    def open_list_dialog(self, count=40):
        items = [f"Элемент {i+1}" for i in range(count)]
        self.dialog_list = AdaptiveListDialog(items=items)
        self.dialog_list.open()


if __name__ == "__main__":
    DemoApp().run()
