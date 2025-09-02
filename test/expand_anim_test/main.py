from __future__ import annotations

from typing import Callable, Optional

from kivy.animation import Animation
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
    ListProperty,
)
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stencilview import StencilView
from kivy.uix.widget import Widget

from kivymd.app import MDApp
from kivymd.uix.card import MDCard


KV = """
#:import dp kivy.metrics.dp

<ExpandingCard>:
    size_hint: None, None
    height: dp(140)
    width: root.animated_width

    MDCard:
        id: _card
        pos: root.pos
        size: root.size
        style: "outlined"
        radius: [dp(16)]
        md_bg_color: app.theme_cls.primaryContainerColor
        line_color: app.theme_cls.primaryColor
        padding: dp(12)

        MDBoxLayout:
            orientation: "vertical"
            spacing: dp(8)

            MDLabel:
                text: "Раскрывающаяся карточка"
                adaptive_height: True
                bold: True

            MDLabel:
                text: "По умолчанию width=0, затем анимация до целевой ширины.\\nКнопка ниже — toggle."
                theme_text_color: "Secondary"
                adaptive_height: True

            MDButton:
                on_release: root.toggle()

                MDButtonText:
                    text: "Переключить состояние"

                MDButtonIcon:
                    icon: "arrow-collapse-horizontal" if root.expanded else "arrow-expand-horizontal"


<DraggableCard>:
    size_hint_y: None
    height: self.minimum_height
    radius: [dp(14)]
    style: "elevated"
    line_color: app.theme_cls.primaryColor if root.is_drag_over else app.theme_cls.outlineColor
    md_bg_color: app.theme_cls.surfaceColor
    padding: dp(12)
    ripple_behavior: True

    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(6)
        adaptive_height: True
        MDLabel:
            text: root.title
            bold: True
            adaptive_height: True
        MDLabel:
            text: root.subtitle
            theme_text_color: "Secondary"
            adaptive_height: True


Screen:
    # Основной вертикальный лэйаут
    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(12)
        padding: dp(12)
        md_bg_color: app.theme_cls.backgroundColor

        # Ряд с тремя колонками
        MDBoxLayout:
            id: row
            spacing: dp(12)
            padding: dp(6)

            # Левая колонка (тянется)
            MDBoxLayout:
                id: left_col
                orientation: "vertical"
                spacing: dp(12)
                size_hint_x: 1

                DraggableCard:
                    id: lc1
                    title: "Соседний блок A1"
                    subtitle: "Перетащи меня на любую карточку"
                DraggableCard:
                    id: lc2
                    title: "Соседний блок A2"
                    subtitle: "Можно менять местами с правыми"

            # Средняя колонка (ширина = ширине карточки)
            MDBoxLayout:
                id: middle_col
                orientation: "vertical"
                spacing: dp(12)
                size_hint_x: None
                width: max(expanding_card.animated_width, dp(1))

                Widget:
                    size_hint_y: None
                    height: dp(4)

                ExpandingCard:
                    id: expanding_card

                Widget:
                    size_hint_y: None
                    height: dp(4)

            # Правая колонка (тянется)
            MDBoxLayout:
                id: right_col
                orientation: "vertical"
                spacing: dp(12)
                size_hint_x: 1

                DraggableCard:
                    id: rc1
                    title: "Соседний блок B1"
                    subtitle: "Drag & drop со снапом"
                DraggableCard:
                    id: rc2
                    title: "Соседний блок B2"
                    subtitle: "Поддержка обмена столбцами"

        # Внешние кнопки управления
        MDBoxLayout:
            size_hint_y: None
            height: dp(56)
            spacing: dp(12)

            MDButton:
                on_release: expanding_card.collapse()
                disabled: not expanding_card.expanded
                MDButtonIcon:
                    icon: "chevron-double-left"
                MDButtonText:
                    text: "Свернуть"

            MDButton:
                on_release: expanding_card.expand()
                disabled: expanding_card.expanded
                MDButtonIcon:
                    icon: "chevron-double-right"
                MDButtonText:
                    text: "Развернуть"

        MDLabel:
            text: "Подсказка: перетаскивайте карточки A1/A2/B1/B2. При наведении на другую — отпустите для обмена с анимацией."
            halign: "center"
            theme_text_color: "Secondary"
            size_hint_y: None
            height: dp(24)

    # Overlay идёт ПОСЛЕДНИМ — поверх всего
    DragOverlay:
        id: overlay
        size_hint: 1, 1
"""


# --------- утилиты ---------


def widget_window_bbox(w: Widget) -> tuple[float, float, float, float]:
    x, y = w.to_window(w.x, w.y)
    return x, y, float(w.width), float(w.height)


def rects_intersect(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


# --------- центральная карточка ---------


class ExpandingCard(StencilView):
    animated_width: float = NumericProperty(0.0)
    target_width: float = NumericProperty(0.0)
    expanded: bool = BooleanProperty(False)
    _anim: Optional[Animation] = None
    compute_target: Callable[[float], float] = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.compute_target is None:
            self.compute_target = lambda avail: min(avail * 0.6, dp(520))
        self.fbind("parent", self._on_parent_changed)

    def toggle(self) -> None:
        self.expand() if not self.expanded else self.collapse()

    def expand(self) -> None:
        self._ensure_target()
        self._animate_to(self.target_width)
        self.expanded = True

    def collapse(self) -> None:
        self._animate_to(0.0)
        self.expanded = False

    def _get_horizontal_container(self) -> Widget | None:
        p = self.parent
        gp = p.parent if p else None
        return gp or p

    def _on_parent_changed(self, *_args) -> None:
        horiz: Widget | None = self._get_horizontal_container()
        if not horiz:
            return
        self.animated_width = 0.0
        self.expanded = False
        horiz.fbind("width", self._on_container_resize)
        self._on_container_resize(horiz, horiz.width)
        self._animate_to(self.target_width, d=0.35, t="out_cubic")
        self.expanded = True

    def _on_container_resize(self, container: Widget, _value: float) -> None:
        avail = float(container.width)
        new_target = float(self.compute_target(avail))
        if abs(new_target - float(self.target_width)) > 0.5:
            self.target_width = new_target
            if self.expanded:
                self._animate_to(self.target_width, d=0.2, t="out_quad")

    def _ensure_target(self) -> None:
        container: Widget | None = self._get_horizontal_container()
        if container:
            self.target_width = float(self.compute_target(float(container.width)))

    def _animate_to(self, width: float, d: float = 0.28, t: str = "out_cubic") -> None:
        if self._anim is not None:
            self._anim.stop(self)
            self._anim = None
        self._anim = Animation(animated_width=max(0.0, float(width)), duration=d, t=t)
        self._anim.bind(on_complete=lambda *_: self._clear_anim_ref())
        self._anim.start(self)

    def _clear_anim_ref(self) -> None:
        self._anim = None


# --------- overlay ---------


class DragOverlay(FloatLayout):
    """Прозрачный слой над контентом; координаты — как у родителя."""


# --------- DnD карточки ---------


class DraggableCard(MDCard):
    title: str = StringProperty("Title")
    subtitle: str = StringProperty("Subtitle")

    dragging: bool = BooleanProperty(False)
    is_drag_over: bool = BooleanProperty(False)
    overlay: DragOverlay | None = ObjectProperty(None, rebind=True)

    # плейсхолдеры и позиции
    _home_placeholder: Widget | None = None
    _target_placeholder: Widget | None = None
    _home_parent: Widget | None = None
    _home_index: int = -1
    _target_parent: Widget | None = None
    _target_index: int = -1

    _touch_offset: ListProperty = ListProperty([0.0, 0.0])
    _anim: Optional[Animation] = None

    def on_parent(self, *_):
        root = MDApp.get_running_app().root
        if root and hasattr(root, "ids"):
            self.overlay = root.ids.get("overlay")

    # ---- drag lifecycle ----

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if hasattr(touch, "button") and touch.button != "left":
            return super().on_touch_down(touch)

        touch.grab(self)
        self.dragging = True
        self._home_parent = self.parent
        self._home_index = self._home_parent.children.index(self)

        # плейсхолдер на месте перетаскиваемой карточки
        self._home_placeholder = Widget(size_hint_y=None, height=self.height)
        self._home_parent.remove_widget(self)
        self._home_parent.add_widget(self._home_placeholder, index=self._home_index)

        # перенос в overlay
        if self.overlay:
            wx, wy = self.to_window(self.x, self.y)
            self._touch_offset = [touch.x - wx, touch.y - wy]
            ox, oy = self.overlay.to_widget(wx, wy)

            self.size_hint = (None, None)
            self._safe_detach_from_parent()
            self.overlay.add_widget(self)

            self.size = (self.width, self.height)
            self.pos = (ox, oy)

            Animation.cancel_all(self)
            Animation(opacity=0.96, duration=0.08).start(self)

        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        if not self.dragging or self.overlay is None:
            return True

        ox, oy = self.overlay.to_widget(touch.x, touch.y)
        self.pos = (ox - self._touch_offset[0], oy - self._touch_offset[1])

        self._update_hover_state()
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)

        if not self.dragging:
            return True
        self.dragging = False

        target = self._detect_drop_target()

        if target and self.overlay:
            # --- готовим двойную анимацию со плейсхолдерами с обеих сторон ---
            tx, ty, tw, th = widget_window_bbox(target)
            px, py, pw, ph = widget_window_bbox(self._home_placeholder)

            # плейсхолдер на месте цели
            self._target_parent = target.parent
            self._target_index = self._target_parent.children.index(target)
            self._target_placeholder = Widget(size_hint_y=None, height=target.height)
            self._target_parent.remove_widget(target)
            self._target_parent.add_widget(
                self._target_placeholder, index=self._target_index
            )

            # переносим target в overlay на текущую позицию
            target_ox, target_oy = self.overlay.to_widget(tx, ty)
            target.size_hint = (None, None)
            self.overlay.add_widget(target)
            target.size = (target.width, target.height)
            target.pos = (target_ox, target_oy)

            # финальные overlay-координаты
            self_dest_ox, self_dest_oy = self.overlay.to_widget(
                tx, ty
            )  # self -> место target
            target_dest_ox, target_dest_oy = self.overlay.to_widget(
                px, py
            )  # target -> место self

            # анимации
            a1 = Animation(x=self_dest_ox, y=self_dest_oy, duration=0.14, t="out_cubic")
            a2 = Animation(
                x=target_dest_ox, y=target_dest_oy, duration=0.14, t="out_cubic"
            )

            def _finish(*_):
                # вернуть self в parent цели (вместо его плейсхолдера)
                self._safe_detach_from_parent()
                if (
                    self._target_parent is not None
                    and self._target_placeholder is not None
                ):
                    idx = self._target_parent.children.index(self._target_placeholder)
                    self._target_parent.remove_widget(self._target_placeholder)
                    self._target_placeholder = None
                    # важное: растяжение по ширине колонки
                    self.size_hint = (1, None)
                    self.width = 0  # сбросить фиксированную ширину
                    self._target_parent.add_widget(self, index=idx)

                # вернуть target в исходную колонку (вместо нашего плейсхолдера)
                target._safe_detach_from_parent()
                if self._home_parent is not None and self._home_placeholder is not None:
                    idx2 = self._home_parent.children.index(self._home_placeholder)
                    self._home_parent.remove_widget(self._home_placeholder)
                    self._home_placeholder = None
                    target.size_hint = (1, None)
                    target.width = 0
                    self._home_parent.add_widget(target, index=idx2)

                # очистка
                self._home_parent = None
                self._target_parent = None
                self._home_index = -1
                self._target_index = -1

                for w in (self, target):
                    Animation.cancel_all(w)
                    Animation(opacity=1.0, duration=0.08).start(w)

            # запускаем; фиксация окончания по второй анимации
            a1.start(self)
            a2.bind(on_complete=_finish)
            a2.start(target)

        else:
            self._animate_back_home()

        self._clear_all_hover()
        return True

    # ---- hover / target ----

    def _iter_all_draggables(self):
        root = MDApp.get_running_app().root
        if not root or not hasattr(root, "ids"):
            return []
        result = []
        for col_id in ("left_col", "right_col"):
            col = root.ids.get(col_id)
            if col:
                for w in col.children:
                    if w is not self and isinstance(w, DraggableCard):
                        result.append(w)
        return result

    def _detect_drop_target(self) -> Optional["DraggableCard"]:
        ax, ay, aw, ah = widget_window_bbox(self)
        my_rect = (ax, ay, aw, ah)
        for other in self._iter_all_draggables():
            bx, by, bw, bh = widget_window_bbox(other)
            if rects_intersect(my_rect, (bx, by, bw, bh)):
                return other
        return None

    def _update_hover_state(self):
        target = self._detect_drop_target()
        for other in self._iter_all_draggables():
            other.is_drag_over = other is target

    def _clear_all_hover(self):
        for other in self._iter_all_draggables():
            other.is_drag_over = False

    # ---- return ----

    def _safe_detach_from_parent(self):
        if self.parent:
            try:
                self.parent.remove_widget(self)
            except Exception:
                pass

    def _animate_back_home(self):
        if (
            self._home_parent is None
            or self._home_placeholder is None
            or self.overlay is None
        ):
            self.opacity = 1.0
            return
        px, py, pw, ph = widget_window_bbox(self._home_placeholder)
        ox, oy = self.overlay.to_widget(px, py)
        anim = Animation(x=ox, y=oy, duration=0.14, t="out_cubic")

        def _finish(*_):
            self._safe_detach_from_parent()
            if self._home_parent is not None and self._home_placeholder is not None:
                idx = self._home_parent.children.index(self._home_placeholder)
                self._home_parent.remove_widget(self._home_placeholder)
                self._home_placeholder = None
                # вернуть растяжение по ширине колонки
                self.size_hint = (1, None)
                self.width = 0
                self._home_parent.add_widget(self, index=idx)

            self._home_parent = None
            self._home_index = -1
            Animation.cancel_all(self)
            Animation(opacity=1.0, duration=0.08).start(self)

        anim.bind(on_complete=_finish)
        anim.start(self)


# --------- App ---------


class ExpandingCardDnDApp(MDApp):
    def build(self):
        self.title = "Expanding Card + Drag & Drop Demo"
        self.theme_cls.material_style = "M3"
        root = Builder.load_string(KV)

        # overlay тянется по всему Screen; подстраховка при изменении окна
        overlay: DragOverlay = root.ids.overlay
        overlay.size = Window.size
        Window.bind(size=lambda _w, s: setattr(overlay, "size", s))
        return root


if __name__ == "__main__":
    ExpandingCardDnDApp().run()
