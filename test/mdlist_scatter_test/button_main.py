# from __future__ import annotations
#
# from typing import Optional
#
# from kivy.app import App
# from kivy.core.window import Window, WindowBase
# from kivy.graphics import Color, Rectangle, Line, InstructionGroup
# from kivy.lang import Builder
# from kivy.metrics import dp
# from kivy.properties import BooleanProperty, ListProperty, StringProperty
# from kivy.uix.floatlayout import FloatLayout
# from kivy.uix.relativelayout import RelativeLayout
# from kivy.uix.scatter import Scatter
# from kivy.uix.scatterlayout import ScatterLayout
# from kivy.uix.stencilview import StencilView
# from kivy.uix.widget import Widget
# from kivy.uix.label import Label
#
#
# # ───────────────────────────────────────────────
# # Минимальный hover-виджет
# # ───────────────────────────────────────────────
#
#
# class HoverTile(Widget):
#     base_rgba = ListProperty([0.35, 0.45, 0.55, 0.35])
#     hover_rgba = ListProperty([0.30, 0.70, 1.00, 0.55])
#     caption = StringProperty("")
#     hovered = BooleanProperty(False)
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self._ig = InstructionGroup()
#         self.canvas.add(self._ig)
#         self._bg = Rectangle(pos=self.pos, size=self.size)
#         self._ig.add(Color(*self.base_rgba))
#         self._ig.add(self._bg)
#
#         self._label: Label | None = None
#         self.bind(pos=self._sync, size=self._sync)
#
#     def _sync(self, *_):
#         self._bg.pos = self.pos
#         self._bg.size = self.size
#         if self._label is not None:
#             self._label.pos = (self.x + dp(8), self.top - self._label.height - dp(6))
#
#     def on_caption(self, *_):
#         if self._label is None:
#             lbl = Label(text=self.caption, markup=True, size_hint=(None, None))
#             lbl.texture_update()
#             w, h = lbl.texture_size
#             lbl.size = (w + dp(10), h + dp(6))
#             self._label = lbl
#             self.add_widget(lbl)
#         else:
#             self._label.text = self.caption
#             self._label.texture_update()
#         self._sync()
#
#     # вызываться из корня
#     def hover_enter(self):
#         if not self.hovered:
#             self.hovered = True
#             self._recolor(self.hover_rgba)
#
#     def hover_update(self):
#         pass  # при желании — логика обновления
#
#     def hover_leave(self):
#         if self.hovered:
#             self.hovered = False
#             self._recolor(self.base_rgba)
#
#     def _recolor(self, rgba):
#         self._ig.clear()
#         self._ig.add(Color(*rgba))
#         self._ig.add(self._bg)
#
#
# # ───────────────────────────────────────────────
# # Каркасы карточек (фон + рамка), содержимое задаёт KV
# # ───────────────────────────────────────────────
#
#
# class CardFrame(Widget):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self._ig = InstructionGroup()
#         self.canvas.add(self._ig)
#         self._draw()
#         self.fbind("pos", lambda *_: self._draw())
#         self.fbind("size", lambda *_: self._draw())
#
#     def _draw(self):
#         self._ig.clear()
#         self._ig.add(Color(0.12, 0.16, 0.20, 1))
#         self._ig.add(Rectangle(pos=self.pos, size=self.size))
#         self._ig.add(Color(1, 1, 1, 1))
#         self._ig.add(Line(rectangle=(*self.pos, *self.size), width=1.2))
#
#
# class FloatCard(CardFrame, FloatLayout): ...
#
#
# class RelativeCard(CardFrame, RelativeLayout): ...
#
#
# class ScatterCard(CardFrame, Scatter): ...
#
#
# class ScatterLayoutCard(CardFrame, ScatterLayout): ...
#
#
# # ───────────────────────────────────────────────
# # Корень: один обработчик hover для всей сцены
# # ───────────────────────────────────────────────
#
#
# class Root(StencilView, FloatLayout):
#     def __init__(self, **kw):
#         super().__init__(**kw)
#         self._active: HoverTile | None = None
#         Window.bind(mouse_pos=self._on_mouse)
#
#     # Обход дерева «сверху-вниз» (top-first).
#     # В Kivy parent.children[0] — верхний; рекурсивно обходим сначала верхних детей.
#     def _iter_top_first(self, node: Widget):
#         for child in node.children:  # children[0] — верхний
#             yield child
#             yield from self._iter_top_first(child)
#
#     def _point_inside_stencil_chain(self, w: Widget, wx: float, wy: float) -> bool:
#         p: Widget | None = w.parent
#         while p is not None and not isinstance(p, WindowBase):
#             if isinstance(p, StencilView):
#                 x0, y0 = p.to_window(p.x, p.y)
#                 if not (x0 <= wx <= x0 + p.width and y0 <= wy <= y0 + p.height):
#                     return False
#             p = p.parent
#         return 0 <= wx <= Window.width and 0 <= wy <= Window.height
#
#     def _pick_top(self, wx: float, wy: float) -> HoverTile | None:
#         for w in self._iter_top_first(self):
#             if not isinstance(w, HoverTile):
#                 continue
#             if not self._point_inside_stencil_chain(w, wx, wy):
#                 continue
#             lx, ly = w.to_widget(wx, wy, relative=False)
#             if w.collide_point(lx, ly):
#                 return w
#         return None
#
#     def _on_mouse(self, _win, pos):
#         wx, wy = pos
#         top = self._pick_top(wx, wy)
#
#         if top is self._active:
#             if top:
#                 top.hover_update()
#             return
#
#         if self._active:
#             self._active.hover_leave()
#         if top:
#             top.hover_enter()
#         self._active = top
#
#
# # ───────────────────────────────────────────────
# # KV: 4 карточки квадратом в центре + перекрытия
# # ───────────────────────────────────────────────
#
# KV = r"""
# #:import dp kivy.metrics.dp
#
# <HoverTile>:
#     size_hint: None, None
#
# <FloatCard>:
#     HoverTile:
#         caption: "[b]Float[/b] A"
#         size: dp(120), dp(60)
#         pos: root.x + dp(12), root.y + dp(12)
#     HoverTile:
#         caption: "[b]Float[/b] B"
#         size: dp(140), dp(75)
#         pos: root.x + dp(60), root.y + dp(40)
#
# <RelativeCard>:
#     HoverTile:
#         caption: "[b]Relative[/b] A"
#         size_hint: .6, .55
#         pos_hint: {"x": .05, "y": .05}
#     HoverTile:
#         caption: "[b]Relative[/b] B"
#         size_hint: .65, .6
#         pos_hint: {"right": .98, "top": .98}
#
# <ScatterCard>:
#     size_hint: None, None
#     size: dp(260), dp(180)
#     do_rotation: True
#     do_scale: True
#     do_translation: True
#     scale: .9
#     rotation: 15
#     HoverTile:
#         caption: "[b]Scatter[/b]"
#         size: root.width - dp(40), root.height - dp(50)
#         pos: root.x + dp(20), root.y + dp(20)
#
# <ScatterLayoutCard>:
#     size_hint: None, None
#     size: dp(260), dp(180)
#     do_rotation: True
#     rotation: -8
#     HoverTile:
#         caption: "[b]ScatterLayout[/b] A"
#         size_hint: .65, .55
#         pos_hint: {"x": .06, "y": .06}
#     HoverTile:
#         caption: "[b]ScatterLayout[/b] B"
#         size_hint: .7, .6
#         pos_hint: {"right": .96, "top": .96}
#
# <Root>:
#     AnchorLayout:
#         anchor_x: "center"
#         anchor_y: "center"
#         GridLayout:
#             cols: 2
#             rows: 2
#             spacing: dp(18)
#             padding: dp(6)
#             size_hint: None, None
#             width: dp(2*260 + 18 + 6*2)
#             height: dp(2*180 + 18 + 6*2)
#
#             FloatCard:
#                 size_hint: None, None
#                 size: dp(260), dp(180)
#
#             RelativeCard:
#                 size_hint: None, None
#                 size: dp(260), dp(180)
#
#             ScatterCard:
#
#             ScatterLayoutCard:
# """
#
#
# # ───────────────────────────────────────────────
# # App
# # ───────────────────────────────────────────────
#
#
# class DemoApp(App):
#     def build(self):
#         Builder.load_string(KV)
#         return Root()
#
#
# if __name__ == "__main__":
#     DemoApp().run()


from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import weakref

from kivy.app import App
from kivy.core.window import Window, WindowBase
from kivy.graphics import Color, Rectangle, Line, InstructionGroup
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import DictProperty, BooleanProperty, ListProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatter import Scatter
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.stencilview import StencilView
from kivy.uix.widget import Widget
from kivy.uix.label import Label


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    def contains_point(self, px: float, py: float) -> bool:
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h


class RectCache:
    """Кэш прямоугольников виджетов в координатах окна. Инвалидация по pos/size."""

    def __init__(self):
        self._cache: weakref.WeakKeyDictionary[Widget, Rect] = (
            weakref.WeakKeyDictionary()
        )

    def clear_all(self) -> None:
        self._cache.clear()

    def bind_invalidation(self, w: Widget) -> None:
        def _invalidate(*_):
            self._cache.pop(w, None)

        w.fbind("pos", _invalidate)
        w.fbind("size", _invalidate)

    def window_rect(self, w: Widget) -> Rect:
        if isinstance(w, WindowBase) or w is Window:
            return Rect(0, 0, Window.width, Window.height)
        rect = self._cache.get(w)
        if rect is None:
            x0, y0 = w.to_window(w.x, w.y)
            rect = Rect(x0, y0, w.width, w.height)
            self._cache[w] = rect
        return rect


class HoverBehavior:
    _hover_ids = DictProperty({})
    hovered = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hover_host_ref: weakref.ReferenceType[HoverHostMixin] | None = None

    def _find_hover_host(self) -> Optional["HoverHostMixin"]:
        node: Optional[Widget] = self.parent  # type: ignore[assignment]
        while node is not None:
            if isinstance(node, HoverHostMixin):
                return node  # type: ignore[return-value]
            node = node.parent  # type: ignore[assignment]
        return None

    def _set_host(self, host: Optional["HoverHostMixin"]) -> None:
        self._hover_host_ref = weakref.ref(host) if host else None

    def _get_host(self) -> Optional["HoverHostMixin"]:
        return self._hover_host_ref() if self._hover_host_ref else None

    def on_kv_post(self, *args):
        # Регистрация произойдёт уже после того, как у HoverRoot созданы поля (__init__)
        host = self._find_hover_host()
        if host:
            host.register_hover_widget(self)
            host._rect_cache.bind_invalidation(self)
            self._set_host(host)

    def on_parent(self, *_):
        # Переезд в другое место дерева: пере-регистрируемся
        new_host = self._find_hover_host()
        old_host = self._get_host()
        if old_host and old_host is not new_host:
            old_host.unregister_hover_widget(self)
        if new_host and old_host is not new_host:
            new_host.register_hover_widget(self)
            new_host._rect_cache.bind_invalidation(self)
        self._set_host(new_host)

    # интерфейс для менеджера
    def _hb_enter(self, uid: int, pos_win: tuple[float, float]) -> None:
        self._hover_ids[uid] = pos_win
        self.hovered = True
        self.on_hover_enter(uid, pos_win)

    def _hb_update(self, uid: int, pos_win: tuple[float, float]) -> None:
        self._hover_ids[uid] = pos_win
        self.on_hover_update(uid, pos_win)

    def _hb_leave(self, uid: int) -> None:
        if uid in self._hover_ids:
            self._hover_ids.pop(uid)
        self.hovered = bool(self._hover_ids)
        self.on_hover_leave(uid)

    # события для переопределения
    def on_hover_enter(self, uid: int, pos_win: tuple[float, float]) -> None: ...
    def on_hover_update(self, uid: int, pos_win: tuple[float, float]) -> None: ...
    def on_hover_leave(self, uid: int) -> None: ...


class HoverHostMixin:
    def __init__(self, **kwargs):
        self._rect_cache = RectCache()
        self._widgets: list[HoverBehavior] = []
        self._sorted: list[HoverBehavior] = []
        self._dirty = True
        self._watched_nodes: weakref.WeakSet[Widget] = weakref.WeakSet()
        super().__init__(**kwargs)  # type: ignore[misc]
        Window.bind(mouse_pos=self._on_mouse_pos)

        # ⬇️ при максимизации/ресайзе окна сбрасываем кэш прямоугольников
        def _(*_):
            self._rect_cache.clear_all()
            self._dirty = True

        Window.bind(size=_)

    # публичное API
    def register_hover_widget(self, w: HoverBehavior) -> None:
        if w not in self._widgets:
            self._widgets.append(w)
            self._watch_ancestors_of(w)
            self._dirty = True

    def unregister_hover_widget(self, w: HoverBehavior) -> None:
        if w in self._widgets:
            self._widgets.remove(w)
            self._dirty = True

    # быстрый путь — каждый кадр
    def _on_mouse_pos(self, _win, pos) -> None:
        if self._dirty:
            self._rebuild_sorted()
            self._dirty = False

        uid = 1
        wx, wy = pos
        claimed = False

        for w in self._sorted:
            if not isinstance(w, Widget):
                continue
            if not self._passes_stencil_chain(w, wx, wy):
                inside = False
            else:
                lx, ly = w.to_widget(wx, wy, relative=False)
                inside = w.collide_point(lx, ly)

            if claimed:
                inside = False

            active = uid in getattr(w, "_hover_ids", {})
            if inside and not active:
                w._hb_enter(uid, (wx, wy))
                claimed = True
            elif inside and active:
                w._hb_update(uid, (wx, wy))
                claimed = True
            elif (not inside) and active:
                w._hb_leave(uid)

    # медленный путь — только при изменении дерева
    def _rebuild_sorted(self) -> None:
        ws = [w for w in self._widgets if isinstance(w, Widget)]
        ws.sort(key=self._z_key, reverse=True)  # верхние раньше
        self._sorted = ws

    def _z_key(self, widget: Widget) -> list[int]:
        key: list[int] = []
        node: Optional[Widget] = widget
        while node is not None and not isinstance(node.parent, WindowBase):
            parent = node.parent
            if parent is None:
                break
            idx = parent.children.index(node)  # 0 — верхний в Kivy
            z = (len(parent.children) - 1) - idx
            key.append(z)
            node = parent  # type: ignore[assignment]
        return key[::-1]

    def _passes_stencil_chain(self, w: Widget, wx: float, wy: float) -> bool:
        p: Optional[Widget] = w.parent  # type: ignore[assignment]
        while p is not None and not isinstance(p, WindowBase):
            if isinstance(p, StencilView):
                pr = self._rect_cache.window_rect(p)
                if not pr.contains_point(wx, wy):
                    return False
            p = p.parent  # type: ignore[assignment]
        return 0 <= wx <= Window.width and 0 <= wy <= Window.height

    def _watch_ancestors_of(self, w: Widget) -> None:
        node: Optional[Widget] = w
        while node is not None:
            if node not in self._watched_nodes:
                self._watched_nodes.add(node)

                def _mark_dirty(*_):
                    self._dirty = True

                node.fbind("children", _mark_dirty)
                node.fbind("parent", _mark_dirty)
                # ⬇️ важно: чтобы RectCache знал, что у предка изменились pos/size
                self._rect_cache.bind_invalidation(node)
            node = node.parent  # type: ignore[assignment]


class HoverTile(HoverBehavior, Widget):
    base_rgba = ListProperty([0.35, 0.45, 0.55, 0.35])
    hover_rgba = ListProperty([0.30, 0.70, 1.00, 0.55])
    caption = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ig = InstructionGroup()
        self.canvas.add(self._ig)
        self._bg = Rectangle(pos=self.pos, size=self.size)
        self._ig.add(Color(*self.base_rgba))
        self._ig.add(self._bg)
        self.bind(pos=self._sync, size=self._sync)
        self._label: Label | None = None

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        if self._label is not None:
            self._label.pos = (self.x + dp(8), self.top - self._label.height - dp(6))

    def on_caption(self, *_):
        if self._label is None:
            lbl = Label(text=self.caption, markup=True, size_hint=(None, None))
            lbl.texture_update()
            w, h = lbl.texture_size
            lbl.size = (w + dp(10), h + dp(6))
            self._label = lbl
            self.add_widget(lbl)
        else:
            self._label.text = self.caption
            self._label.texture_update()
        self._sync()

    def _recolor(self, rgba):
        self._ig.clear()
        self._ig.add(Color(*rgba))
        self._ig.add(self._bg)

    def on_hover_enter(self, *_):
        self._recolor(self.hover_rgba)

    def on_hover_leave(self, *_):
        self._recolor(self.base_rgba)


class CardFrame(Widget):
    """Фон + рамка, содержимое задаётся в KV."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._bg = InstructionGroup()
        self.canvas.add(self._bg)
        self._draw()
        self.fbind("pos", lambda *_: self._draw())
        self.fbind("size", lambda *_: self._draw())

    def _draw(self):
        self._bg.clear()
        self._bg.add(Color(0.12, 0.16, 0.20, 1))
        self._bg.add(Rectangle(pos=self.pos, size=self.size))
        self._bg.add(Color(1, 1, 1, 1))
        self._bg.add(Line(rectangle=(*self.pos, *self.size), width=1.2))


class FloatCard(CardFrame, FloatLayout): ...


class RelativeCard(CardFrame, RelativeLayout): ...


class ScatterCard(CardFrame, Scatter): ...


class ScatterLayoutCard(CardFrame, ScatterLayout): ...


class HoverRoot(HoverHostMixin, StencilView, FloatLayout):
    """Корневой контейнер и менеджер hover."""


# ───────────────────────────────────────────────
# KV: раскладка и перекрытия
# ───────────────────────────────────────────────

KV = r"""
#:import dp kivy.metrics.dp

<HoverTile>:
    size_hint: None, None

<FloatCard>:
    HoverTile:
        caption: "[b]Float[/b] A"
        size: dp(120), dp(60)
        pos: root.x + dp(12), root.y + dp(12)
    HoverTile:
        caption: "[b]Float[/b] B"
        size: dp(140), dp(75)
        pos: root.x + dp(60), root.y + dp(40)

<RelativeCard>:
    HoverTile:
        caption: "[b]Relative[/b] A"
        size_hint: .6, .55
        pos_hint: {"x": .05, "y": .05}
    HoverTile:
        caption: "[b]Relative[/b] B"
        size_hint: .65, .6
        pos_hint: {"right": .98, "top": .98}

<ScatterCard>:
    size_hint: None, None
    size: dp(260), dp(180)
    do_rotation: True
    do_scale: True
    do_translation: True
    scale: .9
    rotation: 15
    HoverTile:
        caption: "[b]Scatter[/b]"
        size: root.width - dp(40), root.height - dp(50)
        pos: root.x + dp(20), root.y + dp(20)

<ScatterLayoutCard>:
    size_hint: None, None
    size: dp(260), dp(180)
    do_rotation: True
    rotation: -8
    HoverTile:
        caption: "[b]ScatterLayout[/b] A"
        size_hint: .65, .55
        pos_hint: {"x": .06, "y": .06}
    HoverTile:
        caption: "[b]ScatterLayout[/b] B"
        size_hint: .7, .6
        pos_hint: {"right": .96, "top": .96}

<HoverRoot>:
    AnchorLayout:
        anchor_x: "center"
        anchor_y: "center"
        GridLayout:
            cols: 2
            rows: 2
            spacing: dp(18)
            padding: dp(6)
            size_hint: None, None
            width: dp(2*260 + 18 + 6*2)
            height: dp(2*180 + 18 + 6*2)

            FloatCard:
                size_hint: None, None
                size: dp(260), dp(180)

            RelativeCard:
                size_hint: None, None
                size: dp(260), dp(180)

            ScatterCard:

            ScatterLayoutCard:
"""


class DemoApp(App):
    def build(self):
        Builder.load_string(KV)
        return HoverRoot()

    def on_stop(self):
        # По желанию можно явно отвязать Window.bind,
        # но при завершении приложения это не критично.
        pass


if __name__ == "__main__":
    DemoApp().run()
