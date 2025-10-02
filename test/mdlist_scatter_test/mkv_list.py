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

        return Builder.load_file(r"/mdlist_scatter_test\mkv_list.kv")

    def toggle_theme(self, active: bool):
        # если active True — включаем Dark, иначе Light
        self.theme_cls.theme_style = "Dark" if active else "Light"


if __name__ == "__main__":
    DemoListApp().run()
