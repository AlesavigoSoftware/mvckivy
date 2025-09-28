"""Manual tabs demo verifying Python-driven layout."""

from __future__ import annotations

from pathlib import Path

from kivy.factory import Factory
from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

from mvckivy.app import MKVApp
from mvckivy.uix.tab import (
    MKVTabsPrimary,
    MKVTabsSecondary,
    MKVTabsItem,
    MKVTabsItemIcon,
    MKVTabsItemText,
    MKVTabsItemSecondary,
    MKVTabsItemSecondaryContainer,
    MKVTabsCarousel,
    MKVTabsBadge,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
KV_TAB_PATH = REPO_ROOT / "src" / "mvckivy" / "uix" / "tab" / "tab.kv"
KV_TEST_PATH = Path(__file__).with_name("main.kv")

FACTORY_CLASSES = (
    MKVTabsPrimary,
    MKVTabsSecondary,
    MKVTabsItem,
    MKVTabsItemIcon,
    MKVTabsItemText,
    MKVTabsItemSecondary,
    MKVTabsItemSecondaryContainer,
    MKVTabsCarousel,
    MKVTabsBadge,
    MDScreen,
    MDLabel,
)

for _cls in FACTORY_CLASSES:
    Factory.register(_cls.__name__, cls=_cls)


class Root(MDBoxLayout):
    pass


class TabsDemoApp(MKVApp):
    title = "MKVTabs Demo"

    def build(self):
        if KV_TAB_PATH.exists():
            Builder.load_file(str(KV_TAB_PATH))
        Builder.load_file(str(KV_TEST_PATH))
        return Root()


if __name__ == "__main__":
    TabsDemoApp().run()
