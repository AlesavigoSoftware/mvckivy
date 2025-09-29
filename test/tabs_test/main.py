"""Ручной стенд, совпадающий с demo/main.py, для визуальной проверки табов."""

from __future__ import annotations

from pathlib import Path

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.widget import Widget

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from mvckivy.app import MKVApp
from mvckivy.uix.tab import MKVBottomSwipeTabs, MKVTabs

REPO_ROOT = Path(__file__).resolve().parents[2]
KV_PATH = Path(__file__).with_name("main.kv")


class Root(MDBoxLayout):
    pass


class TabsDemoApp(MKVApp):
    title = "MVCKivy Tabs Manual"

    def build(self) -> Widget:
        if KV_PATH.exists():
            Builder.load_file(str(KV_PATH))
        else:
            Builder.load_string(_KV_FALLBACK)
        root = Root()
        self._populate_primary_tabs(root.ids.primary_tabs)
        self._populate_bottom_tabs(root.ids.bottom_tabs)
        return root

    def _make_label(self, text: str) -> MDLabel:
        label = MDLabel(text=text, halign="center", size_hint=(1, 1))
        return label

    def _populate_primary_tabs(self, tabs: MKVTabs) -> None:
        tabs.tab_mode = "scrollable"
        sections = ["Новости", "Спорт", "Музыка", "Видео", "Фото", "Игры", "Почта"]
        for title in sections:
            tabs.add_tab(
                title,
                icon="label-outline",
                content=self._make_label(f"Раздел: {title}"),
            )

    def _populate_bottom_tabs(self, tabs: MKVBottomSwipeTabs) -> None:
        tabs.active_text_color = (0.94, 0.33, 0.40, 1)
        tabs.inactive_text_color = (0.45, 0.45, 0.45, 1)
        tabs.active_icon_color = (0.94, 0.33, 0.40, 1)
        tabs.inactive_icon_color = (0.55, 0.55, 0.55, 1)
        definitions = (
            ("Главная", "home-outline", "home"),
            ("Избранное", "star-outline", "star"),
            ("Профиль", "account-outline", "account"),
            ("Настройки", "cog-outline", "cog"),
        )
        for title, icon, active_icon in definitions:
            tabs.add_tab(
                title,
                icon=icon,
                active_icon=active_icon,
                content=self._make_label(f"Раздел: {title}"),
            )


_KV_FALLBACK = """
#:import dp kivy.metrics.dp

<Root>:
    orientation: "vertical"
    padding: dp(24)
    spacing: dp(24)
    md_bg_color: app.theme_cls.backgroundColor

    MDLabel:
        text: "MKVTabs"
        role: "large"
        adaptive_height: True
        halign: "center"

    MKVTabs:
        id: primary_tabs
        size_hint_y: None
        height: dp(240)

    MDLabel:
        text: "MKVBottomSwipeTabs"
        role: "large"
        adaptive_height: True
        halign: "center"

    MKVBottomSwipeTabs:
        id: bottom_tabs
        item_spacing: dp(8)
        bar_height: dp(64)
        size_hint_y: None
        height: dp(220)
"""


if __name__ == "__main__":
    TabsDemoApp().run()
