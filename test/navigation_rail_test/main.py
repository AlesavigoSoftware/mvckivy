"""Manual demo for NavigationRail Python layout."""

from __future__ import annotations

from pathlib import Path

from kivy.factory import Factory
from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.navigationdrawer import (
    MDNavigationDrawer,
    MDNavigationDrawerItem,
    MDNavigationLayout,
)
from kivymd.uix.screen import MDScreen

from mvckivy.app import MKVApp
from mvckivy.uix.navigation_rail import (
    NavigationRail,
    NavigationRailItem,
    NavigationRailItemIcon,
    NavigationRailItemLabel,
    NavigationRailButton,
    NavigationRailMenuButton,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
KV_RAIL_PATH = (
    REPO_ROOT
    / "src"
    / "mvckivy"
    / "uix"
    / "navigation_rail"
    / "navigation_rail.kv"
)
KV_TEST_PATH = Path(__file__).with_name("main.kv")

FACTORY_CLASSES = (
    NavigationRail,
    NavigationRailItem,
    NavigationRailItemIcon,
    NavigationRailItemLabel,
    NavigationRailButton,
    NavigationRailMenuButton,
    MDNavigationLayout,
    MDNavigationDrawer,
    MDNavigationDrawerItem,
    MDBoxLayout,
    ScreenManager,
    MDScreen,
    MDLabel,
)

for _cls in FACTORY_CLASSES:
    Factory.register(_cls.__name__, cls=_cls)


class Root(MDNavigationLayout):
    pass


class NavigationRailDemoApp(MKVApp):
    title = "NavigationRail Demo"

    def build(self):
        if KV_RAIL_PATH.exists():
            Builder.load_file(str(KV_RAIL_PATH))
        Builder.load_file(str(KV_TEST_PATH))
        return Root()


if __name__ == "__main__":
    NavigationRailDemoApp().run()
