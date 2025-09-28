# run_list_demo.py
# -*- coding: utf-8 -*-
"""
Минимальное тестовое приложение KivyMD, которое использует кастомные элементы
списка из `list.py` (+шаблоны из `list.kv`) и показывает прокручиваемый список.

Как запустить (из той же папки, где лежат list.py и list.kv):
    python run_list_demo.py
"""
from __future__ import annotations

import os

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.utils import platform
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView

# Кастомные элементы списка
from mvckivy.uix.list import (
    MKVList,
    MKVListItem,
    MKVListItemHeadlineText,
    MKVListItemSupportingText,
    MKVListItemTertiaryText,
    MKVListItemLeadingIcon,
    MKVListItemTrailingIcon,
    MKVListItemTrailingCheckbox,
)

KV_LIST_PATH = (
    r"C:\Users\alesa\Documents\AlesavigoSoftware\mvckivy\src\mvckivy\uix\list\list.kv"
)


class Root(MDBoxLayout):
    pass


class DemoListApp(MDApp):
    title = "MKV List Demo"

    def build(self):
        # Загружаем шаблоны для MKVListItem, если рядом есть list.kv
        if os.path.exists(KV_LIST_PATH):
            Builder.load_file(KV_LIST_PATH)

        return Builder.load_file(
            r"C:\Users\alesa\Documents\AlesavigoSoftware\mvckivy\test\lists_test\mkv_list.kv"
        )

    def toggle_theme(self, active: bool):
        # если active True — включаем Dark, иначе Light
        self.theme_cls.theme_style = "Dark" if active else "Light"
        # root = Root(
        #     orientation="vertical",
        #     spacing=0,
        #     md_bg_color=self.theme_cls.onBackgroundColor,
        # )
        #
        # scroll = MDScrollView()
        # root.add_widget(scroll)
        #
        # # Сам список
        # lst = MKVList(
        #     cols=1,
        #     adaptive_height=True,  # важно для корректной прокрутки
        #     padding=[dp(8), dp(8), dp(8), dp(8)],
        #     spacing=dp(4),
        # )
        # scroll.add_widget(lst)
        #
        # # Наполняем разными вариантами (1, 2 и 3 строки текста; разные trailing/leading)
        # items_data = [
        #     # (headline, supporting, tertiary, leading_icon, trailing, density, divider)
        #     (
        #         "Single-line item",
        #         None,
        #         None,
        #         "account",
        #         ("icon", "chevron-right"),
        #         0,
        #         True,
        #     ),
        #     (
        #         "Two-line item",
        #         "Supporting text goes here",
        #         None,
        #         "email",
        #         ("checkbox", True),
        #         1,
        #         True,
        #     ),
        #     (
        #         "Three-line item",
        #         "Supporting line",
        #         "Tertiary (small) hint",
        #         "map",
        #         ("icon", "dots-vertical"),
        #         2,
        #         True,
        #     ),
        #     (
        #         "Disabled item",
        #         "Not clickable",
        #         None,
        #         "alert",
        #         ("checkbox", False),
        #         0,
        #         True,
        #     ),
        #     ("Plain headline", None, None, None, None, 1, False),
        #     (
        #         "Compact density",
        #         "Smaller vertical padding",
        #         None,
        #         "calendar",
        #         ("icon", "information-outline"),
        #         1,
        #         True,
        #     ),
        #     (
        #         "Cozy density",
        #         "A bit taller",
        #         "And tertiary too",
        #         "star",
        #         ("checkbox", True),
        #         2,
        #         True,
        #     ),
        #     (
        #         "Max density",
        #         "Tallest variant",
        #         "For visual check",
        #         "account-circle",
        #         ("icon", "chevron-right"),
        #         3,
        #         True,
        #     ),
        # ]
        #
        # def _fill(_dt):
        #     for title, sup, tert, leading, trailing, density, divider in items_data:
        #         it = MKVListItem(density=density, use_divider=divider)
        #         Clock.tick()
        #         if leading:
        #             it.add_widget(MKVListItemLeadingIcon(icon=leading))
        #         it.add_widget(MKVListItemHeadlineText(text=title))
        #         if sup:
        #             it.add_widget(MKVListItemSupportingText(text=sup))
        #         if tert:
        #             it.add_widget(MKVListItemTertiaryText(text=tert, opacity=0.8))
        #         if trailing:
        #             kind, val = trailing
        #             it.add_widget(
        #                 MKVListItemTrailingIcon(icon=val)
        #                 if kind == "icon"
        #                 else MKVListItemTrailingCheckbox(active=bool(val))
        #             )
        #         if title.startswith("Disabled"):
        #             it.disabled = True
        #         lst.add_widget(it)
        #
        # Clock.schedule_once(_fill, 0)
        #
        # return root


if __name__ == "__main__":
    DemoListApp().run()
