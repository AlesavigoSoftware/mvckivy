from __future__ import annotations

import unittest

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from mvckivy.app import MKVApp
from mvckivy.uix.tab import MKVBottomSwipeTabs, MKVTabItem


def pump_frames(count: int = 3) -> None:
    for _ in range(count):
        Clock.tick()


class _BottomTabsApp(MKVApp):
    def build(self):
        return BoxLayout()


class BottomTabsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _BottomTabsApp()
        cls.root = cls.app.build()
        pump_frames()

    def tearDown(self) -> None:
        self.root.clear_widgets()
        pump_frames()

    def _make_tabs(self, **kwargs) -> MKVBottomSwipeTabs:
        tabs = MKVBottomSwipeTabs(**kwargs)
        self.root.add_widget(tabs)
        pump_frames()
        return tabs

    def _content(self, name: str) -> Widget:
        widget = Widget()
        widget.test_id = name
        return widget


class TestBottomTabs(BottomTabsTestCase):
    def test_active_state_uses_colors_and_icons(self) -> None:
        tabs = self._make_tabs(
            active_text_color=(1, 0, 0, 1),
            inactive_text_color=(0.2, 0.2, 0.2, 1),
            active_icon_color=(0, 0.5, 1, 1),
            inactive_icon_color=(0.4, 0.4, 0.4, 1),
        )
        first = tabs.add_tab(
            "Home",
            icon="home-outline",
            active_icon="home",
            content=self._content("home"),
        )
        second = tabs.add_tab(
            "Profile",
            icon="account-outline",
            active_icon="account",
            content=self._content("profile"),
        )
        pump_frames()

        # Initial state highlights the first tab
        self.assertEqual(first.text_widget.text_color, [1, 0, 0, 1])
        self.assertEqual(list(first.icon_widget.icon_color), [0, 0.5, 1, 1])
        self.assertEqual(second.text_widget.text_color, [0.2, 0.2, 0.2, 1])
        self.assertEqual(list(second.icon_widget.icon_color), [0.4, 0.4, 0.4, 1])
        self.assertEqual(first.display_icon, "home")
        self.assertEqual(second.display_icon, "account-outline")
        self.assertFalse(tabs._tab_bar.show_indicator)

        tabs.switch_to(second, animate=False)
        pump_frames()
        self.assertEqual(second.text_widget.text_color, [1, 0, 0, 1])
        self.assertEqual(list(second.icon_widget.icon_color), [0, 0.5, 1, 1])
        self.assertEqual(first.text_widget.text_color, [0.2, 0.2, 0.2, 1])
        self.assertEqual(list(first.icon_widget.icon_color), [0.4, 0.4, 0.4, 1])
        self.assertEqual(second.display_icon, "account")

    def test_swiper_position_controls_order(self) -> None:
        tabs = self._make_tabs()
        tabs.add_tab("One", content=self._content("one"))
        tabs.add_tab("Two", content=self._content("two"))
        pump_frames()

        # Bottom (default) → tab bar is the second child in children list (reverse order)
        children = list(tabs.children)
        self.assertIs(children[0], tabs._carousel)
        self.assertIs(children[1], tabs._tab_bar)

        tabs.swiper_position = "top"
        pump_frames()
        children = list(tabs.children)
        self.assertIs(children[0], tabs._tab_bar)
        self.assertIs(children[1], tabs._carousel)

    def test_horizontal_layout_and_spacing(self) -> None:
        tabs = self._make_tabs(item_spacing=dp(12))
        tabs.add_tab("One", content=self._content("one"))
        tabs.add_tab("Two", content=self._content("two"))
        pump_frames()
        for item in tabs.tabs:
            self.assertEqual(item.orientation, "horizontal")
            self.assertAlmostEqual(item.spacing, dp(12))

    def test_scrollable_mode_many_tabs(self) -> None:
        tabs = self._make_tabs(tab_mode="scrollable")
        for i in range(10):
            tabs.add_tab(f"Item {i}", content=self._content(str(i)))
        pump_frames()
        self.assertTrue(tabs._tab_bar._scroll_view.do_scroll_x)
