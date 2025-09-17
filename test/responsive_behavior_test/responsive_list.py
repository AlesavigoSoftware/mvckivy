from __future__ import annotations

from typing import Literal, List

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import StringProperty, get_color_from_hex
from kivy.factory import Factory

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import (
    MDList,
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
)

KV = r"""
#:import dp kivy.metrics.dp

# Иконка с подсказкой (достаточно tooltip_text)
<InfoIcon@MDIconButton+MDTooltip>:
    size_hint: None, None
    size: dp(36), dp(36)
    padding: 0, 0
    icon: "information-variant"
    tooltip_text: ""
    tooltip_display_delay: 0.1

# Адаптивный айтем со скруглениями и "density"
<AdaptiveListItem@MDListItem>:
    # 0(desktop) / -1(tablet) / -2(mobile)
    density_step: 0
    # сколько текстовых строк мы отображаем (1/2/3)
    text_lines: 3

    # базовые высоты MD3
    _row_delta: dp(4) * root.density_step
    -height: max(dp(48), ((dp(56) if root.text_lines==1 else (dp(72) if root.text_lines==2 else (dp(88) if root.text_lines==3 else dp(100)))) + root._row_delta))
    _pad_base: dp(12) if root.text_lines==3 else dp(8)
    -padding: dp(16), max(dp(4), root._pad_base + root._row_delta), dp(24), max(dp(4), root._pad_base + root._row_delta)

    divider: False
    canvas.before:
        Color:
            rgba: app.theme_cls.surfaceContainerHighColor
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12), dp(12), dp(12), dp(12)]
    canvas.after:
        Color:
            rgba: app.theme_cls.outlineVariantColor
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(12))
            width: 1

<Root>:
    orientation: "vertical"
    md_bg_color: app.theme_cls.backgroundColor

    # Переключатели вида
    MDBoxLayout:
        size_hint_y: None
        height: dp(56)
        padding: dp(8)
        spacing: dp(8)
        md_bg_color: app.theme_cls.surfaceContainerColor

        MDButton:
            style: "outlined"
            on_release: root.set_mode("desktop")
            MDButtonText:
                text: "Desktop (3)"

        MDButton:
            style: "outlined"
            on_release: root.set_mode("tablet")
            MDButtonText:
                text: "Tablet (2)"

        MDButton:
            style: "outlined"
            on_release: root.set_mode("mobile")
            MDButtonText:
                text: "Mobile (1)"

        MDLabel:
            text: "Текущий режим: " + root.mode_display
            halign: "right"
            font_style: "Body"
            role: "medium"

    # Список
    MDScrollView:
        bar_width: 0
        padding: dp(12), dp(12)
        MDList:
            id: lst
            spacing: dp(8)  # desktop=8, tablet=6, mobile=4
"""


class Root(MDBoxLayout):
    mode = StringProperty("desktop")
    mode_display = StringProperty("DESKTOP")
    _list: MDList | None = None
    _items: List[MDListItem] = []

    def on_kv_post(self, *_):
        self._list = self.ids.lst
        self._build_items(12)
        Clock.schedule_once(lambda *_: self.set_mode(self.mode), 0)

    def _build_items(self, count: int):
        for i in range(1, count + 1):
            item = Factory.AdaptiveListItem()

            hl = MDListItemHeadlineText(text=f"Запись #{i}", bold=True)
            s1 = MDListItemSupportingText(text=f"Доп. текст 1 для #{i}")
            s2 = MDListItemSupportingText(text=f"Доп. текст 2 для #{i}")

            # добавляем так, чтобы MDListItem сам положил в text_container
            item.add_widget(hl)
            item.add_widget(s1)
            item.add_widget(s2)

            # иконки tooltips (один раз на айтем)
            tip1 = Factory.InfoIcon()
            tip1.tooltip_text = s1.text
            tip2 = Factory.InfoIcon()
            tip2.tooltip_text = s2.text

            item._hl = hl
            item._s1 = s1
            item._s2 = s2
            item._tip1 = tip1
            item._tip2 = tip2

            self._list.add_widget(item)
            self._items.append(item)

    def set_mode(self, mode: Literal["desktop", "tablet", "mobile"]):
        self.mode = mode
        self.mode_display = mode.upper()

        if mode == "desktop":
            show_s1, show_s2, step, list_spacing = True, True, 0, dp(8)
        elif mode == "tablet":
            show_s1, show_s2, step, list_spacing = True, False, -1, dp(6)
        else:
            show_s1, show_s2, step, list_spacing = False, False, -2, dp(4)

        if self._list:
            self._list.spacing = list_spacing

        for item in self._items:
            tc = self._text_container(item)
            tr = self._trailing_container(item)

            # 1) density и кол-во текстовых строк для формул в KV
            item.density_step = step
            item.text_lines = 1 + (1 if show_s1 else 0) + (1 if show_s2 else 0)

            # 2) очистить trailing полностью (чтобы не было дублей)
            self._clear_trailing(tr)

            # 3) headline всегда в тексте
            self._move_into_text_container(item, item._hl, tc)

            # 4) s1/s2: в текст или в tooltip
            if show_s1:
                self._move_into_text_container(item, item._s1, tc)
            else:
                self._detach(item._s1)

            if show_s2:
                self._move_into_text_container(item, item._s2, tc)
            else:
                self._detach(item._s2)

            icons = 0
            if not show_s1 and tr:
                item._tip1.tooltip_text = item._s1.text
                tr.add_widget(item._tip1)
                icons += 1
            if not show_s2 and tr:
                item._tip2.tooltip_text = item._s2.text
                tr.add_widget(item._tip2)
                icons += 1

            self._set_trailing_width(tr, icons)

    # --- утилиты ---
    def _text_container(self, item: MDListItem):
        tc = getattr(item, "ids", {}).get("text_container", None)
        if tc is not None:
            return tc
        for child in item.children:
            if (
                isinstance(child, MDBoxLayout)
                and getattr(child, "orientation", "") == "vertical"
            ):
                return child
        return None

    def _trailing_container(self, item: MDListItem):
        tr = getattr(item, "ids", {}).get("trailing_container", None)
        if tr is not None:
            return tr
        for child in item.children:
            if isinstance(child, MDBoxLayout) and child.size_hint_x is None:
                return child
        return None

    def _move_into_text_container(self, item: MDListItem, w, tc):
        if not tc or w.parent is tc:
            return
        self._detach(w)
        item.add_widget(w)

    def _detach(self, w):
        p = getattr(w, "parent", None)
        if p is not None:
            try:
                p.remove_widget(w)
            except Exception:
                pass

    def _clear_trailing(self, tr):
        if not tr:
            return
        for child in list(tr.children):
            tr.remove_widget(child)
        tr.width = 0

    def _set_trailing_width(self, tr, count: int):
        if not tr:
            return
        tr.width = (
            0 if count <= 0 else count * dp(36) + max(0, count - 1) * dp(4) + dp(8)
        )


class App(MDApp):
    def build(self):
        self.title = "MDListItem: adaptive density + tooltips + rounding"
        self.theme_cls.primary_palette = "Blue"
        Builder.load_string(KV)
        Clock.schedule_once(
            lambda dt: setattr(
                MDApp.get_running_app().theme_cls,
                "surfaceContainerColor",
                get_color_from_hex("#000000"),
            ),
            10,
        )  # chain bind test
        return Factory.Root()


if __name__ == "__main__":
    App().run()
