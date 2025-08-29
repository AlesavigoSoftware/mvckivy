from __future__ import annotations

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty, ObjectProperty
from kivy.uix.widget import Widget

from kivymd.app import MDApp
from kivymd.uix.segmentedbutton import MDSegmentedButton
from kivymd.uix.menu import MDDropdownMenu


class StretchSegmentedButton(MDSegmentedButton):
    """Растягиваем контейнер сегментов по ширине карточки и снимаем min-width."""

    fit_to_parent = BooleanProperty(True)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        if self.fit_to_parent and "container" in self.ids:
            c = self.ids.container
            c.size_hint_min_x = 0
            self.bind(width=lambda *_: setattr(c, "width", self.width))


class CollapsibleMenuController(Widget):
    """Сворачиваемая карточка с drag по «ручке» и клиппингом контента."""

    title = StringProperty("Управление миссией БПЛА")
    transport = StringProperty("БПЛА-1")
    _transport_menu = ObjectProperty(None)

    # авто 1↔2 столбца
    cols = NumericProperty(1)
    two_cols_breakpoint = NumericProperty(dp(520))

    # нормированное состояние
    slide = NumericProperty(1.0)  # 0.0 = раскрыто, 1.0 = свернуто
    open_h = NumericProperty(dp(520))  # вычисляется от контента
    closed_h = NumericProperty(dp(88))  # ручка + сегмент-бар
    content_height = NumericProperty(0)

    # drag state
    _dragging = BooleanProperty(False)
    _start_y = NumericProperty(0.0)
    _start_slide = NumericProperty(0.0)
    swipe_threshold_px = NumericProperty(dp(48))
    _layout_ready = BooleanProperty(False)
    _finalize_trigger = None

    def on_kv_post(self, _):
        Window.bind(size=self._on_window_resize)
        self._on_window_resize()

        # До готовности макета держим контент закрытым.
        self.slide = 1.0
        self.content_height = 0
        self._layout_ready = False

        # Триггер отложенного пересчёта (в одном кадре).
        self._finalize_trigger = Clock.create_trigger(
            lambda *_: self._finalize_layout(), 0
        )

        # Когда поменяется высота секций/хедера/сегмента — пересчёт.
        ids = self.ids
        if "sections" in ids:
            ids.sections.bind(minimum_height=lambda *_: self._finalize_trigger())
        if "hdr" in ids:
            ids.hdr.bind(height=lambda *_: self._finalize_trigger())
        if "segbar" in ids:
            ids.segbar.bind(height=lambda *_: self._finalize_trigger())

        # Первый пересчёт после сборки KV.
        Clock.schedule_once(lambda *_: self._finalize_trigger(), 0)

    def _finalize_layout(self):
        """Единая точка: пересчитать высоты и применить slide без анимации."""
        self._recalc_heights_and_viewport()
        self._layout_ready = True
        self._apply_slide(no_anim=True)

    def _on_window_resize(self, *_):
        w = Window.width
        if w >= 1400:
            card_w = max(dp(560), w * 0.40)
        elif w >= 1024:
            card_w = max(dp(520), w * 0.46)
        else:
            card_w = max(dp(360), w * 0.90)
        self.ids.menu_card.width = card_w
        self.cols = 2 if card_w >= self.two_cols_breakpoint else 1
        # Пересчитать после стабилизации лейаута
        if self._finalize_trigger is not None:
            self._finalize_trigger()

    # ресайз + колонк
    def _recalc_heights_and_viewport(self):
        ids = self.ids
        handle_h = ids.grip.height if "grip" in ids else dp(18)
        header_h = ids.hdr.height if "hdr" in ids else dp(60)
        segbar_h = ids.segbar.height if "segbar" in ids else dp(56)
        pad_tb = dp(8) + dp(8)
        sections_h = ids.sections.minimum_height if "sections" in ids else 0

        desired_open = header_h + pad_tb + sections_h
        max_open = max(dp(240), Window.height * 0.62)
        self.open_h = min(desired_open, max_open)

        self.closed_h = handle_h + segbar_h + dp(8)

        if "scroll" in ids:
            viewport_h = self.open_h - header_h - pad_tb
            ids.scroll.do_scroll_y = sections_h > viewport_h

    # slide → content_height
    def on_slide(self, *_):
        self._apply_slide(no_anim=True)

    def _apply_slide(self, *, no_anim: bool = False):
        if not self._layout_ready:
            # До готовности держим закрытым без анимации.
            self.content_height = 0
            return
        total_delta = max(self.open_h - self.closed_h, 1)
        target_content = (1.0 - self.slide) * total_delta
        if no_anim:
            self.content_height = target_content
        else:
            Animation.cancel_all(self, "content_height")
            Animation(content_height=target_content, d=0.22, t="out_cubic").start(self)

    # кнопки
    def toggle(self):
        target = 0.0 if self.slide >= 0.5 else 1.0
        self.animate_to(target)

    def expand(self):
        self.animate_to(0.0)

    def collapse(self):
        self.animate_to(1.0)

    def on_segment_pressed(self, _key: str):
        self.expand()

    def open_transport_menu(self, caller):
        app = MDApp.get_running_app()
        menu_items = []
        for name in ["БПЛА-1", "БПЛА-2", "БПЛА-3"]:
            selected = name == self.transport
            item = {
                "text": name,
                "on_release": lambda x=name: self.set_transport(x),
            }
            if selected:
                item["leading_icon"] = "check"
                item["text_color"] = app.theme_cls.primaryColor
                item["leading_icon_color"] = app.theme_cls.primaryColor
            menu_items.append(item)
        self._transport_menu = MDDropdownMenu(caller=caller, items=menu_items)
        self._transport_menu.open()

    def set_transport(self, name):
        self.transport = name
        if self._transport_menu:
            self._transport_menu.dismiss()

    def animate_to(self, target: float, duration: float = 0.22):
        Animation.cancel_all(self, "slide")
        Animation(slide=target, d=duration, t="out_cubic").start(self)

    # жест по ручке
    def _in_handle(self, touch) -> bool:
        if "grip" not in self.ids:
            return False
        grip = self.ids.grip
        lx, ly = grip.to_widget(*touch.pos)
        return grip.collide_point(lx, ly)

    def on_touch_down(self, touch):
        if self._in_handle(touch):
            self._dragging = True
            self._start_y = touch.y
            self._start_slide = self.slide
            touch.grab(self)
            if "scroll" in self.ids:
                self.ids.scroll.do_scroll_y = False
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self._dragging:
            total = max(self.open_h - self.closed_h, 1)
            dy = touch.y - self._start_y
            self.slide = min(1.0, max(0.0, self._start_slide + (-dy / total)))
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if "scroll" in self.ids:
            self.ids.scroll.do_scroll_y = True

        if touch.grab_current is self and self._dragging:
            touch.ungrab(self)
            self._dragging = False
            target = 1.0 if self.slide >= 0.5 else 0.0
            self.animate_to(target)
            return True
        return super().on_touch_up(touch)


class DemoApp(MDApp):
    def build(self):
        self.title = "Collapsible Left Menu • KivyMD 2.0"
        self.theme_cls.theme_style = "Dark"
        return Builder.load_file("menu.kv")


if __name__ == "__main__":
    DemoApp().run()
