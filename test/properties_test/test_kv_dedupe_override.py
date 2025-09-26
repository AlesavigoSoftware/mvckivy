from __future__ import annotations

import logging
import unittest
from textwrap import dedent
from mvckivy.app import MKVApp
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty
from kivy.metrics import dp

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty


class Parent(AliasDedupeMixin, BoxLayout):
    """Базовый класс с динамикой padding ← ui_scale."""

    ui_scale = NumericProperty(1.0)

    def _get_alias_padding(self, ext: ExtendedAliasProperty):
        v = dp(8) * self.ui_scale
        return v, v, v, v

    alias_padding = ExtendedAliasProperty(
        _get_alias_padding,
        None,
        bind=("ui_scale",),
        cache=False,
        watch_before_use=True,
    )


class Child(Parent):
    """Подкласс, в KV у которого padding: GP10 (константа)."""


KV_SRC = """
#:import dp kivy.metrics.dp
#:set GP10 (dp(10), dp(10), dp(10), dp(10))

<Parent>:
    # Раннее правило (динамика от ui_scale)
    padding: self.alias_padding

<Child>:
    # Позднее правило (константа)
    -padding: GP10
    ui_scale: 3.0

Root:
    child: child
    parent_ref: parent
    Child:
        id: child
    Parent:
        id: parent
        ui_scale: 3.0
"""


class Root(BoxLayout):
    child = ObjectProperty()
    parent_ref = ObjectProperty()


class TestApp(MKVApp):
    def build(self):
        # По требованию: возвращаем результат Builder.load_string
        return Builder.load_string(KV_SRC)


class TestWithDedupe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = TestApp()
        cls.app._run_prepare()
        for _ in range(6):
            Clock.tick()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.stop()
        except Exception:
            pass

    def test_child_override_constant_wins(self):
        root: Root = self.app.root
        child: Parent = root.child
        parent: Parent = root.parent_ref

        self.assertEqual(
            [dp(10)] * 4,
            list(child.padding),
            "Child должен держать константу GP10 (10.0)",
        )
        self.assertEqual(
            [dp(8) * parent.ui_scale] * 4,
            list(parent.padding),
            "Parent — динамика от ui_scale",
        )

    def test_ui_scale_changes_affect_parent_not_child(self):
        root: Root = self.app.root
        child: Parent = root.child
        parent: Parent = root.parent_ref

        child.ui_scale = 5.0
        parent.ui_scale = 5.0
        for _ in range(4):
            Clock.tick()

        # Child остаётся на GP10
        self.assertEqual(
            [dp(10)] * 4,
            list(child.padding),
            "Ожидается, что после дедупа KV константа у Child не меняется.",
        )

        # Parent пересчитался
        self.assertEqual([dp(8) * 5.0] * 4, list(parent.padding))

    def test_parent_dynamic_alias_reacts(self):
        root: Root = self.app.root
        parent: Parent = root.parent_ref

        parent.ui_scale = 2.25
        for _ in range(3):
            Clock.tick()

        self.assertEqual([dp(8) * 2.25] * 4, list(parent.padding))


if __name__ == "__main__":
    unittest.main(verbosity=2)
