from __future__ import annotations

import unittest

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from mvckivy.app import MKVApp
from mvckivy.uix.tab import MKVTabs, MKVTabItem


def pump_frames(count: int = 3) -> None:
    for _ in range(count):
        Clock.tick()


class _TabsTestApp(MKVApp):
    def build(self):
        return BoxLayout()


class TabsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _TabsTestApp()
        cls.root = cls.app.build()
        pump_frames()

    def tearDown(self) -> None:
        self.root.clear_widgets()
        pump_frames()

    def _create_tabs(self, **kwargs) -> MKVTabs:
        tabs = MKVTabs(**kwargs)
        self.root.add_widget(tabs)
        pump_frames()
        return tabs

    def _make_dummy_content(self, suffix: str) -> Widget:
        widget = Widget()
        widget.test_id = f"content_{suffix}"
        widget.size_hint = (1, 1)
        return widget


class TestTabsCore(TabsTestCase):
    def test_add_and_remove_tabs(self) -> None:
        tabs = self._create_tabs()
        added: list[MKVTabItem] = []
        removed: list[MKVTabItem | None] = []
        tabs.bind(on_tab_add=lambda inst, item: added.append(item))
        tabs.bind(on_tab_remove=lambda inst, item: removed.append(item))

        first = tabs.add_tab("One", content=self._make_dummy_content("one"))
        second = tabs.add_tab("Two", content=self._make_dummy_content("two"))
        pump_frames()

        self.assertEqual(len(tabs.tabs), 2)
        self.assertEqual(tabs.current_tab, first)
        self.assertEqual([first, second], added)

        tabs.remove_tab(0)
        pump_frames()
        self.assertEqual(len(tabs.tabs), 1)
        self.assertEqual(tabs.current_tab, second)
        self.assertEqual(removed[-1], first)

        tabs.remove_tab(second)
        pump_frames()
        self.assertEqual(len(tabs.tabs), 0)
        self.assertEqual(tabs.current_index, -1)

    def test_switch_via_click_and_event(self) -> None:
        tabs = self._create_tabs()
        events: list[tuple[MKVTabItem | None, MKVTabItem | None]] = []
        tabs.bind(on_tab_switch=lambda inst, item, prev: events.append((item, prev)))

        first = tabs.add_tab("One", content=self._make_dummy_content("one"))
        second = tabs.add_tab("Two", content=self._make_dummy_content("two"))
        third = tabs.add_tab("Three", content=self._make_dummy_content("three"))
        pump_frames()

        second.dispatch("on_release")
        pump_frames()
        self.assertEqual(tabs.current_index, 1)
        self.assertEqual(events[-1], (second, first))

        tabs.switch_to(2, animate=False)
        pump_frames()
        self.assertEqual(tabs.current_tab, third)
        self.assertEqual(events[-1], (third, second))

    def test_switch_via_swipe(self) -> None:
        tabs = self._create_tabs()
        tabs.add_tab("One", content=self._make_dummy_content("one"))
        second = tabs.add_tab("Two", content=self._make_dummy_content("two"))
        pump_frames()

        tabs._carousel.index = 1
        pump_frames()

        self.assertEqual(tabs.current_index, 1)
        self.assertEqual(tabs.current_tab, second)

    def test_lazy_content_factory(self) -> None:
        tabs = self._create_tabs(lazy_content=True)
        created: list[str] = []

        def factory(name: str):
            def _inner() -> Widget:
                created.append(name)
                return self._make_dummy_content(name)

            return _inner

        tabs.add_tab("One", content=self._make_dummy_content("one"))
        tabs.add_tab("Two", content_factory=factory("two"))
        pump_frames()
        self.assertEqual(created, [])

        tabs.switch_to(1, animate=False)
        pump_frames()
        self.assertEqual(created, ["two"])

    def test_scrollable_mode_with_many_tabs(self) -> None:
        tabs = self._create_tabs(tab_mode="scrollable")
        for idx in range(8):
            tabs.add_tab(f"Tab {idx}", content=self._make_dummy_content(str(idx)))
        pump_frames()

        self.assertTrue(tabs._tab_bar._scroll_view.do_scroll_x)

    def test_max_width_applied_for_long_titles(self) -> None:
        tabs = self._create_tabs(max_item_width=dp(120))
        tabs.equal_item_widths = False
        tabs.add_tab("Short", content=self._make_dummy_content("short"))
        long_item = tabs.add_tab(
            "An extremely long tab title exceeding the width",
            content=self._make_dummy_content("long"),
        )
        pump_frames()

        self.assertLessEqual(long_item.width, dp(120) + 1)
        self.assertGreater(long_item.width, tabs.tabs[0].width)
